#!/usr/bin/env bash
# Live drive: run bin/fm-spawn.sh INSIDE a real tmux server (private socket),
# spawning a worker window whose pane shell is deliberately slow to reach its
# prompt (the "checks the Node version on every command" delay from the report).
# A recorder stands in for the `claude` harness and writes the argv + env it was
# actually started with. Proves the launch command survives the pane's canonical
# line discipline (MAX_CANON = 1024 on macOS) end to end.
#
# Usage: live-tmux-launch-drive.sh <out-dir>
set -u
ROOT=${FM_REPO:?set FM_REPO to the worktree root}
OUT=${1:?out dir}
mkdir -p "$OUT"

# shellcheck source=/dev/null
. "$ROOT/tests/fixtures.sh"

SOCKET="fmlive-$$"
REAL_TMUX=$(command -v tmux)
cleanup() { "$REAL_TMUX" -L "$SOCKET" kill-server >/dev/null 2>&1 || true; }
trap cleanup EXIT

TMP_ROOT=$(fm_test_tmproot fm-live-launch)
ID="live-launch-$(printf 'x%.0s' $(seq 1 52))"   # 64-byte maximum task id
[ "${#ID}" -eq 64 ] || { echo "id must be 64 bytes, got ${#ID}" >&2; exit 1; }

CASE="$TMP_ROOT/case"
HOME_DIR="$CASE/home"
PROJ="$CASE/project-$(printf 'd%.0s' $(seq 1 120))"
WT="$CASE/wt-$(printf 'd%.0s' $(seq 1 120))"
BIN="$CASE/bin"
mkdir -p "$CASE" "$BIN"

fm_test_spawn_home "$HOME_DIR" claude
fm_git_worktree "$PROJ" "$WT" "wt-live"
WORKER_WT="$CASE/worker-wt-$(printf 'w%.0s' $(seq 1 110))"
git -C "$PROJ" worktree add --quiet -b worker-live "$WORKER_WT"
fm_test_spawn_brief "$HOME_DIR" "$ID"
printf 'FM_LIVE_ALLOWED\n' > "$HOME_DIR/config/launch-env-allowlist"
mkdir -p "$HOME_DIR/user-home"

# Recorder harness: records exactly what the pane shell started.
cat > "$BIN/claude" <<SH
#!/bin/sh
{ printf 'argc:%s\n' "\$#"; printf 'arg:%s\n' "\$@"; env | LC_ALL=C sort | grep -v '^_=\|^SHLVL=\|^OLDPWD='; } > '$OUT/harness-argv-env.txt'
printf 'HARNESS_STARTED\n' > '$OUT/harness-started.marker'
sleep 120
SH
chmod +x "$BIN/claude"
printf '#!/bin/sh\nexit 0\n' > "$BIN/treehouse"; chmod +x "$BIN/treehouse"
printf '#!/bin/sh\nshift\nexec "$@"\n' > "$BIN/timeout"; chmod +x "$BIN/timeout"

# The worker pane's shell: slow to reach its prompt, exactly like the affected
# project's per-prompt Node version check. While it sleeps the tty is still in
# canonical mode, so anything typed is subject to MAX_CANON.
cat > "$CASE/slow-rc" <<RC
# Stand-in for the per-command \`node --version\` check named in the report: the
# shell does slow work before EVERY prompt, so anything typed while it runs is
# read through the tty's canonical line discipline, not by readline.
PROMPT_COMMAND='sleep 4'
sleep 4
PS1='live\$ '
# treehouse is a shell function in real use: it moves the pane into the
# isolated worktree fm-spawn then discovers through pane_current_path.
treehouse() { [ "\$1" = get ] && cd '$WORKER_WT'; }
RC
PANE_CMD="bash --noprofile --rcfile '$CASE/slow-rc' -i"

"$REAL_TMUX" -L "$SOCKET" new-session -d -s firstmate -x 240 -y 60
"$REAL_TMUX" -L "$SOCKET" set-option -g default-command "$PANE_CMD"
"$REAL_TMUX" -L "$SOCKET" set-option -g history-limit 20000

# Run fm-spawn from inside a real pane of that server, so every tmux call it
# makes (session name, pane path, new-window, send-keys) hits the real server.
cat > "$CASE/run-spawn.sh" <<SH
#!/usr/bin/env bash
cd '$WT' || exit 1
FM_ROOT_OVERRIDE='' FM_HOME='$HOME_DIR' HOME='$HOME_DIR/user-home' \\
  CLAUDE_CONFIG_DIR='' \\
  FM_STATE_OVERRIDE='$HOME_DIR/state' FM_DATA_OVERRIDE='$HOME_DIR/data' \\
  FM_PROJECTS_OVERRIDE='$HOME_DIR/projects' FM_CONFIG_OVERRIDE='$HOME_DIR/config' \\
  FM_SPAWN_NO_GUARD=1 \\
  FM_LIVE_ALLOWED=kept FM_LIVE_DROPPED=leaked \\
  PATH='$BIN':"\$PATH" \\
  '$ROOT/bin/fm-spawn.sh' '$ID' '$PROJ' --mode no-mistakes --yolo off > '$OUT/fm-spawn-stdout.txt' 2>&1
echo "SPAWN_EXIT=\$?" >> '$OUT/fm-spawn-stdout.txt'
touch '$OUT/spawn.done'
SH
chmod +x "$CASE/run-spawn.sh"

"$REAL_TMUX" -L "$SOCKET" new-window -d -t firstmate: -n driver -c "$WT" \
  "bash --noprofile --norc '$CASE/run-spawn.sh'"

for _ in $(seq 1 120); do [ -f "$OUT/spawn.done" ] && break; sleep 1; done
[ -f "$OUT/spawn.done" ] || { echo "fm-spawn never finished" >&2; cat "$OUT/fm-spawn-stdout.txt" 2>/dev/null; exit 1; }

# The worker window is fm-<id>; wait for the harness recorder to be started by
# the pane shell once its slow prompt finally arrives.
for _ in $(seq 1 60); do [ -f "$OUT/harness-started.marker" ] && break; sleep 1; done

"$REAL_TMUX" -L "$SOCKET" capture-pane -p -t "firstmate:fm-$ID" -S -80 > "$OUT/worker-pane-capture.txt" 2>&1 || true
"$REAL_TMUX" -L "$SOCKET" list-windows -t firstmate -F '#{window_name}' > "$OUT/windows.txt" 2>&1 || true

{
  echo "task id bytes: ${#ID}"
  echo "worktree: $WT"
  echo "--- typed launch line (what tmux send-keys -l actually carried) ---"
  ls -l /tmp/fm-$ID/launch.* 2>/dev/null
  echo "--- launch file byte size (the command that had to reach the shell) ---"
  wc -c /tmp/fm-$ID/launch.* 2>/dev/null
  echo "--- launch file mode ---"
  stat -f '%Lp %N' /tmp/fm-$ID/launch.* 2>/dev/null
} > "$OUT/launch-file-facts.txt" 2>&1

cp "$(ls -t /tmp/fm-$ID/launch.* | head -1)" "$OUT/launch-file-contents.txt" 2>/dev/null || true
echo "LIVE_DRIVE_DONE id=$ID"
