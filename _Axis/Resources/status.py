#!/usr/bin/env python3
"""Axis ^status, the daily brief and "what needs me?", built from the project's canonical records.

Optional accelerator for `_Axis/Commands/status.md` and `_Axis/Commands/brief.md`. It never writes a record. It
prints a terminal summary (default), JSON, or a static branded web page under `_Temp/status/`; with --view it gives
the brief, "what needs me?", the due state or Main's prune of the brief's day files under `_Temp/status/brief/`.
Without Python the Agent composes the same by hand from the same records.
"""
import argparse, datetime as dt, html, importlib.util, json, os, re, shutil, subprocess, sys
from pathlib import Path

sys.dont_write_bytecode = True
# BEGIN GENERATED: project-files
PROJECT_FILES=('PROJECT.md','PLAN.md','INITIATIVES.md','TASKS.md','INSTRUCTIONS.md','SETTINGS.md','MINDSET.md','DIRECTIVES.md')
def project_file(root,name):
    """Path of project file NAME: in _Config/ once moved, in _Axis/ before. Two differing copies are an error, never a choice."""
    import pathlib
    if name not in PROJECT_FILES:raise ValueError('not a project file: '+str(name))
    new=pathlib.Path(root)/'_Config'/name;old=pathlib.Path(root)/'_Axis'/name
    if new.is_file() and old.is_file() and new.read_bytes()!=old.read_bytes():raise ValueError('project file differs between _Config and _Axis: '+name)
    return new if new.is_file() or not old.is_file() else old
def project_name(root,name):
    """Project-relative name of project file NAME, by the same rule: `_Config/NAME` or `_Axis/NAME`."""
    import pathlib
    return project_file(root,name).relative_to(pathlib.Path(root)).as_posix()
# END GENERATED: project-files

TS = re.compile(r'^\d{4}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{3}Z\.md$')


def read(p):
    try:
        return Path(p).read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def coordination_summary(root):
    try:
        spec=importlib.util.spec_from_file_location('axis_coordination_view',Path(__file__).with_name('coordination-view.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module.summary(root)
    except (OSError,ValueError,ImportError):return {'verification':'unavailable'}


def records(root, *dirs):
    """Timestamp-named record files, newest first, across the given folders; a record file that is a link is never read."""
    out = []
    for d in dirs:
        p = root / d
        if p.is_dir() and not p.is_symlink():
            out += [f for f in p.iterdir() if TS.match(f.name) and f.is_file() and not f.is_symlink()]
    return sorted(out, key=lambda f: f.name, reverse=True)


def subject(f):
    for line in read(f).splitlines():
        s = line.strip().lstrip('#').strip()
        return re.sub(r'^(Follow-Up|Reminder|Request): ', '', s)
    return ''


def fields(text):
    return {m.group(1): m.group(2).strip() for m in re.finditer(r'^([a-z][a-z-]*): ?(.*)$', text, re.M)}


def is_open(text):
    """An open Follow-Up or Reminder: its first `outcome:` is `N/A` or absent, the rule Session Start counts by.
    A terminal record left in the live folder is history, not waiting (Practices > Followups, > Reminders)."""
    value = next((m.group(1).strip().strip('*').strip() for m in re.finditer(r'^[ \t]*outcome:[ \t]*(.*)$', text, re.M)), 'N/A')
    return value in ('N/A', '')


def first_field(text, key):
    """A structured field's first value, as `is_open` reads `outcome:`; '' when absent."""
    return next((m.group(1).strip() for m in re.finditer(r'^[ \t]*' + re.escape(key) + r':[ \t]*(.*)$', text, re.M)), '')


def followup_order(f):
    """Practices > Followups > Ordering: overdue, then other dated items, each earliest due first, then undated ones,
    oldest raised first. Earliest due first over all dated items puts every overdue one first; the ID is `raised:`."""
    dated = bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}', f['due']))
    return (0, f['due'], f['id']) if dated else (1, '', f['id'])


def due_text(value):
    """A Reminder's `due-at:` for reading, in UTC as the title is: 2026.11.23.06.00.00.000Z -> 2026-11-23 06:00 UTC."""
    t = when(value) if re.fullmatch(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z', value) else None
    return t.strftime('%Y-%m-%d %H:%M UTC') if t else value


def when(name):
    try:
        return dt.datetime.strptime(name[:23], '%Y.%m.%d.%H.%M.%S.%f').replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def age(t, now):
    if not t:
        return ''
    s = (now - t).total_seconds()
    if s < 3600:
        return f'{max(1, int(s // 60))}m ago'
    if s < 172800:
        return f'{int(s // 3600)}h ago'
    return f'{int(s // 86400)}d ago'


def blocks(text, level='## '):
    """Split a Markdown index into (heading, body) blocks at the given heading level."""
    out, head, body = [], None, []
    for line in text.splitlines():
        if line.startswith(level) and not line.startswith(level + '#'):
            if head is not None:
                out.append((head, '\n'.join(body)))
            head, body = line[len(level):].strip(), []
        elif head is not None:
            body.append(line)
    if head is not None:
        out.append((head, '\n'.join(body)))
    return out


def first_paragraph(text, after=None):
    seen = after is None
    for para in re.split(r'\n\s*\n', text):
        p = para.strip()
        if not seen:
            seen = p.startswith(after)
            continue
        if p and not p.startswith(('#', '>', '<!--', '|', '-', '*')) and '{{' not in p:
            p = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', p)
            return re.sub(r'\s+', ' ', p.replace('**', '').replace('`', ''))
    return ''


def collect(root, detail):
    now = dt.datetime.now(dt.timezone.utc)
    ax = root / '_Axis'
    # Until the first start after an update has moved a project file, it is still in _Axis/: the either-place rule.
    cfg = lambda name: project_file(root, name)
    project = read(cfg('PROJECT.md'))
    name = (re.findall(r'^# Project:\s*(.+)$', project, re.M) or ['Not set'])[0].strip()
    if '{{' in name:
        name = 'Not set'
    version = (re.findall(r'^current-version: (\S+)$', read(ax / 'CHANGELOG.md'), re.M) or ['Unavailable'])[0]
    plan = read(cfg('PLAN.md'))
    direction = first_paragraph(plan, after='## ') or 'No Plan written yet.'
    tasks = []
    for head, body in blocks(read(cfg('TASKS.md'))):
        f = fields(body)
        if '{{' in head + body or 'status' not in f:
            continue
        tasks.append({'name': head, 'label': f.get('label', ''), 'status': f.get('status', ''),
                      'updated': f.get('updated', ''), 'initiative': f.get('initiative', '')})
    count = {s: sum(t['status'] == s for t in tasks) for s in ('Active', 'Planned', 'Blocked', 'Completed', 'Cancelled')}
    inits = []
    for head, body in blocks(read(cfg('INITIATIVES.md'))):
        f = fields(body)
        if 'status' in f and '{{' not in head + body:
            nxt = ''
            for sh, sb in blocks(body, '### '):
                if sh.lower() in ('next decision', 'next'):
                    nxt = first_paragraph(sb) or next((l.strip('-* ').strip() for l in sb.splitlines() if l.strip()), '')
            inits.append({'key': head, 'name': f.get('name', head), 'status': f['status'], 'phase': f.get('phase', ''),
                          'next': '' if nxt.lower().rstrip('.') == 'none' else re.sub(r'^next decision:\s*', '', nxt, flags=re.I)})
    fus = []
    for f in records(root, '_Axis/Followups'):
        body = read(f)
        if is_open(body):
            fus.append({'subject': subject(f), 'due': first_field(body, 'due'), 'id': f.name[:-3]})
    fus.sort(key=followup_order)
    rem = []
    for f in records(root, '_Axis/Reminders'):
        body = read(f)
        if is_open(body):
            rem.append({'subject': subject(f), 'due': first_field(body, 'due-at'), 'id': f.name[:-3]})
    rem.sort(key=lambda r: (r['due'] or '~', r['subject']))
    logs = [{'subject': subject(f), 'age': age(when(f.name), now)} for f in records(root, '_Axis/Logs')[:12 if detail == 'full' else 4]]
    snaps = records(root, '_Axis/Snapshots')
    reviews = review_memos(root) or records(root, '_Axis/Reviews', '_Axis/Status')
    memos_waiting = waiting_memos(root)
    agents = []
    ad = ax / 'Agents'
    for f in (ad.iterdir() if ad.is_dir() else []):
        if f.suffix == '.md' and TS.match(f.name) and not f.with_suffix('.kill').exists():
            fresh = now.timestamp() - f.stat().st_mtime < 3600
            if fresh:
                agents.append(subject(f))
    git = ''
    if shutil.which('git') and (root / '.git').exists():
        try:
            br = subprocess.run(['git', '-C', str(root), 'branch', '--show-current'], capture_output=True, text=True, timeout=5).stdout.strip()
            dirty = subprocess.run(['git', '-C', str(root), 'status', '--porcelain'], capture_output=True, text=True, timeout=10).stdout.strip()
            git = f"{br or 'detached'}{', uncommitted changes' if dirty else ', clean'}"
        except (OSError, subprocess.SubprocessError):
            git = ''
    def n(d):
        p = root / d
        return len([f for f in p.iterdir() if TS.match(f.name)]) if p.is_dir() else 0
    active = [t for t in tasks if t['status'] == 'Active']
    model = (read(ax / 'Flags/model').splitlines() or [''])[0].strip()
    blocked = [t for t in tasks if t['status'] == 'Blocked']
    data = {
        'generated': now.strftime('%Y-%m-%d %H:%M'), 'project': name, 'version': version, 'folder': str(root),
        'model': model_name(model),
        'model_access': next((v for v in read(ax/'Flags/model-access').splitlines()[:1] if v in {'subscription','api-key'}),'unverified'),
        'context': context_method(read(cfg('SETTINGS.md'))),
        'decisions': [{'initiative': i['name'], 'next': i['next']} for i in inits if i['status'] in ('Active', 'Blocked') and i['next']],
        'direction': direction, 'tasks': count, 'active': active, 'blocked': blocked,
        'initiatives': [i for i in inits if i['status'] not in ('Completed', 'Cancelled')],
        'followups': fus, 'reminders': rem[:10], 'logs': logs,
        'snapshot': {'subject': subject(snaps[0]), 'age': age(when(snaps[0].name), now)} if snaps else None,
        'review': {'subject': subject(reviews[0]), 'age': age(memo_date(reviews[0].name) or when(reviews[0].name), now), 'path': str(reviews[0].relative_to(root))} if reviews else None,
        'memos_waiting': memos_waiting,
        'agents': agents, 'git': git, 'root': str(root),
        'counts': {'Notes': n('_Axis/Notes'), 'Ideas': n('_Axis/Ideas'), 'Submissions': n('_Axis/Submissions'), 'Logs': n('_Axis/Logs')},
        'coordination': coordination_summary(root),
        'detail': detail,
    }
    if detail == 'full':
        data['recent_completed'] = [t for t in tasks if t['status'] == 'Completed'][-8:]
        data['plan_sections'] = [h for h, _ in blocks(plan)]
    return data


MEMO = re.compile(r'^(\d{4}-\d\d-\d\d|\d{4}(?:\.\d{2}){5}\.\d{3}Z) - (.+)\.md$')


def memo_date(name):
    m = MEMO.match(name)
    if not m:return None
    try:
        value=m.group(1)
        return (dt.datetime.strptime(value,'%Y.%m.%d.%H.%M.%S.%fZ').replace(tzinfo=dt.timezone.utc)
                if value.endswith('Z') else dt.datetime.strptime(value,'%Y-%m-%d').astimezone())
    except ValueError:return None


def memo_order(path):
    date=memo_date(path.name)
    return (date.timestamp() if date else float('-inf'),path.name)


def review_memos(root):
    """Review memos (2.08), newest first: live ones in _Memos/, then _Memos/Archive/."""
    out = []
    for d in ('_Memos', '_Memos/Archive'):
        p = root / d
        if p.is_dir() and not p.is_symlink():
            out += sorted((f for f in p.iterdir() if f.is_file() and not f.is_symlink() and memo_date(f.name) is not None and ' - Review - ' in f.name), key=lambda f: f.name, reverse=True)
    return sorted(out, key=memo_order, reverse=True)


def waiting_memos(root):
    """Names of live memos whose header Status is `waiting on you`, newest first."""
    p = root / '_Memos'
    if not p.is_dir() or p.is_symlink():
        return []
    out = []
    for f in sorted(p.iterdir(), key=memo_order, reverse=True):
        if f.is_file() and not f.is_symlink() and memo_date(f.name) is not None and re.search(r'^- \*\*Status:\*\* waiting on you\s*$', read(f)[:2000], re.M):
            out.append(f.name[:-3])
    return out


def context_method(settings):
    """The Context Management Setting (2.04); missing or unrecognized means Default."""
    m = re.search(r'^### Context Management\n(?:(?!^### ).)*?^\*\*Value:\*\* (\S+)', settings, re.M | re.S)
    return m.group(1) if m and m.group(1) in ('Default', 'Two-Pass') else 'Default'


def model_name(m):
    """The session's model from the `model` Flag, in words: claude-opus-5-5[1m] -> Claude Opus 5.5."""
    m = re.sub(r'\[.*?\]$', '', m).strip()
    if not m or m == 'cleared':
        return 'Unknown'
    x = re.fullmatch(r'claude-([a-z]+)-(\d+)(?:-(\d{1,2}))?(?:-\d{8})?', m)
    if x:
        return f"Claude {x.group(1).title()} {x.group(2)}{'.' + x.group(3) if x.group(3) else ''}"
    return m


def clip(s, w):
    s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s)
    return s if len(s) <= w else s[:w - 1] + '…'


def heading_sgr():
    """Brand terminal rule (tokens.json > terminal): headings bold, brand blue chosen by background, bold only when unknown."""
    theme = os.environ.get('AXIS_THEME', '').lower()
    if theme == 'plain':
        return None
    if theme not in ('light', 'dark'):
        fgbg = os.environ.get('COLORFGBG', '').split(';')[-1]
        theme = 'dark' if fgbg in ('0', '1', '2', '3', '4', '5', '6', '8') else 'light' if fgbg in ('7', '15') else ''
    return {'light': '1;38;2;47;86;201', 'dark': '1;38;2;143;168;245'}.get(theme, '1')


def text(d, width, color):
    sgr = heading_sgr() if color else None
    A = (lambda s: f'\033[{sgr}m{s}\033[0m') if sgr else (lambda s: s)
    B = A
    M = lambda s: s
    # Layout: a STATUS title with the time (no zone) between Axis dividers (14 hyphens with single spaces), one
    # block of "Label:" rows indented four spaces, a divider, then labelled sections and a closing divider.
    # Git stays in the background, so it is not shown.
    rule = ' '.join('-' * 14)
    out = [rule, ' ' + B('STATUS') + '   ' + d['generated'], rule, '']
    t = d['tasks']
    home = os.path.expanduser('~'); path = d['root']
    path = '~' + path[len(home):] if path == home or path.startswith(home + '/') else path
    row = lambda k, v: f"    {(k + ':').ljust(13)}{v}"
    out += [row('Project', d['project']), row('Path', path), row('Model', d['model']), row('Access', d.get('model_access','unverified')), row('Context', d['context']), '',
            row('Tasks', f"{t['Active']} active / {t['Blocked']} blocked"), row('Follow-Up', len(d['followups'])),
            row('Reminders', len(d['reminders'])), row('Agents', len(d['agents'])), row('Version', d['version']), '', rule, '']
    full = d['detail'] == 'full'
    def section(title, lines, empty):
        out.extend([B('  ' + title + ':'), '', *(lines or ['    ' + empty]), ''])
    section('Summary', wrap(d['direction'], width - 4, 4 if full else 3), 'No Plan written yet.')
    cur = [f"    {A('>')} {clip(x['name'] + ' - ' + x['label'], width - 6)}" for x in d['active'][:8 if full else 4]]
    cur += [f"    {A('!')} {clip('Blocked: ' + x['name'] + ' - ' + x['label'], width - 6)}" for x in d['blocked'][:6 if full else 3]]
    section('Current', cur, 'No active or blocked Tasks.')
    section('Waiting on you', [f"    - {clip(f['subject'] + (' (due ' + f['due'] + ')' if f['due'] and f['due'] != 'N/A' else ''), width - 6)}"
                               for f in d['followups'][:5]] + [f"    - Memo: {clip(m, width - 12)}" for m in d['memos_waiting'][:5]], 'Nothing.')
    section('Reminders', [f"    - {clip(r['subject'] + (' - ' + due_text(r['due']) if r['due'] else ''), width - 6)}" for r in d['reminders'][:3]], 'None.')
    recent = [f"    {M(l['age'].rjust(7))}  {clip(l['subject'], width - 13)}" for l in d['logs']]
    tail = ([f"last Snapshot {d['snapshot']['age']}"] if d['snapshot'] else []) + ([f"last Review {d['review']['age']}"] if d['review'] else [])
    if tail:
        recent.append(M('    ' + '; '.join(tail)))
    section('Recent activity', recent, 'No Logs yet.')
    section('Next decisions', [f"    - {clip(x['initiative'] + ': ' + x['next'], width - 6)}" for x in d['decisions'][:6 if full else 3]], 'None recorded.')
    if full:
        if d['initiatives']:
            section('Initiatives', [f"    {clip(i['name'] + ' (' + i['status'] + (', ' + phase if phase else '') + ')', width - 6)}"
                                    for i in d['initiatives'][:8]
                                    for phase in [re.sub(r'^' + re.escape(i['status']) + r'\b[:,.]?\s*', '', i['phase'], flags=re.I)]], '')
        if d.get('recent_completed'):
            section('Recently completed', [f"    - {clip(x['name'], width - 6)}" for x in d['recent_completed']], '')
        c = d['counts']
        section('Records', [f"    {c['Logs']} Logs, {c['Notes']} Notes, {c['Ideas']} Ideas, {c['Submissions']} Submissions waiting"], '')
    out.append(rule)
    return '\n'.join(out)


def wrap(s, w, maxlines):
    words, lines, cur = s.split(), [], ''
    for word in words:
        if len(cur) + len(word) + 1 > w:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + ' ' + word).strip()
    if cur:
        lines.append(cur)
    if len(lines) > maxlines:
        lines = lines[:maxlines]
        lines[-1] = lines[-1][:w - 1] + '…'
    return ['    ' + l for l in lines]


FALLBACK_CSS = """body{margin:0;background:#FFFFFF;color:#0B1220;font:17px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
code{font-family:ui-monospace,Menlo,Consolas,monospace}"""
PAGE_CSS = """.wrap{max-width:1080px;margin:0 auto;padding:32px 24px 48px}
body{background:var(--axis-bg,#FFFFFF);color:var(--axis-fg,#0B1220)}
header.band{background:var(--axis-ink,#0B1220);color:var(--axis-navy-text,#DCE4F5);padding:28px 0}
header .wrap{padding-top:0;padding-bottom:0;display:flex;align-items:center;gap:20px;flex-wrap:wrap}
header img{height:40px}
header h1{margin:0;font-size:28px;color:#FFFFFF;letter-spacing:-0.02em}
header .meta{margin-left:auto;font-family:var(--axis-font-mono,monospace);font-size:13px;color:var(--axis-navy-muted,#B7C1D3)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:24px 0}
.stat{background:var(--axis-band,#EEF2F9);border-radius:var(--axis-radius,14px);padding:14px 18px}
.stat strong{display:block;font-size:30px;color:var(--axis-link,#2F56C9);line-height:1.2}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
.card{background:var(--axis-raised,#FFFFFF);border:1px solid var(--axis-border,#D5DCE8);border-radius:var(--axis-radius,14px);padding:18px 20px}
.card h2{font-size:15px;margin:0 0 8px;font-family:var(--axis-font-mono,monospace);text-transform:uppercase;letter-spacing:.08em;color:var(--axis-fg-muted,#5B6472)}
.card ul{margin:0;padding-left:18px}.card li{margin:4px 0}
.muted{color:var(--axis-fg-muted,#5B6472)}
.lede{font-size:19px;margin:0 0 8px}
footer{margin-top:40px;font-size:14px;color:var(--axis-fg-muted,#5B6472);border-top:1px solid var(--axis-border,#D5DCE8);padding-top:14px}"""


def page(d, root, out):
    e = html.escape
    brand = next((b for b in (root / '_Axis' / 'Branding', root / 'Branding') if (b / 'css' / 'axis-brand.css').is_file()), root / '_Axis' / 'Branding')
    rel = os.path.relpath(brand, out.parent).replace(os.sep, '/')
    has = (brand / 'css' / 'axis-brand.css').is_file()
    head = (f'<link rel="stylesheet" href="{rel}/css/axis-brand.css"><link rel="icon" href="{rel}/favicon/favicon.svg" type="image/svg+xml">'
            if has else f'<style>{FALLBACK_CSS}</style>')
    logo = f'<img src="{rel}/svg/logo/logo-reversed.svg" alt="Axis Workflow" height="40">' if has else '<strong>Axis Workflow</strong>'
    def li(items):
        return ''.join(f'<li>{e(x)}</li>' for x in items) or '<li class="muted">None</li>'
    t = d['tasks']
    stats = [(t['Active'], 'active tasks'), (t['Planned'], 'planned'), (t['Blocked'], 'blocked'), (t['Completed'], 'completed'),
             (len(d['followups']) + len(d['memos_waiting']), 'waiting on you'), (len(d['reminders']), 'reminders'), (len(d['agents']), 'agents live')]
    cards = [
        ('Now', li([f"{x['name']} - {clip(x['label'], 140)}" for x in d['active']] + [f"Blocked: {x['name']} - {clip(x['label'], 120)}" for x in d['blocked']])),
        ('Initiatives', li([f"{i['name']} ({i['status']}{', ' + i['phase'] if i['phase'] and i['phase'] != i['status'] else ''})" for i in d['initiatives']])),
        ('Waiting on you', li([f['subject'] + (f" (due {f['due']})" if f['due'] and f['due'] != 'N/A' else '') for f in d['followups']] + ['Memo: ' + m for m in d['memos_waiting']])),
        ('Reminders', li([r['subject'] + (' - ' + due_text(r['due']) if r['due'] else '') for r in d['reminders']])),
        ('Recent activity', li([f"{l['age']}: {l['subject']}" for l in d['logs']])),
    ]
    if d['detail'] == 'full' and d.get('recent_completed'):
        cards.append(('Recently completed', li([x['name'] for x in d['recent_completed']])))
    last = '; '.join(filter(None, [f"last Snapshot {d['snapshot']['age']}" if d['snapshot'] else '',
                                   f"last Review {d['review']['age']}" if d['review'] else '']))
    body = (f'<header class="band"><div class="wrap">{logo}<h1>{e(d["project"])}</h1>'
            f'<div class="meta">Version {e(d["version"])} · {e(d["generated"])} UTC</div></div></header>'
            f'<main class="wrap"><p class="axis-eyebrow">Project status</p><p class="lede">{e(clip(d["direction"], 600))}</p>'
            f'<div class="stats">' + ''.join(f'<div class="stat"><strong>{v}</strong>{e(k)}</div>' for v, k in stats) + '</div>'
            f'<div class="grid">' + ''.join(f'<section class="card"><h2>{e(h)}</h2><ul>{b}</ul></section>' for h, b in cards) + '</div>'
            f'<p class="muted">{e(last)}</p>'
            '<footer>A snapshot of this project\'s own records, generated by <code>^status</code>; it does not refresh. '
            'For the live view run <code>^dashboard</code>; for a dated report run <code>^review</code>.<br>'
            'Axis Workflow&trade; is free and open source (MIT License), from Kenneth Younge Advisory - training and consulting at kennethyounge.com.</footer></main>')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(d["project"])} - Axis Workflow status</title>{head}<style>{PAGE_CSS}</style></head>'
            f'<body class="axis-root">{body}</body></html>\n')


# --- Daily brief and "what needs me?" (Practices > Status > What needs me, Daily brief). Reads only the sources the
# Practice names; its only write is the day file `_Temp/status/brief/{day}`, created without overwriting after the
# brief is composed. `--view prune` is Main's ^refresh sweep. The rule for when a brief or its Memo is due is stated
# once, in the Practice and in `due_state()`, which turn.py and boot.py call.
ID_RE = r'\d{4}(?:\.\d{2}){5}\.\d{3}Z'
ID_FILE = re.compile(r'^' + ID_RE + r'\.md$')
MEMO_NAME = re.compile(r'^(' + ID_RE + r'|\d{4}-\d\d-\d\d) - (.+)\.md$')
BRIEF_MEMO = re.compile(r'^Daily brief (\d{4}-\d\d-\d\d)$')
DAY_NAME = re.compile(r'^\d{4}-\d\d-\d\d$')
# Machine-written Log Subjects left out of "since". One list: a new fixed Subject is added here once.
MACHINE_SUBJECTS = ('Session Starting', 'Session Started', 'Shutdown by User', 'Reference move', 'Reference warnings',
                    'Main retired by User (axis retire)', 'Auxiliary Team member allocation',
                    'Auxiliary Team native launch prepared', 'Main displacement prepared')
MACHINE_PREFIXES = ('Capability downgrade:',)
GIVES_BRIEF = ('Main', 'Auxiliary', 'Assistant')
KEEP_DAY_FILES = 14
CHAT_MAX = 900
LIMITS = {'terminal': {'needs': 5, 'needs_view': 10, 'since': 3, 'coming': 2},
          'chat': {'needs': 3, 'needs_view': 5, 'since': 3, 'coming': 2}}
SHOWN = {'Done': ('Done', 'done'), 'Blocked': ('Blocked, updated', 'blocked (updated)'), 'New': ('New', 'new')}


class NotForSession(Exception):
    pass


def parse_id(s):
    try:
        return dt.datetime.strptime((s or '').strip(), '%Y.%m.%d.%H.%M.%S.%fZ').replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def fmt_id(t):
    return t.strftime('%Y.%m.%d.%H.%M.%S.') + f'{t.microsecond // 1000:03d}Z'


def plain(s, width=0):
    """Record text as plain data: link labels only, no code ticks or emphasis, no control or direction characters."""
    s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s or '')
    s = re.sub('[\x00-\x1f\x7f\u200b-\u200f\u202a-\u202e\u2066-\u2069]', '', s).replace('`', '').replace('**', '')
    s = re.sub(r'\s+', ' ', s).strip()
    return s if not width or len(s) <= width else s[:width - 1] + '\u2026'


def session_role(root, sid):
    """The role row name from this session's own Marker, through the shipped role table; None when the session is
    unknown, stopped or malformed, or when AXIS_ROLE names another role. Opens nothing but the Marker."""
    if not sid or not re.fullmatch(ID_RE, sid):
        return None
    marker = root / '_Axis/Agents' / (sid + '.md')
    if marker.is_symlink() or not marker.is_file() or (root / '_Axis/Agents' / (sid + '.kill')).exists():
        return None
    lines = read(marker).splitlines()
    if 'session: ' + sid not in lines:
        return None
    try:
        spec = importlib.util.spec_from_file_location('axis_envelope_roles', Path(__file__).with_name('envelope.py'))
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); table = module.ROLE_TABLE
    except Exception:
        return None
    first = lines[0] if lines else ''
    row = next((r for r in table if r['cls'] == 'session' and ((first == r['subject']) if r['match'] == 'exact' else first.startswith(r['subject']))), None)
    if row is None:
        return None
    declared = re.sub(r'\s+', '', os.environ.get('AXIS_ROLE', '')).lower()
    declared = 'auxiliary' if declared == 'external' else declared
    if declared and declared not in (row['name'].lower(), row['title'].replace(' ', '').lower()):
        return None
    return row['name']


def brief_settings(root, notices):
    """Daily Brief (default Yes), Daily Memo (default No) and the day's time zone."""
    try:
        text = project_file(root, 'SETTINGS.md').read_text(encoding='utf-8', errors='replace')
    except (OSError, ValueError):
        text = ''; notices.append('Settings could not be read; using the defaults.')
    def value(name):
        m = re.search(r'^### ' + re.escape(name) + r'\n(?:(?!\n#{2,3} ).)*?\*\*Value:\*\* ([^\n]+)', text, re.M | re.S)
        return m.group(1).strip() if m else None
    out = {}
    for name, key, default in (('Daily Brief', 'brief', True), ('Daily Memo', 'memo', False)):
        v = value(name)
        if v is None:
            out[key] = default
        elif v.lower() in ('yes', 'no'):
            out[key] = v.lower() == 'yes'
        else:
            out[key] = default; notices.append(f'The {name} Setting is malformed; using {"Yes" if default else "No"}.')
    zone_name = value('Project Time Zone') or 'Unknown'
    tz = None
    if zone_name != 'Unknown':
        try:
            from zoneinfo import ZoneInfo
            tz = dt.timezone.utc if zone_name == 'UTC' else ZoneInfo(zone_name)
        except Exception:
            notices.append("Project Time Zone could not be used; days follow this computer's clock.")
    out['tz'] = tz or dt.datetime.now().astimezone().tzinfo
    return out


def day_dir(root):
    return root / '_Temp/status/brief'


# Directory-descriptor walk (K2): where the host has no-follow opens and descriptor-relative calls, the day folder is reached
# from the project root one folder at a time, each opened with O_NOFOLLOW below the descriptor of the one above, so a link
# put in place of a part after any check is never followed. Elsewhere the path checks of day_folder() stand alone.
FD_WALK = all(hasattr(os, n) for n in ('O_NOFOLLOW', 'O_DIRECTORY')) and all(f in os.supports_dir_fd for f in (os.open, os.mkdir, os.unlink, os.stat))


def open_day_fd(root, create=False):
    """(fd, None) for the open brief folder; (None, None) when a part is missing and create is off; (None, problem) naming the
    first part that is a link or not a folder. With create, a missing part is made below the descriptor of its parent. The
    caller closes fd."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        cur = os.open(str(root), os.O_RDONLY | os.O_DIRECTORY)
    except OSError:
        return None, '_Temp (folder unsafe or not a folder)'
    part = ''
    for name in ('_Temp', 'status', 'brief'):
        part = part + ('/' if part else '') + name
        try:
            nxt = os.open(name, flags, dir_fd=cur)
        except FileNotFoundError:
            if not create:
                os.close(cur); return None, None
            try:
                os.mkdir(name, 0o777, dir_fd=cur)
            except FileExistsError:
                pass
            except OSError:
                os.close(cur); return None, part + ' (folder could not be created)'
            try:
                nxt = os.open(name, flags, dir_fd=cur)
            except OSError:
                os.close(cur); return None, part + ' (folder unsafe or not a folder)'
        except OSError:
            os.close(cur); return None, part + ' (folder unsafe or not a folder)'
        os.close(cur); cur = nxt
    return cur, None


def day_names(root):
    """Names of the regular day files, never a link, oldest first; [] when the folder is missing or unsafe."""
    if not FD_WALK:
        d = day_folder(root)[0]
        try:
            return sorted(p.name for p in d.iterdir() if DAY_NAME.match(p.name) and p.is_file() and not p.is_symlink()) if d else []
        except OSError:
            return []
    fd, _ = open_day_fd(root)
    if fd is None:
        return []
    try:
        out = []
        for n in os.listdir(fd):
            if DAY_NAME.match(n):
                try:
                    if os.stat(n, dir_fd=fd, follow_symlinks=False).st_mode & 0o170000 == 0o100000: out.append(n)  # a regular file
                except OSError:
                    pass
        return sorted(out)
    except OSError:
        return []
    finally:
        os.close(fd)


def day_exists(root, day):
    """Whether an entry of that name is in the brief folder, a link counting as one; False when the folder is missing or unsafe."""
    if not FD_WALK:
        d = day_folder(root)[0]
        return d is not None and os.path.lexists(d / day)
    fd, _ = open_day_fd(root)
    if fd is None:
        return False
    try:
        os.stat(day, dir_fd=fd, follow_symlinks=False); return True
    except OSError:
        return False
    finally:
        os.close(fd)


def day_text(root, name):
    """The text of one day file, read below the descriptor walk and never through a link; None when absent, a link or unreadable."""
    if not FD_WALK:
        d = day_folder(root)[0]
        return None if d is None or (d / name).is_symlink() else read(d / name)
    fd, _ = open_day_fd(root)
    if fd is None:
        return None
    try:
        f = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, 'O_NONBLOCK', 0), dir_fd=fd)
        try:
            if os.fstat(f).st_mode & 0o170000 != 0o100000: return None
            with os.fdopen(f, encoding='utf-8', errors='replace') as h:
                f = None; return h.read()
        finally:
            if f is not None: os.close(f)
    except OSError:
        return None
    finally:
        os.close(fd)


def day_folder(root, create=False):
    """(folder, None) when _Temp, _Temp/status and _Temp/status/brief are each a plain folder, never a link (K2);
    (None, None) when one is missing and create is off; (None, problem) naming the first unsafe part. Checked before
    each write and each deletion; with create, a missing part is made one at a time below a descriptor where the host
    has them (and nothing is created by path after that), else by path and checked again. The write, the deletion and every read go through open_day_fd()."""
    root = Path(root); p = root
    if FD_WALK and create:
        fd, unsafe = open_day_fd(root, create=True)
        if fd is None:
            return None, unsafe or '_Temp/status/brief (folder missing)'
        os.close(fd)
    for part in ('_Temp', '_Temp/status', '_Temp/status/brief'):
        p = root / part
        if create and not FD_WALK and not os.path.lexists(p):
            try:
                p.mkdir()
            except FileExistsError:
                pass
            except OSError:
                return None, part + ' (folder could not be created)'
        if not os.path.lexists(p):
            return None, None
        if p.is_symlink() or getattr(p, 'is_junction', lambda: False)() or not p.is_dir():
            return None, part + ' (folder unsafe or not a folder)'
    if p.resolve() != root.resolve() / '_Temp/status/brief':
        return None, '_Temp/status/brief (folder unsafe or not a folder)'
    return p, None


def project_ready(root):
    p = root / '_Axis/Flags/project-ready'
    return p.is_file() and not p.is_symlink() and parse_id((read(p).splitlines() or [''])[0]) is not None


def brief_memo_exists(root, day):
    for folder in (root / '_Memos', root / '_Memos/Archive'):
        if folder.is_dir() and not folder.is_symlink():
            for f in folder.iterdir():
                m = MEMO_NAME.match(f.name)
                if m and BRIEF_MEMO.match(m.group(2)) and BRIEF_MEMO.match(m.group(2)).group(1) == day:
                    return True
    return False


def due_state(root, sid, now=None, clock_uncertain=False):
    """Whether the brief, and for Main its Memo, is due for this session now. Writes nothing. Raises NotForSession
    for a session that may not give the brief."""
    root = Path(root).resolve()
    role = session_role(root, sid)
    if role not in GIVES_BRIEF:
        raise NotForSession(role)
    notices = []
    s = brief_settings(root, notices)
    now = now or dt.datetime.now(dt.timezone.utc)
    day = now.astimezone(s['tz']).date().isoformat()
    def check(want, done):
        if not want: return False, 'Setting No'
        if clock_uncertain: return False, 'clock unverified'
        if not project_ready(root): return False, 'project not set up'
        if done(): return False, 'shown today' if done is shown else 'written today'
        return True, 'due'
    folder, unsafe = day_folder(root)
    if unsafe: notices.append('No day file is written or read: ' + unsafe + '.')
    shown = lambda: folder is not None and day_exists(root, day)
    brief = check(s['brief'], shown)
    memo = check(s['memo'], lambda: brief_memo_exists(root, day)) if role == 'Main' else (False, 'Main only')
    rec = {'role': role, 'day': day, 'brief_due': brief[0], 'brief_reason': brief[1], 'memo_due': memo[0],
           'memo_reason': memo[1], 'notices': notices}
    if brief[1] == 'shown today':
        rec['shown_by'] = fields(day_text(root, day) or '').get('session')
    return rec


def due_lines(root, sid, surface='{terminal|chat}', startup=False):
    """Lines turn.py and boot.py print on their own when a brief or Memo is due; [] otherwise or on any failure."""
    try:
        d = due_state(root, sid)
    except Exception:
        return []
    out = []
    call = f'(python3 _Axis/Resources/status.py --root . --view brief --if-due --session {sid} --surface {surface})'
    if d['brief_due'] and startup:
        out.append(f'Daily brief due today: give it in this reply under _Axis/Practices/Status.md > Daily brief {call}; '
                   'it replaces the Follow-Up count notice, which you state only when you give no brief.')
    elif d['brief_due']:
        out.append(f'Daily brief due today: after answering a message the User wrote, give it under _Axis/Practices/Status.md > Daily brief {call}.')
    if d['memo_due']:
        out.append('Daily brief Memo due today: write it under _Axis/Practices/Status.md > Daily memo '
                   f'(python3 _Axis/Resources/status.py --root . --view brief --format memo --session {sid}).')
    return out


def listing(folder, family, problems):
    """Entries of a record folder; an unreadable or unsafe folder is reported, never treated as empty."""
    if not folder.exists() and not folder.is_symlink():
        return []
    if folder.is_symlink() or not folder.is_dir():
        problems.append(f'{family} (folder unsafe or not a folder)'); return None
    try:
        return sorted(folder.iterdir(), key=lambda f: f.name)
    except OSError:
        problems.append(f'{family} (folder unreadable)'); return None


def day_label(d, today):
    return 'today' if d == today else d.strftime('%a ') + str(d.day) + d.strftime(' %b')


def age_label(t, now):
    s = (now - t).total_seconds()
    if s < 3600: return f'{max(1, int(s // 60))} min'
    if s < 86400: return f'{int(s // 3600)} h'
    n = int(s // 86400); return f'{n} day' + ('s' if n != 1 else '')


def zone_of(name):
    try:
        from zoneinfo import ZoneInfo
        return dt.timezone.utc if name == 'UTC' else ZoneInfo(name)
    except Exception:
        return None


def needs_items(root, now, tz, clock_uncertain, problems):
    """Open Follow-Ups, due Reminders and Memos waiting on User, in one ordered list (live folders only)."""
    today = now.astimezone(tz).date()
    fus, rems, upcoming = [], [], []
    for f in listing(root / '_Axis/Followups', 'Follow-Ups', problems) or []:
        if not ID_FILE.match(f.name): continue
        if f.is_symlink():
            problems.append(f'one linked Follow-Up, not read ({f.name[:-3]})'); continue
        text = read(f); fl, first = fields(text), (text.splitlines() or [''])[0]
        if not first.startswith('Follow-Up: ') or fl.get('raised') != f.name[:-3] or 'resolved' not in fl or 'due' not in fl or parse_id(fl['raised']) is None:
            problems.append(f'one malformed Follow-Up ({f.name[:-3]})'); continue
        if fl['resolved'] != 'N/A': continue
        try:
            d = None if fl['due'] == 'N/A' else dt.date.fromisoformat(fl['due'])
        except ValueError:
            problems.append(f'one malformed Follow-Up ({f.name[:-3]})'); continue
        fus.append({'kind': 'followup', 'path': '_Axis/Followups/' + f.name, 'subject': plain(first[len('Follow-Up: '):]),
                    'due': d, 'raised': parse_id(fl['raised']), 'reminder': None})
    fus.sort(key=lambda x: (0, x['due'], x['raised']) if x['due'] and x['due'] < today else (1, x['due'], x['raised']) if x['due'] else (2, dt.date.max, x['raised']))
    if clock_uncertain:
        problems.append('Reminder due state unverified (the clock could not be trusted)')
    for f in listing(root / '_Axis/Reminders', 'Reminders', problems) or []:
        if not ID_FILE.match(f.name): continue
        if f.is_symlink():
            problems.append(f'one linked Reminder, not read ({f.name[:-3]})'); continue
        text = read(f); fl, first = fields(text), (text.splitlines() or [''])[0]
        at = parse_id(fl.get('due-at', ''))
        if not first.startswith('Reminder: ') or fl.get('created') != f.name[:-3] or at is None or 'outcome' not in fl:
            problems.append(f'one malformed Reminder ({f.name[:-3]})'); continue
        if fl['outcome'] != 'N/A' or clock_uncertain: continue
        own = zone_of(fl['timezone']) if fl.get('timezone') else None
        r = {'kind': 'reminder', 'path': '_Axis/Reminders/' + f.name, 'subject': plain(first[len('Reminder: '):]), 'at': at,
             'target': fl.get('target', 'N/A'), 'zone': fl.get('timezone') if own is not None else None}
        if at <= now: rems.append(r)
        elif at <= now + dt.timedelta(days=7): upcoming.append(r)
    rems.sort(key=lambda r: r['at']); upcoming.sort(key=lambda r: r['at'])
    by_path = {x['path']: x for x in fus}; loose = []
    for r in rems:
        if r['target'] in by_path and by_path[r['target']]['reminder'] is None: by_path[r['target']]['reminder'] = r
        else: loose.append(r)
    upcoming = [r for r in upcoming if r['target'] not in by_path]
    memos = []
    for f in listing(root / '_Memos', 'Memos', problems) or []:
        m = MEMO_NAME.match(f.name)
        if m and f.is_symlink():
            problems.append(f'one linked Memo, not read ({plain(f.name[:-3], 60)})'); continue
        if not m or not f.is_file(): continue
        try:
            with open(f, encoding='utf-8', errors='replace') as h: head = h.read(2000)
        except OSError:
            problems.append('one Memo (unreadable)'); continue
        if not re.search(r'^- \*\*Status:\*\* waiting on you\s*$', head, re.M): continue
        try:
            created = parse_id(m.group(1)) if m.group(1).endswith('Z') else dt.datetime.fromisoformat(m.group(1)).replace(tzinfo=tz)
        except ValueError:
            created = None
        if created is None:
            problems.append(f'one Memo with an unreadable date in its name ({plain(f.name, 60)})'); continue
        memos.append({'kind': 'memo', 'path': '_Memos/' + f.name, 'subject': 'Memo: ' + plain(m.group(2)), 'created': created, 'name': f.name})
    memos.sort(key=lambda x: (x['created'], x['name']), reverse=True)
    overdue = [x for x in fus if x['due'] and x['due'] < today]
    return overdue + loose + [x for x in fus if x not in overdue] + memos, upcoming, today


def rem_local(r, tz):
    own = zone_of(r['zone']) if r.get('zone') else None
    return r['at'].astimezone(own or tz), (r['zone'] if own is not None and r['zone'] != getattr(tz, 'key', None) else None)


def item_label(x, now, tz, today, clock_uncertain=False):
    if x['kind'] == 'followup' and clock_uncertain:
        if x['due']: return 'due ' + x['due'].strftime('%a ') + str(x['due'].day) + x['due'].strftime(' %b')
        r = x['raised'].astimezone(tz); return 'raised ' + r.strftime('%a ') + str(r.day) + r.strftime(' %b')
    if x['kind'] == 'followup':
        s = ('overdue since ' + day_label(x['due'], today)) if x['due'] and x['due'] < today else ('due ' + day_label(x['due'], today)) if x['due'] else 'waiting ' + age_label(x['raised'], now)
        return s + ('; reminder due' if x['reminder'] else '')
    if x['kind'] == 'reminder':
        local, other = rem_local(x, tz)
        when = local.strftime('%H:%M') if x['at'].astimezone(tz).date() == today else 'since ' + day_label(local.date(), today)
        return 'reminder due ' + when + (f' ({other})' if other else '')
    return 'waiting since ' + day_label(x['created'].astimezone(tz).date(), today)


def task_rows(root, problems):
    try:
        text = project_file(root, 'TASKS.md').read_text(encoding='utf-8', errors='replace')
    except (OSError, ValueError):
        problems.append('Tasks (index unreadable)'); return []
    out, head, body = [], None, []
    for line in text.splitlines() + ['## ']:
        if line.startswith('## '):
            if head is not None and '{{' not in head + '\n'.join(body):
                f = fields('\n'.join(body))
                if 'status' in f:
                    out.append({'name': plain(head), 'status': f['status'], 'created': parse_id(f.get('created', '')),
                                'updated': parse_id(f.get('updated', '')), 'completed': parse_id(f.get('completed', ''))})
            head, body = line[3:].strip(), []
        elif head is not None:
            body.append(line)
    return out


def changes_since(root, since, waiting, problems, rows):
    lines = [('Done', t['name']) for t in rows if t['status'] == 'Completed' and t['completed'] and t['completed'] > since]
    lines += [('Blocked', t['name']) for t in rows if t['status'] == 'Blocked' and t['updated'] and t['updated'] > since]
    lines += [('New', t['name']) for t in rows if t['status'] in ('Active', 'Blocked') and t['created'] and t['created'] > since
              and not (t['status'] == 'Blocked' and t['updated'] and t['updated'] > since)]
    for f in listing(root / '_Memos', 'Memos', []) or []:
        m = MEMO_NAME.match(f.name); t = parse_id(m.group(1)) if m and m.group(1).endswith('Z') else None
        if t and t > since and f.name not in waiting and not BRIEF_MEMO.match(m.group(2)) and not f.is_symlink():
            lines.append(('New memo', plain(m.group(2))))
    logs = []
    for f in listing(root / '_Axis/Logs', 'Logs', problems) or []:
        if not ID_FILE.match(f.name): continue
        t = parse_id(f.name[:-3])
        if t is None:
            problems.append(f'one malformed Log name ({f.name[:-3]})'); continue
        if t > since and f.is_symlink():
            problems.append(f'one linked Log, not read ({f.name[:-3]})'); continue
        if t > since:
            subj = plain((read(f).splitlines() or [''])[0])
            if subj and subj not in MACHINE_SUBJECTS and not subj.startswith(MACHINE_PREFIXES): logs.append(('Log', subj))
    return lines + list(reversed(logs))


def previous_brief(root, today, now):
    names = [n for n in day_names(root) if n < today]
    for name in reversed(names):
        t = parse_id(fields(day_text(root, name) or '').get('shown', ''))
        if t and t < now: return t, False
    return now - dt.timedelta(hours=24), True


def brief_data(root, now, tz, clock_uncertain, notices):
    problems = []
    items, upcoming, today = needs_items(root, now, tz, clock_uncertain, problems)
    since, first = previous_brief(root, today.isoformat(), now)
    rows = task_rows(root, problems)
    ch = changes_since(root, since, {x['name'] for x in items if x['kind'] == 'memo'}, problems, rows)
    blocked = sorted((t for t in rows if t['status'] == 'Blocked' and t['updated']), key=lambda t: t['updated'])
    return {'today': today, 'clock_uncertain': clock_uncertain, 'items': items, 'upcoming': upcoming, 'since': since, 'first': first,
            'changes': ch, 'active': sum(1 for t in rows if t['status'] == 'Active'), 'blocked': sum(1 for t in rows if t['status'] == 'Blocked'),
            'oldest_update': blocked[0] if blocked else None, 'problems': problems, 'notices': notices}


def since_label(d, tz):
    if d['first']: return 'In the last day'
    local, today = d['since'].astimezone(tz), d['today']
    if d['clock_uncertain']: return 'Since ' + local.strftime('%a ') + str(local.day) + local.strftime(' %b %H:%M')
    if local.date() == today: return 'Since ' + local.strftime('%H:%M')
    if (today - local.date()).days < 7: return 'Since ' + local.strftime('%A %H:%M')
    return 'Since ' + day_label(local.date(), today)


def brief_paragraphs(d, now, tz, title, stamp, width, lim):
    today, cu, items, ch, up = d['today'], d['clock_uncertain'], d['items'], d['changes'], d['upcoming']
    out = [f'Your brief for {title} (records at {stamp}).' if not cu else 'Your brief (the date could not be verified).']
    if items:
        n = len(items); block = [f"{n} thing{'s' if n != 1 else ''} need{'' if n != 1 else 's'} you:"]
        block += [f"{i}. {plain(x['subject'], width)} ({item_label(x, now, tz, today, cu)})" for i, x in enumerate(items[:lim['needs']], 1)]
        if n > lim['needs']: block.append(f"+{n - lim['needs']} more. Say \"what needs me?\" to see them all.")
        out.append('\n'.join(block))
    else:
        out.append('Nothing needs you.')
    if ch:
        shown = '; '.join(f"{plain(v, width)} {SHOWN[k][1]}" if k in SHOWN else f"{k.lower()}: {plain(v, width)}" for k, v in ch[:lim['since']])
        more = len(ch) - lim['since']
        out.append(f"{since_label(d, tz)}: {shown}" + (f"; {more} other change{'s' if more != 1 else ''}" if more > 0 else '') + '.')
    if up:
        out.append('Coming up: ' + '; '.join(f"{plain(r['subject'], width)} ({day_label(rem_local(r, tz)[0].date(), today)})" for r in up[:lim['coming']]) + '.')
    out.append(f"Work: {d['active']} active, {d['blocked']} blocked.")
    if d['problems']: out.append('Not checked: ' + '; '.join(d['problems']) + '.')
    return '\n\n'.join(out)


def render_brief(d, now, tz, surface):
    lim, today, cu = LIMITS[surface], d['today'], d['clock_uncertain']
    title = 'today (date unverified)' if cu else today.strftime('%A ') + str(today.day) + today.strftime(' %B')
    stamp = 'clock unverified' if cu else now.astimezone(tz).strftime('%H:%M')
    items, ch, up = d['items'], d['changes'], d['upcoming']
    rule = ' '.join('-' * 14)
    if not items and not ch and not up and not d['problems']:
        quiet = f"Brief for {title}: nothing needs you, and nothing changed {'in the last day' if d['first'] else 'since' + since_label(d, tz)[5:]}."
        return quiet if surface == 'chat' else rule + '\n ' + quiet + '\n' + rule
    if surface == 'chat':
        for width in (90, 60, 40, 24):
            text = brief_paragraphs(d, now, tz, title, stamp, width, lim)
            if len(text) <= CHAT_MAX: break
        return text
    out = [rule, f' BRIEF   {title}   {stamp}' if not cu else f' BRIEF   {title}', rule, '']
    out.append(f"  Needs you ({len(items)}):" if items else '  Needs you: nothing.')
    out += [f"    {i}. {plain(x['subject'], 50)} - {item_label(x, now, tz, today, cu)}" for i, x in enumerate(items[:lim['needs']], 1)]
    if len(items) > lim['needs']: out.append(f"    +{len(items) - lim['needs']} more: ask \"what needs me?\"")
    out.append('')
    if ch:
        out.append(f"  {since_label(d, tz)}:")
        out += [f"    {SHOWN[k][0] if k in SHOWN else k}: {plain(v, 56)}" for k, v in ch[:lim['since']]]
        if len(ch) > lim['since']: out.append(f"    +{len(ch) - lim['since']} more in the records")
        out.append('')
    if up:
        out.append('  Coming up:')
        out += [f"    {day_label(rem_local(r, tz)[0].date(), today):<11} {plain(r['subject'], 56)}" for r in up[:lim['coming']]]
        out.append('')
    lb = d['oldest_update']
    out.append(f"  Work: {d['active']} active, {d['blocked']} blocked" + (f" (oldest update: {plain(lb['name'], 22)}, {age_label(lb['updated'], now)} ago)." if lb and not cu else '.'))
    if d['problems']: out.append('  Not checked: ' + '; '.join(d['problems']) + '.')
    out.append(rule)
    return '\n'.join(out)


def render_memo(d, now, tz):
    """The day's brief as a Memo body for startup-state.py memo (Practices > Memos > Shape); writes nothing."""
    local = now.astimezone(tz); off = local.strftime('%z'); off = off[:3] + ':' + off[3:] if off else '+00:00'
    stamp = local.strftime('%Y-%m-%d %H:%M') + f' (UTC{off})'
    title = d['today'].strftime('%A ') + str(d['today'].day) + d['today'].strftime(' %B')
    body = brief_paragraphs(d, now, tz, title, local.strftime('%H:%M'), 90, {'needs': 10, 'since': 10, 'coming': 7})
    return (f"# Daily brief {d['today'].isoformat()}\n\n- **Status:** record\n- **Type:** memo\n- **Created:** {stamp}\n"
            f"- **Updated:** {stamp}\n\n## Summary\n\n{body}\n")


def render_needs(items, problems, now, tz, today, surface, cu=False):
    lim = LIMITS[surface]['needs_view']; stamp = 'clock unverified' if cu else now.astimezone(tz).strftime('%H:%M')
    if not items:
        if problems: return f"I found nothing that needs you, but I could not check everything: {'; '.join(problems)}."
        return f'Nothing needs you right now (project records at {stamp}).'
    n = len(items); width = 90 if surface == 'chat' else 56
    lines = [f"{i}. {plain(x['subject'], width)} - {item_label(x, now, tz, today, cu)}" for i, x in enumerate(items[:lim], 1)]
    if n > lim: lines.append(f'+{n - lim} more: say "all", or ^followups for the full asks.')
    tail = ('\n\nNot checked: ' + '; '.join(problems) + '.') if problems else ''
    return f"{n} thing{'s' if n != 1 else ''} need{'' if n != 1 else 's'} you (project records at {stamp}):\n\n" + '\n'.join(lines) + tail


def claim_day(root, day, now, sid, role, problems=None):
    """Create today's day file without overwriting: 'claimed', 'exists' or 'failed'. Never deletes or changes a file,
    and never writes through a link: the day folder and every folder above it in the project is checked just before."""
    try:
        d, unsafe = day_folder(root, create=True)
        if d is None:
            if problems is not None: problems.append(unsafe or '_Temp/status/brief (folder missing)')
            return 'failed'
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
        if FD_WALK:
            dfd, unsafe = open_day_fd(root, create=True)
            if dfd is None:
                if problems is not None: problems.append(unsafe or '_Temp/status/brief (folder missing)')
                return 'failed'
            try:
                fd = os.open(day, flags, 0o644, dir_fd=dfd)
            finally:
                os.close(dfd)
        else:
            fd = os.open(d / day, flags, 0o644)
    except FileExistsError:
        return 'exists'
    except OSError:
        return 'failed'
    with os.fdopen(fd, 'w') as f:
        f.write(f'shown: {fmt_id(now)}\nsession: {sid}\nrole: {role}\n')
    return 'claimed'


def prune_days(root, problems):
    """Main's ^refresh sweep: keep the newest KEEP_DAY_FILES day files; never through a link, checked before each deletion."""
    d, unsafe = day_folder(root)
    if d is None:
        if unsafe: problems.append(unsafe)
        return []
    old = day_names(root)[:-KEEP_DAY_FILES]
    dfd = None
    if FD_WALK:
        dfd, unsafe = open_day_fd(root)
        if dfd is None:
            if unsafe: problems.append(unsafe)
            return []
    deleted = []
    try:
        for name in old:
            now_d, unsafe = day_folder(root)
            if now_d != d:
                problems.append(unsafe or '_Temp/status/brief (folder changed during the prune)'); break
            try:
                if dfd is not None: os.unlink(name, dir_fd=dfd)
                else: (d / name).unlink()
            except FileNotFoundError:
                continue
            deleted.append(name)
    finally:
        if dfd is not None: os.close(dfd)
    return deleted


def json_value(o):
    if isinstance(o, dt.datetime): return fmt_id(o.astimezone(dt.timezone.utc))
    if isinstance(o, dt.date): return o.isoformat()
    return str(o)


def brief_main(a, root):
    """--view needs|brief|due|prune. Exit 3 before any project record is opened for a session that may not use it."""
    role = session_role(root, a.session)
    if role not in GIVES_BRIEF:
        print('NOT FOR THIS SESSION: the brief and "what needs me?" serve only the User\'s own sessions (Main, Auxiliary, Assistant).')
        return 3
    if a.view == 'prune':
        if role != 'Main':
            print('NOT FOR THIS SESSION: only Main prunes the day files, in ^refresh.'); return 3
        problems = []; deleted = prune_days(root, problems)
        print(json.dumps({'deleted': deleted, 'not_checked': problems})); return 0
    now = parse_id(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    if now is None:
        print('status: --now is not an Axis timestamp', file=sys.stderr); return 2
    notices = []; s = brief_settings(root, notices); tz = s['tz']; day = now.astimezone(tz).date().isoformat()
    if a.view == 'due':
        print(json.dumps(due_state(root, a.session, now, a.clock_uncertain))); return 0
    if a.view == 'needs':
        problems = []; items, _, today = needs_items(root, now, tz, a.clock_uncertain, problems)
        print(json.dumps({'items': items, 'problems': problems, 'notices': notices}, default=json_value, indent=1) if a.format == 'json'
              else render_needs(items, problems, now, tz, today, a.surface, a.clock_uncertain))
        return 0
    if a.format == 'memo':
        print(render_memo(brief_data(root, now, tz, a.clock_uncertain, notices), now, tz), end=''); return 0
    if a.if_due:
        d = due_state(root, a.session, now, a.clock_uncertain)
        if not d['brief_due']:
            print(f"BRIEF: not due ({d['brief_reason']})."); return 0
    # Compose first: a failure here leaves no day file, so the brief is still due.
    d = brief_data(root, now, tz, a.clock_uncertain, notices)
    text = render_brief(d, now, tz, a.surface) if a.format != 'json' else None
    mark = None; unsafe = []
    if not a.clock_uncertain and project_ready(root):
        mark = claim_day(root, day, now, a.session, role, unsafe)
        if a.if_due and mark == 'exists':
            print('BRIEF: not due (shown today).'); return 0
    if mark == 'failed':
        notices.append("I could not record that today's brief was shown, so it may appear again today.")
        notices += ['No day file is written: ' + x + '.' for x in unsafe]
    if a.format == 'json':
        print(json.dumps({**d, 'day_file': mark}, default=json_value, indent=1))
    else:
        print(text)
        for n in notices: print('Notice: ' + n)
    return 0


def main():
    ap = argparse.ArgumentParser(description='Axis project status, daily brief and "what needs me?".')
    ap.add_argument('--root', default='.')
    ap.add_argument('--format', choices=('text', 'html', 'json', 'memo'), default='text')
    ap.add_argument('--view', choices=('status', 'needs', 'brief', 'due', 'prune'), default='status')
    ap.add_argument('--session')
    ap.add_argument('--surface', choices=('terminal', 'chat'), default='terminal')
    ap.add_argument('--if-due', action='store_true')
    ap.add_argument('--now')
    ap.add_argument('--clock-uncertain', action='store_true')
    ap.add_argument('--detail', choices=('short', 'full'), default='short')
    ap.add_argument('--width', type=int, default=0)
    ap.add_argument('--color', choices=('auto', 'always', 'never'), default='auto')
    a = ap.parse_args()
    root = Path(a.root).resolve()
    if not (root / '_Axis').is_dir():
        print('status: no _Axis/ folder under --root', file=sys.stderr)
        return 2
    if a.view != 'status' or a.format == 'memo':
        if a.format == 'html' or (a.format == 'memo' and a.view != 'brief'):
            print('status: --format html is for ^status; --format memo needs --view brief', file=sys.stderr)
            return 2
        return brief_main(a, root)
    try:
        d = collect(root, a.detail)
    except ValueError as error:
        # Two differing copies of a project file: reported as that error, never one of them shown.
        print(f'status: {error}', file=sys.stderr)
        return 2
    if a.format == 'json':
        print(json.dumps(d, indent=1, default=str))
    elif a.format == 'html':
        out = root / '_Temp' / 'status' / 'index.html'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page(d, root, out), encoding='utf-8')
        print(out)
    else:
        width = a.width or min(shutil.get_terminal_size((80, 24)).columns, 100)
        term = os.environ.get('TERM', '')
        color = a.color == 'always' or (a.color == 'auto' and sys.stdout.isatty() and term not in ('', 'dumb') and not os.environ.get('NO_COLOR'))
        print(text(d, width, color))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
