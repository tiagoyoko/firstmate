#!/usr/bin/env bash
# Adversarial: the launch command is now written to a file under /tmp/fm-<id>.
# Drive the two ways that can go wrong and check firstmate refuses by name
# instead of launching a worker with a command it could not deliver.
#   case symlink   - /tmp/fm-<id> is a symlink planted by someone else
#   case readonly  - /tmp/fm-<id> exists but the launch file cannot be created
set -u
ROOT=${FM_REPO:?set FM_REPO}
OUT=${1:?out dir}
mkdir -p "$OUT"
# shellcheck source=/dev/null
. "$ROOT/tests/fixtures.sh"

SOCK="fmguard-$$"
cleanup() { tmux -L "$SOCK" kill-server >/dev/null 2>&1 || true; }
trap cleanup EXIT
TMP_ROOT=$(fm_test_tmproot fm-guards)
tmux -L "$SOCK" new-session -d -s firstmate -x 200 -y 50
printf 'sleep 3\nPS1=%s\n' "'pane\$ '" > "$TMP_ROOT/rc"

run_guard() { # <case> <id>
  local kase=$1 id=$2 cdir
  cdir="$TMP_ROOT/$kase"
  mkdir -p "$cdir/bin"
  fm_test_spawn_home "$cdir/home" claude
  fm_git_worktree "$cdir/project" "$cdir/wt" "wt-$kase"
  git -C "$cdir/project" worktree add --quiet -b "worker-$kase" "$cdir/worker-wt"
  fm_test_spawn_brief "$cdir/home" "$id"
  mkdir -p "$cdir/home/user-home"
  printf '#!/bin/sh\nprintf HARNESS_STARTED > %s\nsleep 60\n' "$OUT/harness-$kase.marker" > "$cdir/bin/claude"
  chmod +x "$cdir/bin/claude"
  printf '#!/bin/sh\nexit 0\n' > "$cdir/bin/treehouse"; chmod +x "$cdir/bin/treehouse"
  printf '#!/bin/sh\nshift\nexec "$@"\n' > "$cdir/bin/timeout"; chmod +x "$cdir/bin/timeout"
  printf "sleep 3\nPS1='%s\$ '\ntreehouse() { [ \"\$1\" = get ] && cd '%s'; }\n" "$kase" "$cdir/worker-wt" > "$TMP_ROOT/rc-$kase"
  tmux -L "$SOCK" set-option -g default-command "bash --noprofile --rcfile '$TMP_ROOT/rc-$kase' -i"

  cat > "$cdir/run.sh" <<SH
#!/usr/bin/env bash
cd '$cdir/wt' || exit 1
FM_ROOT_OVERRIDE='' FM_HOME='$cdir/home' HOME='$cdir/home/user-home' CLAUDE_CONFIG_DIR='' \\
  FM_STATE_OVERRIDE='$cdir/home/state' FM_DATA_OVERRIDE='$cdir/home/data' \\
  FM_PROJECTS_OVERRIDE='$cdir/home/projects' FM_CONFIG_OVERRIDE='$cdir/home/config' \\
  FM_SPAWN_NO_GUARD=1 PATH='$cdir/bin':"\$PATH" \\
  '$ROOT/bin/fm-spawn.sh' '$id' '$cdir/project' --mode no-mistakes --yolo off > '$OUT/spawn-$kase.txt' 2>&1
echo "SPAWN_EXIT=\$?" >> '$OUT/spawn-$kase.txt'
touch '$OUT/done-$kase'
SH
  chmod +x "$cdir/run.sh"
  tmux -L "$SOCK" new-window -d -t firstmate: -n "d-$kase" -c "$cdir/wt" "bash --noprofile --norc '$cdir/run.sh'"
  local i=0
  while [ $i -lt 150 ]; do [ -f "$OUT/done-$kase" ] && break; sleep 1; i=$((i+1)); done
  sleep 6
  tmux -L "$SOCK" capture-pane -p -t "firstmate:fm-$id" -S -40 > "$OUT/pane-$kase.txt" 2>&1 || true
}

# --- case symlink: someone else's directory wearing this task's temp name ---
SYM_ID="guard-symlink-$(printf 's%.0s' $(seq 1 50))"
DECOY=$(mktemp -d "${TMPDIR:-/tmp}/fm-decoy.XXXXXX")
rm -rf "/tmp/fm-$SYM_ID"; ln -s "$DECOY" "/tmp/fm-$SYM_ID"
run_guard symlink "$SYM_ID"

# --- case readonly: the temp root exists but nothing can be created in it ---
RO_ID="guard-readonly-$(printf 'r%.0s' $(seq 1 49))"
# gotmp already exists, so the earlier GOTMPDIR mkdir -p still succeeds; only
# creating the launch file is impossible.
rm -rf "/tmp/fm-$RO_ID"; mkdir -p "/tmp/fm-$RO_ID/gotmp"; chmod 500 "/tmp/fm-$RO_ID"
run_guard readonly "$RO_ID"

{
  for kase in symlink readonly; do
    echo "=== case $kase ==="
    grep -E '^(error|SPAWN_EXIT)' "$OUT/spawn-$kase.txt" | tail -3
    if [ -f "$OUT/harness-$kase.marker" ]; then
      echo "worker harness: STARTED  <-- unexpected"
    else
      echo "worker harness: never started"
    fi
    echo "decoy/temp root contents after the refusal:"
    ls -A "/tmp/fm-$([ "$kase" = symlink ] && echo "$SYM_ID" || echo "$RO_ID")/" 2>/dev/null | sed 's/^/  /' || echo "  (unreadable)"
    echo
  done
} > "$OUT/summary.txt"
cat "$OUT/summary.txt"
chmod 700 "/tmp/fm-$RO_ID" 2>/dev/null || true
rm -rf "/tmp/fm-$RO_ID" "/tmp/fm-$SYM_ID" "$DECOY"
