#!/usr/bin/env bash
# Adversarial: two firstmate homes launch the SAME task id at the same time on
# one machine (the collision the repo documents in bin/fm-backend-hometag-lib.sh).
# Both write their launch command under the shared /tmp/fm-<id> root while both
# pane shells are still slow-starting. Each worker must end up running ITS OWN
# home's brief.
set -u
ROOT=${FM_REPO:?set FM_REPO}
OUT=${1:?out dir}
mkdir -p "$OUT"
# shellcheck source=/dev/null
. "$ROOT/tests/fixtures.sh"

SOCK="fmtwo-$$"
cleanup() { tmux -L "$SOCK" kill-server >/dev/null 2>&1 || true; }
trap cleanup EXIT

TMP_ROOT=$(fm_test_tmproot fm-two-homes)
ID="two-homes-$(printf 'y%.0s' $(seq 1 54))"
[ "${#ID}" -eq 64 ] || { echo "id must be 64 bytes, got ${#ID}"; exit 1; }
rm -rf "/tmp/fm-$ID"

tmux -L "$SOCK" new-session -d -s homeA -x 240 -y 60
tmux -L "$SOCK" new-session -d -s homeB -x 240 -y 60
printf 'sleep 6\nPS1=%s\n' "'pane\$ '" > "$TMP_ROOT/slow-rc"
tmux -L "$SOCK" set-option -g default-command "bash --noprofile --rcfile '$TMP_ROOT/slow-rc' -i"

setup_home() { # <tag> <session>
  local tag=$1 cdir
  cdir="$TMP_ROOT/$tag"
  mkdir -p "$cdir/bin"
  fm_test_spawn_home "$cdir/home" claude
  fm_git_worktree "$cdir/project" "$cdir/wt" "wt-$tag"
  git -C "$cdir/project" worktree add --quiet -b "worker-$tag" "$cdir/worker-wt"
  fm_test_spawn_brief "$cdir/home" "$ID" "INTENT-BELONGS-TO-HOME-$tag"
  mkdir -p "$cdir/home/user-home"
  cat > "$cdir/bin/claude" <<SH
#!/bin/sh
{ printf 'arg:%s\n' "\$@"; printf 'FM_TASK_ID=%s\n' "\$FM_TASK_ID"; } > '$OUT/harness-$tag.txt'
sleep 120
SH
  chmod +x "$cdir/bin/claude"
  printf '#!/bin/sh\nexit 0\n' > "$cdir/bin/treehouse"; chmod +x "$cdir/bin/treehouse"
  printf '#!/bin/sh\nshift\nexec "$@"\n' > "$cdir/bin/timeout"; chmod +x "$cdir/bin/timeout"
  cat >> "$TMP_ROOT/slow-rc-$tag" <<RC
sleep 6
PS1='$tag\$ '
treehouse() { [ "\$1" = get ] && cd '$cdir/worker-wt'; }
RC
  cat > "$cdir/run.sh" <<SH
#!/usr/bin/env bash
cd '$cdir/wt' || exit 1
FM_ROOT_OVERRIDE='' FM_HOME='$cdir/home' HOME='$cdir/home/user-home' CLAUDE_CONFIG_DIR='' \\
  FM_STATE_OVERRIDE='$cdir/home/state' FM_DATA_OVERRIDE='$cdir/home/data' \\
  FM_PROJECTS_OVERRIDE='$cdir/home/projects' FM_CONFIG_OVERRIDE='$cdir/home/config' \\
  FM_SPAWN_NO_GUARD=1 PATH='$cdir/bin':"\$PATH" \\
  '$ROOT/bin/fm-spawn.sh' '$ID' '$cdir/project' --mode no-mistakes --yolo off > '$OUT/spawn-$tag.txt' 2>&1
echo "SPAWN_EXIT=\$?" >> '$OUT/spawn-$tag.txt'
touch '$OUT/done-$tag'
SH
  chmod +x "$cdir/run.sh"
}

setup_home A homeA
setup_home B homeB
# Each home's worker pane needs its own treehouse target, so give each session
# its own rc.
tmux -L "$SOCK" set-option -t homeA default-command "bash --noprofile --rcfile '$TMP_ROOT/slow-rc-A' -i"
tmux -L "$SOCK" set-option -t homeB default-command "bash --noprofile --rcfile '$TMP_ROOT/slow-rc-B' -i"

# Launch both at once: home B's spawn lands inside the window where A's pane
# shell is still starting up.
tmux -L "$SOCK" new-window -d -t homeA: -n driverA -c "$TMP_ROOT/A/wt" "bash --noprofile --norc '$TMP_ROOT/A/run.sh'"
tmux -L "$SOCK" new-window -d -t homeB: -n driverB -c "$TMP_ROOT/B/wt" "bash --noprofile --norc '$TMP_ROOT/B/run.sh'"

for _ in $(seq 1 180); do [ -f "$OUT/done-A" ] && [ -f "$OUT/done-B" ] && break; sleep 1; done
for _ in $(seq 1 90); do [ -s "$OUT/harness-A.txt" ] && [ -s "$OUT/harness-B.txt" ] && break; sleep 1; done

{
  echo "shared task temp root: /tmp/fm-$ID"
  echo
  echo "--- launch files written there (one per launch, owner-only) ---"
  ls -l "/tmp/fm-$ID"/launch.* 2>/dev/null
  echo
  echo "--- which brief each worker's harness actually received ---"
  for tag in A B; do
    if [ -s "$OUT/harness-$tag.txt" ]; then
      printf 'home %s worker -> %s\n' "$tag" \
        "$(grep -o 'INTENT-BELONGS-TO-HOME-[AB]' "$OUT/harness-$tag.txt" | sort -u | tr '\n' ' ')"
    else
      printf 'home %s worker -> harness never started\n' "$tag"
    fi
  done
} > "$OUT/summary.txt"
cat "$OUT/summary.txt"
cp -R "/tmp/fm-$ID" "$OUT/task-tmp-root" 2>/dev/null || true
rm -rf "/tmp/fm-$ID"
