#!/usr/bin/env bash
# secrets-capsule.sh - deterministic, privacy-safe encrypted Secrets transport.
# Run through bash from the project root. Output is deliberately limited to
# stable status tokens and never includes a secret name, value, or local path.
# Requires Bash 3.2+, Git, tar, find, and the official age/age-keygen CLIs.
set -euo pipefail

# Component diagnostics can contain a local path or secret filename. The helper's
# public interface is stdout status tokens only.
exec 2>/dev/null

umask 077

ROOT=${AXIS_PROJECT_ROOT:-$(pwd -P)}
SECRETS_DIR="$ROOT/_Axis/Secrets"
CONFIG_FILE="$SECRETS_DIR/.recipient"
CAPSULE_FILE="$SECRETS_DIR/.capsule.age"
BINDING_FILE="$SECRETS_DIR/.binding"
KEY_DIR=${AXIS_SECRETS_KEY_DIR:-${HOME:?}/.axis/keys}
TMP_BASE=${TMPDIR:-/tmp}
TMP_PATHS=()
NEW_TEMP=""
INIT_KEY=""
INIT_CONFIG_TEMP=""
INIT_STARTED=0
INIT_COMMITTED=0
RECEIVE_ACTIVE=0
RECEIVE_BACKUP=""
RECEIVE_QUARANTINE=""
RECEIVE_BINDING_BACKUP=""
RECEIVE_BINDING_EXISTED=0

safe_error() {
  printf 'error:%s\n' "$1"
  exit "${2:-1}"
}

cleanup() {
  local path
  if [ "$RECEIVE_ACTIVE" -eq 1 ] && declare -F rollback_receive >/dev/null 2>&1; then
    rollback_receive "$RECEIVE_BACKUP" "$RECEIVE_QUARANTINE" || true
    if [ "$RECEIVE_BINDING_EXISTED" -eq 1 ]; then
      cp -p -- "$RECEIVE_BINDING_BACKUP" "$BINDING_FILE" || true
    else
      rm -f -- "$BINDING_FILE"
    fi
    RECEIVE_ACTIVE=0
  fi
  for path in "${TMP_PATHS[@]:-}"; do
    [ -n "$path" ] || continue
    case "$path" in
      "$TMP_BASE"/axis-secrets.*) rm -rf -- "$path" ;;
    esac
  done
  if [ "$INIT_STARTED" -eq 1 ] && [ "$INIT_COMMITTED" -eq 0 ]; then
    [ -n "$INIT_KEY" ] && rm -f -- "$INIT_KEY"
    [ -n "$INIT_CONFIG_TEMP" ] && rm -f -- "$INIT_CONFIG_TEMP"
    rm -f -- "$CONFIG_FILE" "$CAPSULE_FILE" "$BINDING_FILE"
  fi
}
trap cleanup EXIT
trap 'exit 130' HUP INT TERM

new_temp_dir() {
  local path
  path=$(mktemp -d "$TMP_BASE/axis-secrets.XXXXXX") || safe_error temp-unavailable
  chmod 700 "$path" || safe_error temp-permissions
  TMP_PATHS+=("$path")
  NEW_TEMP=$path
}

require_project() {
  [ -d "$SECRETS_DIR" ] || safe_error not-axis-project
  [ -f "$ROOT/_Axis/PROJECT.md" ] || safe_error not-axis-project
  command -v git >/dev/null 2>&1 || safe_error missing-git 3
  local top
  top=$(git -C "$ROOT" rev-parse --show-toplevel 2>/dev/null || true)
  [ -n "$top" ] && [ "$(cd "$top" && pwd -P)" = "$ROOT" ] \
    || safe_error wrong-repository-root
}

require_age() {
  command -v age >/dev/null 2>&1 || safe_error missing-age 3
  command -v age-keygen >/dev/null 2>&1 || safe_error missing-age-keygen 3
  command -v tar >/dev/null 2>&1 || safe_error missing-tar 3
}

is_reserved_name() {
  case "$1" in
    .gitkeep|.recipient|.capsule.age|.binding|.recipient.tmp.*|.capsule.age.tmp.*|.binding.tmp.*) return 0 ;;
    *) return 1 ;;
  esac
}

skip_path() {
  local base_dir=$1 path=$2 rel
  [ "$base_dir" = "$SECRETS_DIR" ] || return 1
  rel=${path#"$base_dir"/}
  case "$rel" in */*) return 1 ;; esac
  is_reserved_name "$rel"
}

validate_tree() {
  local base_dir=$1 count=0 path rel component
  [ -d "$base_dir" ] || return 1
  while IFS= read -r -d '' path; do
    skip_path "$base_dir" "$path" && continue
    count=$((count + 1))
    [ "$count" -le 1000 ] || return 1
    [ ! -L "$path" ] || return 1
    [ -f "$path" ] || [ -d "$path" ] || return 1
    rel=${path#"$base_dir"/}
    case "$rel" in
      ''|/*|*\\*|*$'\n'*|*$'\r'*) return 1 ;;
    esac
    IFS='/' read -r -a components <<< "$rel"
    for component in "${components[@]}"; do
      [ -n "$component" ] || return 1
      [ "$component" != . ] && [ "$component" != .. ] || return 1
      printf '%s' "$component" | LC_ALL=C grep -q '[[:cntrl:]]' && return 1
    done
  done < <(find "$base_dir" -mindepth 1 -print0 2>/dev/null)
  return 0
}

list_entries() {
  local base_dir=$1 path rel
  while IFS= read -r -d '' path; do
    skip_path "$base_dir" "$path" && continue
    rel=${path#"$base_dir"/}
    printf '%s\n' "$rel"
  done < <(find "$base_dir" -mindepth 1 -print0 2>/dev/null) | LC_ALL=C sort
}

tree_empty() {
  [ -z "$(list_entries "$1" | head -n 1)" ]
}

tree_digest() {
  local base_dir=$1 rel path object
  {
    while IFS= read -r rel; do
      [ -n "$rel" ] || continue
      path="$base_dir/$rel"
      if [ -d "$path" ]; then
        printf 'D\0%s\0' "$rel"
      else
        object=$(git -C "$ROOT" hash-object "$path") || return 1
        printf 'F\0%s\0%s\0' "$rel" "$object"
      fi
    done < <(list_entries "$base_dir")
  } | git -C "$ROOT" hash-object --stdin
}

capsule_digest() {
  git -C "$ROOT" hash-object "$CAPSULE_FILE"
}

read_config() {
  [ -f "$CONFIG_FILE" ] || return 1
  [ "$(wc -l < "$CONFIG_FILE" | tr -d ' ')" = 3 ] || return 1
  grep -qx 'axis-secrets-format: 1' "$CONFIG_FILE" || return 1
  KEY_ID=$(sed -n 's/^key-id: //p' "$CONFIG_FILE")
  RECIPIENT=$(sed -n 's/^recipient: //p' "$CONFIG_FILE")
  printf '%s\n' "$KEY_ID" | grep -Eq '^[0-9a-f]{40}([0-9a-f]{24})?$' || return 1
  printf '%s\n' "$RECIPIENT" | grep -Eq '^age1[0-9a-z]+$' || return 1
  IDENTITY_FILE="$KEY_DIR/$KEY_ID.agekey"
}

identity_matches() {
  [ -f "$IDENTITY_FILE" ] || return 1
  [ ! -L "$IDENTITY_FILE" ] || return 1
  [ "$(age-keygen -y "$IDENTITY_FILE" 2>/dev/null)" = "$RECIPIENT" ]
}

read_binding() {
  [ -f "$BINDING_FILE" ] || return 1
  [ "$(wc -l < "$BINDING_FILE" | tr -d ' ')" = 3 ] || return 1
  grep -qx 'axis-secrets-binding: 1' "$BINDING_FILE" || return 1
  BOUND_CAPSULE=$(sed -n 's/^capsule: //p' "$BINDING_FILE")
  BOUND_PLAINTEXT=$(sed -n 's/^plaintext: //p' "$BINDING_FILE")
  printf '%s\n' "$BOUND_CAPSULE" | grep -Eq '^[0-9a-f]{40}([0-9a-f]{24})?$' || return 1
  printf '%s\n' "$BOUND_PLAINTEXT" | grep -Eq '^[0-9a-f]{40}([0-9a-f]{24})?$' || return 1
}

write_binding() {
  local capsule=$1 plaintext=$2 temp="$SECRETS_DIR/.binding.tmp.$$"
  {
    printf 'axis-secrets-binding: 1\n'
    printf 'capsule: %s\n' "$capsule"
    printf 'plaintext: %s\n' "$plaintext"
  } > "$temp" || return 1
  mv -f -- "$temp" "$BINDING_FILE"
}

validate_archive() {
  local capsule=$1 temp names canonical verbose entry rel component first count=0
  new_temp_dir
  temp=$NEW_TEMP
  names="$temp/names"
  canonical="$temp/canonical"
  verbose="$temp/types"
  : > "$canonical"
  if ! age -d -i "$IDENTITY_FILE" "$capsule" 2>"$temp/decrypt-error" \
      | tar -tf - > "$names" 2>"$temp/tar-error"; then
    return 1
  fi
  if ! age -d -i "$IDENTITY_FILE" "$capsule" 2>"$temp/decrypt-type-error" \
      | tar -tvf - > "$verbose" 2>"$temp/tar-type-error"; then
    return 1
  fi
  while IFS= read -r entry; do
    [ "$entry" = ./ ] && continue
    count=$((count + 1))
    [ "$count" -le 1000 ] || return 1
    case "$entry" in ./*) rel=${entry#./} ;; *) return 1 ;; esac
    rel=${rel%/}
    [ -n "$rel" ] || continue
    case "$rel" in /*|*\\*|*$'\n'*|*$'\r'*) return 1 ;; esac
    IFS='/' read -r -a components <<< "$rel"
    for component in "${components[@]}"; do
      [ -n "$component" ] || return 1
      [ "$component" != . ] && [ "$component" != .. ] || return 1
      printf '%s' "$component" | LC_ALL=C grep -q '[[:cntrl:]]' && return 1
    done
    is_reserved_name "${components[0]}" && return 1
    printf '%s\n' "$rel" >> "$canonical" || return 1
  done < "$names"
  [ -z "$(LC_ALL=C sort "$canonical" | uniq -d | head -n 1)" ] || return 1
  while IFS= read -r entry; do
    first=${entry:0:1}
    [ "$first" = - ] || [ "$first" = d ] || return 1
  done < "$verbose"
}

current_status() {
  if [ ! -e "$CONFIG_FILE" ] && [ ! -e "$CAPSULE_FILE" ]; then
    printf 'disabled\n'
    return 0
  fi
  [ -f "$CONFIG_FILE" ] && [ -f "$CAPSULE_FILE" ] || { printf 'malformed\n'; return 0; }
  command -v age >/dev/null 2>&1 && command -v age-keygen >/dev/null 2>&1 \
    || { printf 'missing-tool\n'; return 0; }
  read_config || { printf 'malformed\n'; return 0; }
  identity_matches || { printf 'missing-identity\n'; return 0; }
  validate_tree "$SECRETS_DIR" || { printf 'unsafe-tree\n'; return 0; }
  local plaintext capsule
  plaintext=$(tree_digest "$SECRETS_DIR") || { printf 'unverified\n'; return 0; }
  capsule=$(capsule_digest) || { printf 'malformed\n'; return 0; }
  if read_binding; then
    if [ "$capsule" = "$BOUND_CAPSULE" ] && [ "$plaintext" = "$BOUND_PLAINTEXT" ]; then
      printf 'ready\n'
    elif [ "$capsule" = "$BOUND_CAPSULE" ]; then
      printf 'local-changes\n'
    elif [ "$plaintext" = "$BOUND_PLAINTEXT" ]; then
      printf 'incoming\n'
    else
      printf 'conflict\n'
    fi
  elif tree_empty "$SECRETS_DIR"; then
    printf 'incoming\n'
  else
    printf 'unbound\n'
  fi
}

seal_core() {
  read_config || safe_error malformed-config
  identity_matches || safe_error missing-identity 3
  validate_tree "$SECRETS_DIR" || safe_error unsafe-secret-tree
  local temp candidate plaintext capsule
  new_temp_dir
  temp=$NEW_TEMP
  candidate="$temp/capsule.age"
  if ! (
    cd "$SECRETS_DIR"
    tar --exclude='./.gitkeep' \
      --exclude='./.recipient' \
      --exclude='./.capsule.age' \
      --exclude='./.binding' \
      --exclude='./.recipient.tmp.*' \
      --exclude='./.capsule.age.tmp.*' \
      --exclude='./.binding.tmp.*' -cf - . 2>"$temp/tar-error"
  ) | age -r "$RECIPIENT" -o "$candidate" 2>"$temp/age-error"; then
    safe_error seal-failed
  fi
  [ -s "$candidate" ] || safe_error empty-capsule
  validate_archive "$candidate" || safe_error capsule-verification-failed
  mv -f -- "$candidate" "$CAPSULE_FILE" || safe_error capsule-replace-failed
  plaintext=$(tree_digest "$SECRETS_DIR") || safe_error plaintext-digest-failed
  capsule=$(capsule_digest) || safe_error capsule-digest-failed
  write_binding "$capsule" "$plaintext" || safe_error binding-write-failed
}

move_children() {
  local source=$1 destination=$2 path
  while IFS= read -r -d '' path; do
    mv -- "$path" "$destination/" || return 1
  done < <(find "$source" -mindepth 1 -maxdepth 1 -print0 2>/dev/null)
}

move_plain_children() {
  local source=$1 destination=$2 path rel
  while IFS= read -r -d '' path; do
    rel=${path#"$source"/}
    if [ "$source" = "$SECRETS_DIR" ] && is_reserved_name "$rel"; then
      continue
    fi
    mv -- "$path" "$destination/" || return 1
  done < <(find "$source" -mindepth 1 -maxdepth 1 -print0 2>/dev/null)
}

copy_plain_children() {
  local source=$1 destination=$2 path rel
  while IFS= read -r -d '' path; do
    rel=${path#"$source"/}
    if [ "$source" = "$SECRETS_DIR" ] && is_reserved_name "$rel"; then
      continue
    fi
    cp -pR -- "$path" "$destination/" || return 1
  done < <(find "$source" -mindepth 1 -maxdepth 1 -print0 2>/dev/null)
}

rollback_receive() {
  local backup=$1 quarantine=$2
  mkdir -p "$quarantine"
  move_plain_children "$SECRETS_DIR" "$quarantine" || true
  move_children "$backup" "$SECRETS_DIR" || true
}

receive_core() {
  local status temp extract backup retired quarantine expected actual capsule
  status=$(current_status)
  case "$status" in
    ready) printf 'current\n'; return 0 ;;
    local-changes) printf 'local-changes\n'; return 0 ;;
    incoming) ;;
    conflict|unbound) safe_error secret-conflict 2 ;;
    missing-tool) safe_error missing-age 3 ;;
    missing-identity) safe_error missing-identity 3 ;;
    *) safe_error "$status" ;;
  esac
  read_config || safe_error malformed-config
  identity_matches || safe_error missing-identity 3
  validate_archive "$CAPSULE_FILE" || safe_error capsule-verification-failed
  new_temp_dir
  temp=$NEW_TEMP
  extract="$temp/new"
  backup="$temp/old"
  retired="$temp/retired"
  quarantine="$temp/rollback-new"
  mkdir -p "$extract" "$backup" "$retired" "$quarantine"
  if ! age -d -i "$IDENTITY_FILE" "$CAPSULE_FILE" 2>"$temp/decrypt-error" \
      | tar -xf - -C "$extract" 2>"$temp/extract-error"; then
    safe_error capsule-extract-failed
  fi
  validate_tree "$extract" || safe_error unsafe-capsule-tree
  expected=$(tree_digest "$extract") || safe_error incoming-digest-failed
  copy_plain_children "$SECRETS_DIR" "$backup" || safe_error local-backup-failed
  if [ -f "$BINDING_FILE" ]; then
    RECEIVE_BINDING_BACKUP="$temp/old-binding"
    cp -p -- "$BINDING_FILE" "$RECEIVE_BINDING_BACKUP" || safe_error binding-backup-failed
    RECEIVE_BINDING_EXISTED=1
  else
    RECEIVE_BINDING_BACKUP=""
    RECEIVE_BINDING_EXISTED=0
  fi
  RECEIVE_BACKUP=$backup
  RECEIVE_QUARANTINE=$quarantine
  RECEIVE_ACTIVE=1
  move_plain_children "$SECRETS_DIR" "$retired" || safe_error local-retire-failed
  move_children "$extract" "$SECRETS_DIR" || safe_error secret-install-failed
  actual=$(tree_digest "$SECRETS_DIR") || safe_error installed-digest-failed
  if [ "$actual" != "$expected" ]; then
    safe_error installed-digest-mismatch
  fi
  capsule=$(capsule_digest) || safe_error capsule-digest-failed
  write_binding "$capsule" "$actual" || safe_error binding-write-failed
  RECEIVE_ACTIVE=0
  printf 'received\n'
}

init_capsule() {
  require_age
  [ ! -e "$CONFIG_FILE" ] && [ ! -e "$CAPSULE_FILE" ] && [ ! -e "$BINDING_FILE" ] \
    || safe_error already-configured
  mkdir -p "$KEY_DIR" || safe_error key-directory-unavailable
  chmod 700 "$KEY_DIR" || safe_error key-directory-permissions
  local temp temp_key recipient key_id config_temp
  new_temp_dir
  temp=$NEW_TEMP
  temp_key="$temp/identity.agekey"
  age-keygen -o "$temp_key" >"$temp/keygen-output" 2>"$temp/keygen-error" \
    || safe_error key-generation-failed
  recipient=$(age-keygen -y "$temp_key" 2>"$temp/key-read-error") \
    || safe_error recipient-read-failed
  printf '%s\n' "$recipient" | grep -Eq '^age1[0-9a-z]+$' \
    || safe_error recipient-invalid
  key_id=$(printf '%s\n' "$recipient" | git -C "$ROOT" hash-object --stdin) \
    || safe_error key-id-failed
  INIT_KEY="$KEY_DIR/$key_id.agekey"
  [ ! -e "$INIT_KEY" ] || safe_error key-id-collision
  mv -- "$temp_key" "$INIT_KEY" || safe_error key-install-failed
  INIT_STARTED=1
  chmod 600 "$INIT_KEY" || safe_error key-permissions
  config_temp="$SECRETS_DIR/.recipient.tmp.$$"
  INIT_CONFIG_TEMP=$config_temp
  {
    printf 'axis-secrets-format: 1\n'
    printf 'key-id: %s\n' "$key_id"
    printf 'recipient: %s\n' "$recipient"
  } > "$config_temp" || safe_error config-write-failed
  mv -- "$config_temp" "$CONFIG_FILE" || safe_error config-replace-failed
  INIT_CONFIG_TEMP=""
  seal_core
  INIT_COMMITTED=1
  printf 'initialized:%s\n' "$key_id"
}

require_project
command=${1:-status}
case "$command" in
  init) init_capsule ;;
  status) current_status ;;
  seal)
    require_age
    status=$(current_status)
    case "$status" in
      ready|local-changes) seal_core; printf 'sealed\n' ;;
      incoming|conflict|unbound) safe_error secret-conflict 2 ;;
      missing-tool) safe_error missing-age 3 ;;
      missing-identity) safe_error missing-identity 3 ;;
      *) safe_error "$status" ;;
    esac
    ;;
  receive)
    require_age
    receive_core
    ;;
  *) safe_error unknown-command ;;
esac
