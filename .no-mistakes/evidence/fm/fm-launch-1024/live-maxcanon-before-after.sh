#!/usr/bin/env bash
# Adversarial reproduction of the reported defect against a real terminal.
#
# The pane shell does slow work before EVERY prompt (PROMPT_COMMAND='sleep 4',
# the stand-in for the per-command Node version check named in the report), so a
# command typed while it is busy is read through the tty's canonical line
# discipline, which caps a line at MAX_CANON (1024 bytes on macOS).
#
# Three cases, all typed into that same window:
#   measure  how many bytes of an over-long line the shell actually receives
#   inline   the real launch command fm-spawn built, typed whole (pre-fix shape)
#   sourced  the short line that sources that same command (this change)
#
# Usage: live-maxcanon-before-after.sh <out-dir> <real-launch-command-file>
set -u
OUT=${1:?out dir}
LAUNCH_SRC=${2:?path to a real launch command produced by fm-spawn}
mkdir -p "$OUT"
SOCK="fmcanon-$$"
W=$(mktemp -d "${TMPDIR:-/tmp}/fm-canon.XXXXXX")
cleanup() { tmux -L "$SOCK" kill-server >/dev/null 2>&1 || true; rm -rf "$W"; }
trap cleanup EXIT

mkdir -p "$W/bin"
cat > "$W/bin/claude" <<SH
#!/bin/sh
{ printf 'argc:%s\n' "\$#"; printf 'arg:%s\n' "\$@"; } > '$W/harness.txt'
sleep 90
SH
chmod +x "$W/bin/claude"

printf "PROMPT_COMMAND='sleep 4'\nPS1='live\$ '\n" > "$W/rc"
tmux -L "$SOCK" new-session -d -s c -x 240 -y 50
tmux -L "$SOCK" set-option -g default-command "bash --noprofile --rcfile '$W/rc' -i"

# Type <lines...> into a fresh window while its shell is busy before its prompt.
type_into_busy_pane() { # <window> <line>...
  local win=$1; shift
  tmux -L "$SOCK" new-window -d -t c: -n "$win" -c "$W"
  local line
  for line in "$@"; do
    tmux -L "$SOCK" send-keys -t "c:$win" -l "$line"
    tmux -L "$SOCK" send-keys -t "c:$win" Enter
  done
}

# --- case measure: how much of an over-long line survives ---------------------
# A comment line, so the shell does nothing with it: what matters is how much of
# it the terminal accepted, which is exactly what it echoes back.
PAD=$(printf 'A%.0s' $(seq 1 1500))
type_into_busy_pane measure "#$PAD"
sleep 15
tmux -L "$SOCK" capture-pane -p -t c:measure -S -40 > "$OUT/pane-measure.txt"
typed_bytes=$(printf '#%s' "$PAD" | LC_ALL=C wc -c | tr -d ' ')
measured=$(tr -cd 'A' < "$OUT/pane-measure.txt" | LC_ALL=C wc -c | tr -d ' ')
measured=$((measured / 2))   # the pane shows the terminal echo and the shell's own echo

# --- case inline: the real launch command, typed whole ------------------------
LAUNCH=$(cat "$LAUNCH_SRC")
LAUNCH_BYTES=$(printf '%s' "$LAUNCH" | LC_ALL=C wc -c | tr -d ' ')
rm -f "$W/harness.txt"
type_into_busy_pane inline "export PATH='$W/bin':\$PATH" "$LAUNCH"
sleep 20
tmux -L "$SOCK" capture-pane -p -t c:inline -S -40 > "$OUT/pane-inline.txt"
inline_argc=$(head -1 "$W/harness.txt" 2>/dev/null || true)

# --- case sourced: the short line this change types ---------------------------
printf '%s\n' "$LAUNCH" > "$W/launch.file"
SOURCED=". '$W/launch.file'"
SOURCED_BYTES=$(printf '%s' "$SOURCED" | LC_ALL=C wc -c | tr -d ' ')
rm -f "$W/harness.txt"
type_into_busy_pane sourced "export PATH='$W/bin':\$PATH" "$SOURCED"
sleep 20
tmux -L "$SOCK" capture-pane -p -t c:sourced -S -40 > "$OUT/pane-sourced.txt"
sourced_argc=$(head -1 "$W/harness.txt" 2>/dev/null || true)
cp "$W/harness.txt" "$OUT/harness-argv-sourced.txt" 2>/dev/null || true

{
  echo "host MAX_CANON: $(getconf MAX_CANON / 2>/dev/null || echo 1024) bytes"
  echo "pane shell:     bash running PROMPT_COMMAND='sleep 4' before every prompt"
  echo
  echo "measure: typed a ${typed_bytes}-byte line; the terminal accepted ${measured:-0} payload bytes"
  echo
  echo "inline:  the real ${LAUNCH_BYTES}-byte launch command typed whole"
  echo "         harness: ${inline_argc:-never started}"
  echo
  echo "sourced: a ${SOURCED_BYTES}-byte line sourcing that same command"
  echo "         harness: ${sourced_argc:-never started}"
} > "$OUT/summary.txt"
cat "$OUT/summary.txt"
