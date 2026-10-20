#!/usr/bin/env python3
"""Portable, checkpoint-driven schedules. No daemon, shell execution or lease renewal.

The deterministic time helpers need only Python. Scheduler mutations additionally
need coordination.Store and a live Main. Trigger deliveries propose/admit Jobs;
this module never starts an agent or interprets event contents as instructions.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import time
from contextlib import contextmanager
try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:
    ZoneInfo = None
    ZoneInfoNotFoundError = Exception

UTC = dt.timezone.utc
STAMP = re.compile(r"\d{4}(?:\.\d{2}){5}\.\d{3}Z")
MAX_SCAN_DAYS = 370
MAX_CANDIDATES = 64
TERMINAL = {"succeeded", "failed", "cancelled", "expired"}
DEFAULT_POLICIES = {"missed": "coalesce-one", "max_age_seconds": 86400,
                    "catch_up_limit": 1, "overlap": "queue-one", "queue_limit": 1,
                    "max_retries": 2, "retry_base_seconds": 30,
                    "retry_cap_seconds": 300, "clock_jump_seconds": 21600}
PROCESS_TOKEN = secrets.token_hex(16)


class ScheduleError(Exception):
    def __init__(self, code, detail=""):
        self.code, self.detail = code, detail
        super().__init__(code + (": " + str(detail) if detail else ""))


def need(condition, code, detail=""):
    if not condition:
        raise ScheduleError(code, detail)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def instant(value):
    """Parse an aware ISO-8601 instant or an Axis metadata timestamp, never local time."""
    if isinstance(value, dt.datetime):
        parsed = value
    else:
        need(isinstance(value, str) and len(value) <= 40, "invalid-instant")
        try:
            parsed = (dt.datetime.strptime(value, "%Y.%m.%d.%H.%M.%S.%fZ").replace(tzinfo=UTC)
                      if STAMP.fullmatch(value) else dt.datetime.fromisoformat(value.replace("Z", "+00:00")))
        except ValueError:
            raise ScheduleError("invalid-instant", value) from None
    need(parsed.tzinfo is not None and parsed.utcoffset() is not None, "timezone-required")
    return parsed.astimezone(UTC)


def stamp(value):
    value = instant(value)
    return value.strftime("%Y.%m.%d.%H.%M.%S.") + f"{value.microsecond // 1000:03d}Z"


def iso(value):
    return instant(value).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def integer(value, minimum, maximum, label):
    need(type(value) is int and minimum <= value <= maximum, "invalid-" + label)
    return value


def exact(value, required, optional=()):
    need(isinstance(value, dict), "invalid-object")
    need(set(required) <= value.keys() and value.keys() <= set(required) | set(optional), "unsupported-grammar")


def relative(value):
    need(isinstance(value, str) and value and len(value) <= 512 and not value.startswith("/")
         and "\\" not in value and all(p not in ("", ".", "..") for p in value.split("/"))
         and not any(ord(c) < 32 for c in value), "unsafe-path")
    need(not any(p.casefold() == "secrets" for p in value.split("/")), "protected-path")
    return value


def zone(name):
    need(isinstance(name, str) and len(name) <= 100 and not name.startswith("/")
         and ".." not in name.split("/"), "invalid-timezone")
    need(ZoneInfo is not None, "timezone-converter-unavailable")
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        raise ScheduleError("timezone-unavailable", name) from None


def validate_trigger(trigger):
    need(isinstance(trigger, dict), "invalid-trigger")
    trigger = copy.deepcopy(trigger)
    kind = trigger.get("type")
    if kind == "once":
        exact(trigger, {"type", "at"})
        trigger["at"] = iso(trigger["at"])
    elif kind == "calendar":
        exact(trigger, {"type", "frequency", "time", "timezone"}, {"weekdays", "start", "dst"})
        need(trigger["frequency"] in {"daily", "weekly"}, "unsupported-calendar-frequency")
        need(isinstance(trigger["time"], str) and re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?", trigger["time"]), "invalid-local-time")
        trigger["time"] = trigger["time"] + ":00" if len(trigger["time"]) == 5 else trigger["time"]
        zone(trigger["timezone"])
        if trigger["frequency"] == "weekly":
            days = trigger.get("weekdays")
            need(isinstance(days, list) and 1 <= len(days) <= 7, "invalid-weekdays")
            for day in days:
                integer(day, 0, 6, "weekday")
            need(len(set(days)) == len(days), "duplicate-weekday")
            trigger["weekdays"] = sorted(days)
        else:
            need("weekdays" not in trigger, "unsupported-grammar")
        if "start" in trigger:
            try:
                need(dt.date.fromisoformat(trigger["start"]).isoformat() == trigger["start"], "invalid-start-date")
            except (ValueError, TypeError):
                raise ScheduleError("invalid-start-date") from None
        dst = trigger.setdefault("dst", {"nonexistent": "skip", "repeated": "first"})
        exact(dst, {"nonexistent", "repeated"})
        need(dst["nonexistent"] in {"skip", "next-valid"}, "invalid-dst-policy")
        need(dst["repeated"] in {"first", "second", "both"}, "invalid-dst-policy")
    elif kind == "interval":
        exact(trigger, {"type", "mode", "seconds"}, {"anchor", "first_at", "completion"})
        integer(trigger["seconds"], 1, 31536000, "interval")
        need(trigger["mode"] in {"fixed-rate", "completion-relative"}, "invalid-interval-mode")
        if trigger["mode"] == "fixed-rate":
            need("anchor" in trigger and "first_at" not in trigger and "completion" not in trigger, "unsupported-grammar")
            trigger["anchor"] = iso(trigger["anchor"])
        else:
            need("first_at" in trigger and "anchor" not in trigger, "unsupported-grammar")
            need(trigger.get("completion", "succeeded") == "succeeded", "unsupported-completion-outcome")
            trigger["first_at"] = iso(trigger["first_at"])
            trigger["completion"] = "succeeded"
    elif kind == "event":
        exact(trigger, {"type", "source", "name"}, {"debounce_seconds"})
        for key in ("source", "name"):
            need(isinstance(trigger[key], str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", trigger[key]), "invalid-event-rule")
        trigger["debounce_seconds"] = integer(trigger.get("debounce_seconds", 0), 0, 86400, "debounce")
    else:
        raise ScheduleError("unsupported-trigger", kind)
    return trigger


def local_instants(naive, timezone, policy):
    """Round-trip each fold; nonexistent local times never silently acquire an offset."""
    def valid(value):
        found = set()
        for fold in (0, 1):
            utc = value.replace(tzinfo=timezone, fold=fold).astimezone(UTC)
            if utc.astimezone(timezone).replace(tzinfo=None) == value:
                found.add(utc)
        return sorted(found)
    found = valid(naive)
    notice = None
    if not found:
        notice = {"reason": "dst-nonexistent-" + policy["nonexistent"], "local": naive.isoformat()}
        if policy["nonexistent"] == "skip":
            return [], notice
        # At most one day of skipped local time (including historical date-line moves).
        probe = naive
        for _ in range(1441):
            probe += dt.timedelta(minutes=1)
            found = valid(probe)
            if found:
                while valid(probe - dt.timedelta(seconds=1)) and probe > naive:
                    probe -= dt.timedelta(seconds=1)
                found = valid(probe)
                break
        need(found, "unresolved-local-time")
    if len(found) == 2 and policy["repeated"] != "both":
        found = [found[0 if policy["repeated"] == "first" else 1]]
    return found, notice


def occurrences(trigger, after, until, *, completion=None, event=None, limit=MAX_CANDIDATES):
    """Return newest bounded planned occurrences in (after, until], plus skip facts.

    Calendar lookback is bounded; callers choose their missed-work age beforehand.
    Event identities must already be verified by a trusted adapter, not a JSON label.
    """
    trigger = validate_trigger(trigger)
    after, until = instant(after), instant(until)
    integer(limit, 1, MAX_CANDIDATES, "candidate-limit")
    need(until >= after, "clock-rollback")
    candidates, notices, omitted = [], [], 0
    kind = trigger["type"]
    if kind == "once":
        at = instant(trigger["at"])
        if after < at <= until:
            candidates.append({"planned": iso(at)})
    elif kind == "interval":
        if trigger["mode"] == "completion-relative":
            if completion is not None:
                need(isinstance(completion, dict) and completion.get("state") in TERMINAL, "invalid-completion")
                if completion["state"] != "succeeded":
                    return {"candidates": [], "notices": [{"reason": "completion-not-successful"}], "omitted": 0}
                at = instant(completion["completed_at"]) + dt.timedelta(seconds=trigger["seconds"])
            else:
                at = instant(trigger["first_at"])
            if after < at <= until:
                candidates.append({"planned": iso(at)})
        else:
            anchor, interval = instant(trigger["anchor"]), trigger["seconds"]
            first = max(0, math.floor((after - anchor).total_seconds() / interval) + 1)
            last = math.floor((until - anchor).total_seconds() / interval)
            count = max(0, last - first + 1)
            omitted = max(0, count - limit)
            for offset in range(max(first, last - limit + 1), last + 1):
                candidates.append({"planned": iso(anchor + dt.timedelta(seconds=offset * interval))})
    elif kind == "calendar":
        tz = zone(trigger["timezone"])
        day = after.astimezone(tz).date()
        last = until.astimezone(tz).date()
        need((last - day).days <= MAX_SCAN_DAYS, "calendar-window-too-large")
        start = dt.date.fromisoformat(trigger.get("start", day.isoformat()))
        day = max(day, start)
        local_time = dt.time.fromisoformat(trigger["time"])
        while day <= last:
            if trigger["frequency"] == "daily" or day.weekday() in trigger["weekdays"]:
                values, notice = local_instants(dt.datetime.combine(day, local_time), tz, trigger["dst"])
                if notice:
                    notices.append(notice)
                for at in values:
                    if after < at <= until:
                        candidates.append({"planned": iso(at), "local": at.astimezone(tz).isoformat(), "timezone": trigger["timezone"]})
            day += dt.timedelta(days=1)
        omitted = max(0, len(candidates) - limit)
        candidates = candidates[-limit:]
    elif kind == "event" and event is not None:
        exact(event, {"source", "name", "id", "at"})
        need(event["source"] == trigger["source"] and event["name"] == trigger["name"], "event-rule-mismatch")
        need(isinstance(event["id"], str) and 0 < len(event["id"].encode()) <= 256
             and not any(ord(c) < 32 for c in event["id"]), "invalid-event-id")
        at = instant(event["at"])
        if after < at <= until:
            candidates.append({"planned": iso(at), "event": {"source": event["source"], "id": event["id"]}})
    return {"candidates": candidates, "notices": notices, "omitted": omitted}


def next_occurrence(trigger, after, *, completion=None):
    trigger, after = validate_trigger(trigger), instant(after)
    if trigger["type"] == "event":
        return None
    if trigger["type"] == "once":
        at = instant(trigger["at"])
        return iso(at) if at > after else None
    if trigger["type"] == "interval":
        if trigger["mode"] == "completion-relative":
            if completion is not None and completion.get("state") != "succeeded":
                return None
            at = (instant(completion["completed_at"]) + dt.timedelta(seconds=trigger["seconds"])) if completion else instant(trigger["first_at"])
        else:
            anchor, seconds = instant(trigger["anchor"]), trigger["seconds"]
            at = anchor + dt.timedelta(seconds=max(0, math.floor((after - anchor).total_seconds() / seconds) + 1) * seconds)
        return iso(at) if at > after else None
    result = occurrences(trigger, after, after + dt.timedelta(days=8), limit=64)
    return result["candidates"][0]["planned"] if result["candidates"] else None


def occurrence_key(project, schedule, revision, occurrence):
    planned = occurrence.get("event", occurrence.get("planned"))
    need(planned is not None, "invalid-occurrence")
    return digest({"project": project, "schedule": schedule, "revision": revision, "occurrence": planned})


def retry_decision(*, classification, idempotent, retries, failed_at, now, deadline,
                   maximum=2, base_seconds=30, cap_seconds=300):
    """Offer a retry of the same Job/attempt, never revive a terminal Job."""
    integer(retries, 0, 1000, "retry-count")
    integer(maximum, 0, 2, "retry-limit")
    integer(base_seconds, 1, 3600, "retry-base")
    integer(cap_seconds, base_seconds, 3600, "retry-cap")
    now, deadline, failed_at = instant(now), instant(deadline), instant(failed_at)
    if classification not in {"transient-transport", "unavailable-capacity", "transient", "capacity", "transport"}:
        return {"decision": "hold", "reason": "failure-not-retryable"}
    if idempotent is not True:
        return {"decision": "hold", "reason": "idempotence-unproven"}
    if retries >= maximum:
        return {"decision": "hold", "reason": "retry-limit"}
    retry_at = failed_at + dt.timedelta(seconds=min(cap_seconds, base_seconds * 2 ** retries))
    if max(now, retry_at) >= deadline:
        return {"decision": "hold", "reason": "retry-deadline"}
    return {"decision": "retry" if now >= retry_at else "wait", "retry_at": iso(retry_at), "retry_number": retries + 1}


def validate_definition(value, now):
    exact(value, {"subject", "target", "trigger", "action", "authority", "scope", "validator"},
          {"description", "output", "notification", "policies", "limits"})
    value = copy.deepcopy(value)
    need(isinstance(value["subject"], str) and 0 < len(value["subject"]) <= 80 and "\n" not in value["subject"], "invalid-subject")
    exact(value["target"], {"kind", "ref"})
    need(value["target"]["kind"] in {"task", "workflow", "team", "supervision"}, "invalid-target")
    relative(value["target"]["ref"])
    exact(value["action"], {"operation"})
    allowed = {"prepare", "workflow", "status", "inspect"}
    need(value["action"]["operation"] in allowed, "unsupported-action")
    if value["target"]["kind"] == "supervision":
        need(value["action"]["operation"] in {"status", "inspect"}, "supervision-report-only")
    if "description" in value:
        need(isinstance(value["description"], str) and 0 < len(value["description"]) <= 4096, "invalid-description")
    value["trigger"] = validate_trigger(value["trigger"])
    exact(value["authority"], {"ref"}, {"expires", "digest"})
    relative(value["authority"]["ref"])
    value["authority"]["expires"] = stamp(value["authority"].get("expires", instant(now) + dt.timedelta(hours=24)))
    need(instant(value["authority"]["expires"]) > instant(now), "authority-expired")
    need(isinstance(value["scope"], list) and 1 <= len(value["scope"]) <= 32, "invalid-scope")
    for item in value["scope"]:
        relative(item)
    need(isinstance(value["validator"], str) and 0 < len(value["validator"]) <= 1024, "invalid-validator")
    if "output" in value:
        relative(value["output"])
        need(any(value["output"] == s or value["output"].startswith(s + "/") for s in value["scope"]), "output-outside-scope")
    value.setdefault("notification", {"destination": "project", "policy": "summary"})
    exact(value["notification"], {"destination", "policy"})
    need(value["notification"]["destination"] == "project", "external-notification-unavailable")
    need(value["notification"]["policy"] in {"summary", "failures", "none"}, "invalid-notification-policy")
    policies = dict(DEFAULT_POLICIES)
    need(isinstance(value.get("policies", {}), dict) and value.get("policies", {}).keys() <= policies.keys(), "invalid-policy")
    policies.update(value.get("policies", {}))
    need(policies["missed"] in {"skip", "coalesce-one", "catch-up-bounded"}, "invalid-missed-policy")
    need(policies["overlap"] in {"skip", "queue-one", "queue-bounded"}, "invalid-overlap-policy")
    integer(policies["max_age_seconds"], 1, 86400 * 366, "missed-age")
    integer(policies["catch_up_limit"], 1, MAX_CANDIDATES, "catch-up-limit")
    integer(policies["queue_limit"], 1, MAX_CANDIDATES, "queue-limit")
    integer(policies["max_retries"], 0, 2, "retry-limit")
    integer(policies["retry_base_seconds"], 1, 3600, "retry-base")
    integer(policies["retry_cap_seconds"], policies["retry_base_seconds"], 3600, "retry-cap")
    integer(policies["clock_jump_seconds"], 1, 86400 * 366, "clock-jump")
    if policies["overlap"] == "queue-one":
        policies["queue_limit"] = 1
    value["policies"] = policies
    limits = {"duration_seconds": 3600, "rounds": 3, "launches": 12, "concurrency": 3, "reserve_launches": 1,
              "usage_policy": "included allowance only; metering unavailable"}
    need(isinstance(value.get("limits", {}), dict) and value.get("limits", {}).keys() <= limits.keys(), "invalid-limits")
    limits.update(value.get("limits", {}))
    integer(limits["duration_seconds"], 1, 86400, "duration")
    integer(limits["rounds"], 1, 100, "rounds")
    integer(limits["launches"], 1, 1000, "launches")
    integer(limits["concurrency"], 1, limits["launches"], "concurrency")
    integer(limits["reserve_launches"], 1, limits["launches"], "reserve")
    need(limits["reserve_launches"] < limits["launches"], "invalid-reserve")
    need(isinstance(limits["usage_policy"], str) and limits["usage_policy"], "invalid-usage-policy")
    value["limits"] = limits
    return value


def machine_hint():
    """Read the existing optional local instance hint. It detects changes, not identity/authentication."""
    path = Path(os.path.expanduser("~/.axis/instance-id"))
    try:
        if path.is_symlink() or path.parent.is_symlink():
            return None
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            return None
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            raw = os.read(fd, 4097)
        finally:
            os.close(fd)
        if len(raw) > 4096:
            return None
        value = raw.decode().strip()
        if not STAMP.fullmatch(value):
            return None
        instant(value)
        return hashlib.sha256(raw).hexdigest()
    except (OSError, UnicodeError, ScheduleError):
        return None


def load_core():
    path = Path(__file__).with_name("coordination.py")
    need(path.is_file() and not path.is_symlink(), "core-unavailable")
    spec = importlib.util.spec_from_file_location("axis_scheduling_coordination", path)
    module = importlib.util.module_from_spec(spec)
    try:
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    except (ImportError, OSError) as error:
        raise ScheduleError("core-unavailable", type(error).__name__) from None
    return module


class Scheduler:
    """Schedule definitions and projections over the shared Coordination Store.

    `event_verifier` is trusted integration code returning a normalized event or
    refusing it. No caller-supplied `verified` boolean is accepted as evidence.
    """
    def __init__(self, root=None, *, core=None, session=None, event_verifier=None):
        self.core = core if core is not None else load_core().Store(root or ".", session=session)
        self.root = Path(self.core.root)
        self.event_verifier = event_verifier
        self._held = None

    def _now(self):
        return instant(self.core.now())

    def _check(self):
        self.core.require_main()
        if self._held:
            path, owner, start, identity = self._held
            need(time.monotonic() - start < 10, "schedule-lock-expired")
            need(path.is_dir() and not path.is_symlink() and (path.stat().st_dev, path.stat().st_ino) == identity
                 and self._read_json(path / "OWNER") == owner, "schedule-lock-lost")

    def _read_json(self, path):
        rel = str(path.relative_to(self.root))
        safe = self.core.path(rel)
        info = safe.lstat()
        need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "unsafe-path")
        fd = os.open(safe, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            data = os.read(fd, 65537)
            need(len(data) <= 65536, "record-too-large")
            def unique(pairs):
                out = {}
                for key, value in pairs:
                    need(key not in out, "duplicate-json-key")
                    out[key] = value
                return out
            return json.loads(data, object_pairs_hook=unique, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        except (ValueError, UnicodeError):
            raise ScheduleError("corrupt-scheduler-state") from None
        finally:
            os.close(fd)

    @contextmanager
    def _locked(self):
        self._check()
        path = self.core.path("_Axis/Flags/scheduler.lock", missing=True, kind="directory")
        owner = {"session": self.core.session, "nonce": secrets.token_hex(16)}
        try:
            path.mkdir()
        except FileExistsError:
            raise ScheduleError("scheduler-busy") from None
        owner_path = path / "OWNER"
        with owner_path.open("x") as stream:
            stream.write(canonical(owner))
            stream.flush()
            os.fsync(stream.fileno())
        self._held = (path, owner, time.monotonic(), (path.stat().st_dev, path.stat().st_ino))
        try:
            self._check()
            yield
        finally:
            held = self._held
            self._held = None
            if held and time.monotonic() - held[2] < 10 and path.is_dir() and not path.is_symlink() and (path.stat().st_dev, path.stat().st_ino) == held[3] and self._read_json(owner_path) == owner:
                owner_path.unlink()
                path.rmdir()

    def _context(self):
        try:
            context = self.core.main_context()
        except Exception as error:
            code = getattr(error, "code", "")
            if isinstance(code, str) and code.startswith("placement-"):
                raise ScheduleError(code) from None
            raise
        need(context.get("session") == self.core.session and context.get("control_epoch") == self.core.session
             and context.get("storage") in {"atomic", "serialized"}, "invalid-main-context")
        return context

    def _machine(self):
        hint = machine_hint()
        return {"kind": "instance", "value": hint} if hint else {"kind": "process", "value": PROCESS_TOKEN}

    def _binding(self):
        try:
            value = self._read_json(self.root / "_Axis/Flags/scheduler-binding.json")
        except (FileNotFoundError, OSError) as error:
            raise ScheduleError("placement-inactive", type(error).__name__) from None
        except Exception as error:
            if getattr(error, "code", "") in {"missing_path", "missing-path"}:
                raise ScheduleError("placement-inactive") from None
            raise
        exact(value, {"schema", "project", "root", "session", "control_epoch", "storage", "machine_hint", "executor", "activation"})
        need(value["schema"] == "axis.scheduler-placement/v1" and value["project"] == self.core.project_id()
             and value["root"] == str(self.root.resolve()) and value["session"] == self.core.session,
             "placement-mismatch")
        need(isinstance(value["activation"], str) and re.fullmatch(r"[0-9a-f]{32}", value["activation"]), "corrupt-placement")
        exact(value["machine_hint"], {"kind", "value"})
        need(value["machine_hint"]["kind"] in {"instance", "process"} and isinstance(value["machine_hint"]["value"], str), "corrupt-placement")
        current_machine = self._machine()
        if value["machine_hint"] != current_machine:
            if value["machine_hint"].get("kind") == "process" or current_machine["kind"] == "process":
                raise ScheduleError("stable-executor-binding-unavailable", "No stable local executor binding is available; explicitly bind and evaluate in one Main process, or use the manual workflow.")
            raise ScheduleError("placement-machine-changed")
        context = self._context()
        need(value["control_epoch"] == context["control_epoch"] and value["storage"] == context["storage"], "placement-context-changed")
        return value

    def bind(self, executor, *, epoch=None):
        """Explicit Main placement activation; never called by a timer or startup hook."""
        need(isinstance(executor, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", executor), "invalid-executor")
        with self._locked():
            self._check()
            context = self._context()
            need(epoch is None or epoch == context["control_epoch"], "control-epoch-mismatch")
            value = {"schema": "axis.scheduler-placement/v1", "project": self.core.project_id(),
                     "root": str(self.root.resolve()), "session": self.core.session,
                     "control_epoch": context["control_epoch"], "storage": context["storage"], "machine_hint": self._machine(),
                     "executor": executor, "activation": secrets.token_hex(16)}
            path = self.core.path("_Axis/Flags/scheduler-binding.json", missing=True)
            previous = path.read_bytes() if path.exists() else None
            temporary = path.with_name(path.name + "." + secrets.token_hex(8) + ".tmp")
            try:
                with temporary.open("x") as stream:
                    stream.write(canonical(value) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                self._check()
                need((path.read_bytes() if path.exists() else None) == previous, "placement-changed")
                self.core.path("_Axis/Flags/scheduler-binding.json", missing=True)
                if previous is None:
                    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
                    try:
                        raw = (canonical(value) + "\n").encode()
                        offset = 0
                        while offset < len(raw):
                            written = os.write(fd, raw[offset:])
                            need(written > 0, "placement-write-failed")
                            offset += written
                        os.fsync(fd)
                    finally:
                        os.close(fd)
                else:
                    os.replace(temporary, path)
                need(self._read_json(path) == value, "placement-readback")
            finally:
                if temporary.exists():
                    temporary.unlink()
            return value

    def _accepted(self, record):
        module = sys.modules.get(type(self.core).__module__)
        validate = getattr(module, "validate_acceptance", None)
        need(callable(validate), "core-acceptance-unavailable")
        validate(record)

    def _candidate(self, candidate, record):
        exact(candidate, {"planned"}, {"local", "timezone", "event", "proof"})
        planned = instant(candidate["planned"])
        trigger = record["definition"]["trigger"]
        if trigger["type"] == "event":
            need(isinstance(candidate.get("proof"), str) and STAMP.fullmatch(candidate["proof"]), "event-proof-missing")
            proof = self.core.read("Messages", candidate["proof"])
            self._accepted(proof)
            data = proof.get("data", {})
            need(data.get("type") == "schedule-event" and data.get("schedule") == record["id"], "event-proof-mismatch")
            expected = occurrences(trigger, planned - dt.timedelta(milliseconds=1), planned, event=data.get("event"))["candidates"]
        else:
            # Completion-relative times are bound by the retained successful predecessor Job below.
            if trigger.get("mode") == "completion-relative":
                return
            expected = occurrences(trigger, planned - dt.timedelta(milliseconds=1), planned)["candidates"]
        without_proof = {k: v for k, v in candidate.items() if k != "proof"}
        need(expected == [without_proof], "invalid-queued-occurrence")

    def _record(self, schedule_id):
        need(isinstance(schedule_id, str) and STAMP.fullmatch(schedule_id), "invalid-schedule-id")
        return self._validate_record(self.core.read("Schedules", schedule_id))

    def _validate_record(self, record):
        schedule_id = record["id"]
        self._accepted(record)
        need(record.get("schedule_schema") == "axis.schedule/v1", "unsupported-schedule-schema")
        need(record.get("status") in {"draft", "active", "paused", "retired"}, "corrupt-schedule-status")
        need(isinstance(record.get("definition"), dict) and isinstance(record.get("runtime"), dict), "corrupt-schedule")
        revision = record.get("revision")
        need(isinstance(revision, str) and STAMP.fullmatch(revision), "incomplete-revision")
        messages = self.core.records("Messages")
        need(len(messages) <= 10000, "message-index-too-large")
        revisions = [item for item in messages if item.get("data", {}).get("type") == "schedule-revision"
                     and item["data"].get("schedule") == schedule_id]
        need(0 < len(revisions) <= 1024, "revision-history-bound")
        successors = {}
        for item in revisions:
            self._accepted(item)
            payload = item["data"]
            need(item.get("kind") == "control" and payload.get("definition_digest") == digest(payload.get("definition")), "revision-mismatch")
            predecessor = payload.get("predecessor")
            need(predecessor is None or isinstance(predecessor, str) and STAMP.fullmatch(predecessor), "revision-predecessor")
            need(predecessor not in successors, "revision-fork")
            successors[predecessor] = item
        seen, cursor = set(), None
        while cursor in successors:
            cursor = successors[cursor]["id"]
            need(cursor not in seen, "revision-cycle")
            seen.add(cursor)
        need(len(seen) == len(revisions) and cursor == revision, "revision-head-mismatch")
        message = self.core.read("Messages", revision)
        self._accepted(message)
        need(message.get("kind") == "control", "revision-kind")
        data = message.get("data", {})
        need(data.get("type") == "schedule-revision" and data.get("schedule") == schedule_id
             and data.get("definition_digest") == digest(record["definition"])
             and data.get("lineage") == record.get("lineage")
             and data.get("definition") == record["definition"], "revision-mismatch")
        need(isinstance(record.get("lineage"), str) and re.fullmatch(r"[0-9a-f]{32}", record["lineage"]), "corrupt-lineage")
        runtime = record["runtime"]
        need(set(runtime) <= {"cursor", "queue", "last_observed", "revision_mapping", "zone_probe", "hold",
                            "monotonic", "clock_generation", "clock_reconciled", "last_event", "next_due", "notices"}, "corrupt-runtime")
        instant(runtime.get("cursor")); instant(runtime.get("last_observed"))
        need(isinstance(runtime.get("queue"), list) and len(runtime["queue"]) <= MAX_CANDIDATES, "corrupt-queue")
        for candidate in runtime["queue"]:
            self._candidate(candidate, record)
        if "monotonic" in runtime:
            need(type(runtime["monotonic"]) in {int, float} and math.isfinite(runtime["monotonic"]) and runtime["monotonic"] >= 0, "corrupt-clock")
        need(runtime.get("hold") in {None, "clock-uncertain", "timezone-data-changed"}, "corrupt-hold")
        return record

    def _replace(self, record, **changes):
        self._check()
        new = copy.deepcopy(record)
        new.update(changes)
        # Core digest is canonical over its record, not the local semantic digest.
        module = sys.modules.get(type(self.core).__module__)
        core_digest = getattr(module, "digest", digest)
        result = self.core.replace_record("Schedules", record["id"], new, core_digest(record))
        self.core.rebuild_indexes()
        return result

    def _revision(self, record, definition, *, replay=False):
        previous = record.get("revision")
        lineage = secrets.token_hex(16) if replay or not record.get("lineage") else record["lineage"]
        message = self.core.message("control", "main", "Immutable schedule definition revision.",
                                   correlation="schedule:" + record["id"],
                                   data={"type": "schedule-revision", "schedule": record["id"],
                                         "predecessor": previous, "lineage": lineage,
                                         "definition_digest": digest(definition), "definition": definition,
                                         "pending_policy": "retire-unadmitted", "replay_new_intent": replay})
        return message["id"], lineage

    def create(self, definition):
        with self._locked():
            now = self._now()
            definition = validate_definition(definition, now)
            definition["authority"] = self.core.validate_authority(definition["authority"], live=True)
            self.core.path(definition["target"]["ref"])
            cursor = now - dt.timedelta(milliseconds=1)
            if definition["trigger"]["type"] == "once":
                cursor = min(cursor, instant(definition["trigger"]["at"]) - dt.timedelta(milliseconds=1))
            created = self.core.create_record("Schedules", {"subject": definition["subject"],
                         "schedule_schema": "axis.schedule/v1", "status": "draft", "definition": definition,
                         "revision": None, "lineage": None, "activation": None,
                         "runtime": {"cursor": stamp(cursor), "queue": [], "last_observed": stamp(now)}})
            record = created["record"]
            revision, lineage = self._revision(record, definition)
            self._replace(record, revision=revision, lineage=lineage)
            return self.show(record["id"])

    def show(self, schedule_id):
        record = self._record(schedule_id)
        return {"id": record["id"], "status": record["status"], "revision": record["revision"],
                "definition": record["definition"], "runtime": record["runtime"],
                "trigger_availability": "checkpoint-driven", "activation": record.get("activation")}

    def list(self):
        result = []
        for record in self.core.records("Schedules"):
            result.append(self.show(record["id"]))
        return result

    def preview(self, definition):
        definition = validate_definition(definition, self._now())
        next_at = next_occurrence(definition["trigger"], self._now() - dt.timedelta(milliseconds=1))
        return {"definition": definition, "next_utc": next_at,
                "next_local": instant(next_at).astimezone(zone(definition["trigger"]["timezone"])).isoformat()
                if next_at and definition["trigger"]["type"] == "calendar" else next_at,
                "trigger_availability": "checkpoint-driven", "usage_enforcement": "launch/round/concurrency/deadline; usage estimate only"}

    def revise(self, schedule_id, definition, *, replay=False):
        with self._locked():
            record = self._record(schedule_id)
            need(record["status"] != "retired", "schedule-retired")
            definition = copy.deepcopy(definition)
            if (isinstance(definition, dict) and isinstance(definition.get("authority"), dict)
                    and definition["authority"].get("ref") == record["definition"]["authority"]["ref"]):
                definition["authority"].setdefault("expires", record["definition"]["authority"]["expires"])
                definition["authority"].setdefault("digest", record["definition"]["authority"].get("digest"))
            definition = validate_definition(definition, self._now())
            definition["authority"] = self.core.validate_authority(definition["authority"], live=True)
            revision, lineage = self._revision(record, definition, replay=replay)
            runtime = copy.deepcopy(record["runtime"])
            old_queue = runtime.get("queue", [])
            metadata = {"subject", "description", "notification"}
            semantic_change = ({k: v for k, v in definition.items() if k not in metadata}
                               != {k: v for k, v in record["definition"].items() if k not in metadata})
            runtime["queue"] = [] if semantic_change or replay else old_queue
            runtime["revision_mapping"] = {"from": record["revision"], "to": revision,
                                           "retired_unadmitted": old_queue if semantic_change or replay else [],
                                           "mapped_unadmitted": old_queue if not semantic_change and not replay else [],
                                           "lineage_preserved": not replay}
            if replay or semantic_change:
                runtime["cursor"] = stamp(self._now() - dt.timedelta(milliseconds=1))
            runtime.pop("zone_probe", None)
            self._replace(record, subject=definition["subject"], definition=definition, revision=revision,
                          lineage=lineage, runtime=runtime, status="paused" if record["status"] == "active" else record["status"], activation=None)
            return self.show(schedule_id)

    def _status(self, schedule_id, status):
        with self._locked():
            record = self._record(schedule_id)
            need(record["status"] != "retired", "schedule-retired")
            changes = {"status": status}
            if status == "active":
                binding = self._binding()
                self.core.validate_authority(record["definition"]["authority"], live=True)
                validate_definition(record["definition"], self._now())
                self.core.path(record["definition"]["target"]["ref"])
                changes["activation"] = {"activation": binding["activation"], "executor": binding["executor"]}
            if status == "retired":
                runtime = copy.deepcopy(record["runtime"])
                runtime["queue"] = []
                changes["runtime"] = runtime
            self._replace(record, **changes)
            return self.show(schedule_id)

    def pause(self, schedule_id):
        return self._status(schedule_id, "paused")

    def resume(self, schedule_id):
        return self._status(schedule_id, "active")

    def retire(self, schedule_id):
        return self._status(schedule_id, "retired")

    def reconcile_clock(self, schedule_id):
        with self._locked():
            record = self._record(schedule_id)
            runtime = copy.deepcopy(record["runtime"])
            runtime["cursor"] = stamp(min(instant(runtime["cursor"]), self._now()))
            runtime.update(last_observed=stamp(self._now()), clock_generation=PROCESS_TOKEN,
                           monotonic=time.monotonic(), clock_reconciled=True)
            runtime.pop("hold", None)
            runtime.pop("zone_probe", None)
            self._replace(record, runtime=runtime)
            return self.show(schedule_id)

    def _jobs(self, schedule_id):
        jobs = []
        records = self.core.records("Jobs")
        need(len(records) <= 10000, "job-index-too-large")
        for job in records:
            if job.get("schedule") == schedule_id:
                projection = self.core.project("Jobs", job["id"])
                need(not projection.get("held"), "job-state-held", job["id"])
                jobs.append((job, projection))
        return jobs

    def due(self, schedule_id=None, *, event=None, clock_uncertain=False):
        """Admit eligible Jobs only; return receipts, skipped/queued facts and retry offers."""
        if schedule_id is None:
            ids = [item["id"] for item in self.core.records("Schedules")]
            need(len(ids) <= 1000, "schedule-index-too-large")
            return [self.due(item, event=event, clock_uncertain=clock_uncertain) for item in ids]
        with self._locked():
            record = self._record(schedule_id)
            result = {"schedule": schedule_id, "revision": record["revision"], "admitted": [],
                      "duplicates": [], "notices": [], "queued": [], "retry_offers": []}
            if record["status"] != "active":
                result["status"] = record["status"]
                return result
            binding = self._binding()
            need(record.get("activation") == {"activation": binding["activation"], "executor": binding["executor"]}, "activation-changed")
            now, definition = self._now(), record["definition"]
            definition["authority"] = self.core.validate_authority(definition["authority"], live=True)
            definition = validate_definition(definition, now)
            policy = definition["policies"]
            runtime = copy.deepcopy(record["runtime"])
            last = instant(runtime["last_observed"])
            wall = (now - last).total_seconds()
            uncertain = clock_uncertain or wall < 0 or wall > policy["clock_jump_seconds"]
            if runtime.get("clock_generation") == PROCESS_TOKEN:
                elapsed = time.monotonic() - runtime.get("monotonic", time.monotonic())
                uncertain = uncertain or abs(wall - elapsed) > 5
            if uncertain or runtime.get("hold"):
                runtime["hold"] = runtime.get("hold", "clock-uncertain")
                self._replace(record, runtime=runtime)
                result.update(status="held", reason=runtime["hold"])
                return result
            probe = runtime.get("zone_probe")
            if probe and definition["trigger"]["type"] == "calendar":
                actual = next_occurrence(definition["trigger"], probe["after"])
                if actual != probe["next"]:
                    runtime["hold"] = "timezone-data-changed"
                    self._replace(record, runtime=runtime)
                    result.update(status="held", reason="timezone-data-changed")
                    return result
            jobs = self._jobs(schedule_id)
            active = [(job, state) for job, state in jobs if state["state"] not in TERMINAL or state.get("active") or state.get("stop_unconfirmed")]
            completion = None
            if definition["trigger"].get("mode") == "completion-relative" and jobs:
                terminal = [(job, state) for job, state in jobs if state["state"] in TERMINAL]
                if terminal and not active:
                    completion = max(terminal, key=lambda pair: instant(pair[1]["completed_at"]))[1]
                    if completion["state"] != "succeeded":
                        result.update(status="held", reason="completion-not-successful")
                        return result
            for job, state in active:
                if state["state"] not in {"admitted", "running"}:
                    continue
                pinned = self.core.read("Messages", job["definition_revision"])
                self._accepted(pinned)
                pinned_data = pinned.get("data", {})
                need(pinned_data.get("type") == "schedule-revision" and pinned_data.get("schedule") == schedule_id, "job-revision-mismatch")
                retry_policy = pinned_data["definition"]["policies"]
                for attempt_id, attempt in state.get("attempts", {}).items():
                    if attempt.get("status") == "failed" and not attempt.get("retry_authorized"):
                        decision = retry_decision(classification=attempt.get("classification", state.get("classification")),
                            idempotent=attempt.get("idempotent", state.get("idempotent")), retries=attempt.get("retry_count", state.get("retry_count", 0)),
                            failed_at=attempt["failed_at"], now=now,
                            deadline=job["limits"]["deadline"], maximum=min(retry_policy["max_retries"], job["limits"].get("retries", 2)),
                            base_seconds=retry_policy["retry_base_seconds"], cap_seconds=retry_policy["retry_cap_seconds"])
                        result["retry_offers"].append(dict(decision, job=job["id"], attempt=attempt_id))
            if active and definition["trigger"].get("mode") == "completion-relative":
                result["status"] = "active-job"
                return result
            after = max(instant(runtime["cursor"]), now - dt.timedelta(seconds=policy["max_age_seconds"]))
            if completion:
                # A completion can occur after an evaluation cursor; use its planned successor.
                planned = instant(completion["completed_at"]) + dt.timedelta(seconds=definition["trigger"]["seconds"])
                after = min(after, planned - dt.timedelta(milliseconds=1))
            verified = None
            if event is not None:
                need(definition["trigger"]["type"] == "event", "unexpected-event")
                need(callable(self.event_verifier), "event-verifier-unavailable")
                verified = self.event_verifier(copy.deepcopy(event), copy.deepcopy(definition["trigger"]))
                need(isinstance(verified, dict), "event-unverified")
                after = now - dt.timedelta(seconds=policy["max_age_seconds"])
            calculated = occurrences(definition["trigger"], after, now, completion=completion, event=verified)
            if verified and calculated["candidates"]:
                self._check()
                proof = self.core.message("control", "main", "Verified event identity retained for schedule evaluation.",
                    correlation="schedule:" + schedule_id,
                    data={"type": "schedule-event", "schedule": schedule_id, "event": verified})
                for candidate in calculated["candidates"]:
                    candidate["proof"] = proof["id"]
            candidates = runtime.get("queue", []) + calculated["candidates"]
            result["notices"].extend(calculated["notices"])
            if (definition["trigger"]["type"] == "once" and not jobs
                    and instant(definition["trigger"]["at"]) < now - dt.timedelta(seconds=policy["max_age_seconds"])):
                result["notices"].append({"reason": "occurrence-expired", "planned": definition["trigger"]["at"]})
            if calculated["omitted"]:
                result["notices"].append({"reason": "bounded-candidate-window", "count": calculated["omitted"]})
            unique = {}
            for candidate in candidates:
                if instant(candidate["planned"]) < now - dt.timedelta(seconds=policy["max_age_seconds"]):
                    result["notices"].append({"reason": "occurrence-expired", "planned": candidate["planned"]})
                    continue
                key = occurrence_key(self.core.project_id(), schedule_id, record["lineage"], candidate)
                unique[key] = candidate
            candidates = sorted(unique.values(), key=lambda item: (instant(item["planned"]), canonical(item)))
            if policy["missed"] == "skip":
                skipped = [c for c in candidates if instant(c["planned"]) < now - dt.timedelta(seconds=1)]
                candidates = [c for c in candidates if c not in skipped]
                if skipped:
                    result["notices"].append({"reason": "missed-skip", "count": len(skipped)})
            elif policy["missed"] == "coalesce-one" and len(candidates) > 1:
                result["notices"].append({"reason": "missed-coalesced", "count": len(candidates) - 1})
                candidates = candidates[-1:]
            elif len(candidates) > policy["catch_up_limit"]:
                result["notices"].append({"reason": "catch-up-bounded", "count": len(candidates) - policy["catch_up_limit"]})
                candidates = candidates[-policy["catch_up_limit"]:]
            runtime["queue"] = []
            known = {job.get("operation_key"): job for job, _ in jobs}
            for candidate in candidates:
                self._check()
                operation = occurrence_key(self.core.project_id(), schedule_id, record["lineage"], candidate)
                prior_once = [job for job, _ in jobs if job.get("occurrence", {}).get("lineage") == record["lineage"]]
                if definition["trigger"]["type"] == "once" and prior_once:
                    result["duplicates"].append(prior_once[0]["id"])
                    result["notices"].append({"reason": "once-already-admitted", "planned": candidate["planned"]})
                    continue
                if operation in known:
                    result["duplicates"].append(known[operation]["id"])
                    continue
                if active:
                    if policy["overlap"] == "skip":
                        result["notices"].append({"reason": "overlap-skip", "planned": candidate["planned"]})
                    else:
                        runtime["queue"].append(candidate)
                        runtime["queue"] = runtime["queue"][-policy["queue_limit"]:]
                        result["notices"].append({"reason": "overlap-queued", "planned": candidate["planned"]})
                    continue
                if definition["trigger"]["type"] == "event" and runtime.get("last_event"):
                    age = (instant(candidate["planned"]) - instant(runtime["last_event"])).total_seconds()
                    if age < definition["trigger"]["debounce_seconds"]:
                        result["notices"].append({"reason": "event-debounced", "planned": candidate["planned"]})
                        continue
                limits = copy.deepcopy(definition["limits"])
                limits["deadline"] = stamp(min(now + dt.timedelta(seconds=limits.pop("duration_seconds")), instant(definition["authority"]["expires"])))
                limits["usage"] = limits.pop("usage_policy")
                limits["retries"] = policy["max_retries"]
                mandate = {"subject": definition["subject"], "objective": definition.get("description", definition["subject"]),
                           "authority": definition["authority"], "scope": definition["scope"],
                           "actions": [{"prepare": "report", "workflow": "coordinate", "status": "inspect", "inspect": "inspect"}[definition["action"]["operation"]]],
                           "schedule_action": definition["action"], "validator": definition["validator"],
                           "limits": limits, "schedule": schedule_id, "definition_revision": record["revision"],
                           "occurrence": dict(candidate, key=occurrence_key(self.core.project_id(), schedule_id, record["revision"], candidate),
                                              observed=iso(now), lineage=record["lineage"])}
                try:
                    admitted = self.core.admit_job(mandate, operation)
                except Exception as error:
                    if getattr(error, "code", "") == "overlap":
                        runtime["queue"] = (runtime["queue"] + [candidate])[-policy["queue_limit"]:]
                        result["notices"].append({"reason": "overlap-raced"})
                        continue
                    raise
                result["duplicates" if admitted["status"] == "duplicate" else "admitted"].append(admitted["id"])
                active.append((admitted["record"], {"state": "admitted"}))
                if definition["trigger"]["type"] == "event":
                    runtime["last_event"] = candidate["planned"]
            runtime.update(cursor=stamp(now), last_observed=stamp(now), clock_generation=PROCESS_TOKEN,
                           monotonic=time.monotonic(), notices=result["notices"][-64:])
            next_at = next_occurrence(definition["trigger"], now, completion=completion)
            runtime["next_due"] = next_at
            if definition["trigger"]["type"] == "calendar":
                runtime["zone_probe"] = {"after": iso(now), "next": next_at}
            self._replace(record, runtime=runtime)
            result.update(status="evaluated", queued=runtime["queue"], next_due=next_at)
            return result

    def recover_revision(self, schedule_id, revision):
        """Finish an explicitly selected, already accepted linear revision after interrupted view update."""
        with self._locked():
            record = self.core.read("Schedules", schedule_id)
            self._accepted(record)
            need(record.get("status") != "retired", "schedule-retired")
            message = self.core.read("Messages", revision)
            self._accepted(message)
            data = message.get("data", {})
            need(data.get("type") == "schedule-revision" and data.get("schedule") == schedule_id, "revision-mismatch")
            definition = copy.deepcopy(data.get("definition"))
            self.core.validate_authority(definition["authority"], live=False)
            proposed = copy.deepcopy(record)
            runtime = copy.deepcopy(record["runtime"])
            runtime["revision_mapping"] = {"from": record.get("revision"), "to": revision,
                "retired_unadmitted": runtime.get("queue", []), "mapped_unadmitted": [], "lineage_preserved": record.get("lineage") == data.get("lineage")}
            runtime["queue"] = []
            proposed.update(subject=definition["subject"], definition=definition, revision=revision,
                            lineage=data.get("lineage"), status="paused", activation=None, runtime=runtime)
            self._validate_record(proposed)  # Reject forks, gaps, altered sources and any non-tip choice.
            changes = {key: proposed[key] for key in ("subject", "definition", "revision", "lineage", "status", "activation", "runtime")}
            self._replace(record, **changes)
            return self.show(schedule_id)

    def manual_evaluate(self, schedule_id, executor, *, activate=False):
        """Explicit same-process placement/activation/evaluation, never a timer operation."""
        need(activate is True, "explicit-activation-required")
        self._record(schedule_id)
        self.bind(executor)
        self.resume(schedule_id)
        return self.due(schedule_id)

    def trigger(self, payload):
        """One-shot external clock adapter. Input is data; it cannot bind or renew Main."""
        exact(payload, {"action", "delivery_id"}, {"schedule", "event"})
        need(payload["action"] == "evaluate", "unsupported-trigger-action")
        need(isinstance(payload["delivery_id"], str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", payload["delivery_id"]), "invalid-delivery-id")
        self._check()
        need(self._context()["storage"] == "atomic", "serialized-trigger-unavailable", "Serialized storage requires Main-mediated manual due evaluation.")
        return {"delivery_id": payload["delivery_id"], "results": self.due(payload.get("schedule"), event=payload.get("event"))}


def read_input(path):
    if path == "-":
        data = sys.stdin.read(65537)
    else:
        with Path(path).open() as stream:
            data = stream.read(65537)
    need(len(data.encode()) <= 65536, "input-too-large")
    def unique(pairs):
        out = {}
        for key, value in pairs:
            need(key not in out, "duplicate-json-key")
            out[key] = value
        return out
    try:
        return json.loads(data, object_pairs_hook=unique, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except ValueError:
        raise ScheduleError("invalid-json") from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--session")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("create", "preview", "trigger"):
        item = sub.add_parser(name)
        item.add_argument("--json", default="-")
    item = sub.add_parser("bind")
    item.add_argument("executor")
    item.add_argument("--epoch")
    sub.add_parser("list")
    for name in ("show", "pause", "resume", "retire", "reconcile-clock"):
        item = sub.add_parser(name)
        item.add_argument("schedule")
    item = sub.add_parser("revise")
    item.add_argument("schedule")
    item.add_argument("--json", default="-")
    item.add_argument("--replay-new-intent", action="store_true")
    item = sub.add_parser("due")
    item.add_argument("schedule", nargs="?")
    item.add_argument("--clock-uncertain", action="store_true")
    item = sub.add_parser("recover-revision")
    item.add_argument("schedule")
    item.add_argument("revision")
    item = sub.add_parser("manual-evaluate")
    item.add_argument("schedule")
    item.add_argument("--executor", required=True)
    item.add_argument("--activate", action="store_true")
    args = parser.parse_args(argv)
    try:
        scheduler = Scheduler(args.root, session=args.session)
        if args.command in {"create", "preview", "trigger"}:
            result = getattr(scheduler, args.command)(read_input(args.json))
        elif args.command == "bind":
            result = scheduler.bind(args.executor, epoch=args.epoch)
        elif args.command == "recover-revision":
            result = scheduler.recover_revision(args.schedule, args.revision)
        elif args.command == "manual-evaluate":
            result = scheduler.manual_evaluate(args.schedule, args.executor, activate=args.activate)
        elif args.command == "list":
            result = scheduler.list()
        elif args.command == "revise":
            result = scheduler.revise(args.schedule, read_input(args.json), replay=args.replay_new_intent)
        elif args.command == "due":
            result = scheduler.due(args.schedule, clock_uncertain=args.clock_uncertain)
        else:
            result = getattr(scheduler, args.command.replace("-", "_"))(args.schedule)
        print(canonical({"ok": True, "result": result}))
        return 0
    except Exception as error:
        print(canonical({"ok": False, "error": getattr(error, "code", type(error).__name__), "detail": str(error)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
