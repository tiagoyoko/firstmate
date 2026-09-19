# Live validation: a worker's start-up command must survive the pane shell

Branch `fm/fm-launch-1024`. The reported defect: the command that starts a worker
is cut at exactly 1024 bytes when it arrives before the terminal is ready, which
is what happens in a project whose shell checks the Node version on every prompt.

Everything below was driven against real `bin/fm-spawn.sh` running inside a real
tmux server on a private socket, spawning a real worker window whose pane shell
does slow work before every prompt (`PROMPT_COMMAND='sleep 4'`), so firstmate's typed
lines land while the terminal is still in canonical mode - the exact timing the report names.

| File | What it shows |
| --- | --- |
| `maxcanon/summary.txt` | The defect reproduced and fixed in the same window: the terminal accepts exactly 1023 payload bytes of an over-long typed line; the real 2406-byte launch command typed whole never starts the harness; the 81-byte sourced line starts it with all six arguments. |
| `maxcanon/pane-inline.txt`, `maxcanon/pane-measure.txt` | The pane during the failing cases - the typed command visibly cut off mid-line. |
| `live-after/worker-pane-capture.txt` | The real worker pane after a real `fm-spawn` run: four short typed lines, the last one `. '/tmp/fm-<id>/launch.XXXXXX'`. |
| `live-after/harness-argv-env.txt` | The argv and environment the worker harness was actually started with - all six arguments, including the 2407-byte launch brief. |
| `live-after/launch-file-facts.txt` | The launch file: 2407 bytes, mode 600, unique name under the task temp root. |
| `two-homes/summary.txt` | Two firstmate homes launching the same 64-byte task id at once: two distinct launch files, each worker running its own home's brief. |
| `guards/summary.txt` | Both refusal paths: a planted symlink as the task temp root, and a temp root where the launch file cannot be created. Neither starts a worker. |
| `touched-tests.log` | The repository's own tests for the changed files. |

Reproduce with the scripts in this directory (`FM_REPO=<worktree> bash <script> <out-dir>`).
