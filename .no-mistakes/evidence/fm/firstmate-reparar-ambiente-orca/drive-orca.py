import os, json, subprocess, time, shlex
from pathlib import Path
ROOT=Path.cwd(); LAB=ROOT/'.test-phase'; EV=Path('/Users/tiagoyoko/.no-mistakes/evidence/01M6CNQCPVNR4SAVF8VXRHBNKZ')
FM=LAB/'orca-firstmate'; PROJECT=LAB/'orca-project'; USER=LAB/'orca-user'
for p in [FM/'state',FM/'config',FM/'data/orca-live',PROJECT,LAB/'orca-omp-profile']:p.mkdir(parents=True,exist_ok=True)
env={'PATH':os.environ['PATH'],'HOME':str(USER),'ZDOTDIR':str(USER),'TMPDIR':str(LAB/'tmp'),'ORCA_USER_DATA_PATH':str(ROOT/'o'),'XDG_CONFIG_HOME':str(USER/'config'),'XDG_DATA_HOME':str(USER/'data'),'XDG_CACHE_HOME':str(USER/'cache'),'GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','FM_ROOT_OVERRIDE':str(ROOT),'FM_HOME':str(FM),'FM_GATE_REFUSE_BYPASS':'1','OMP_SKIP_SETUP':'1','PI_CODING_AGENT_DIR':str(LAB/'orca-omp-profile')}
log=(EV/'orca-control-live.log').open('w')
def run(args,expected=0,timeout=120):
    log.write('$ '+shlex.join([str(a) for a in args])+'\n');log.flush()
    r=subprocess.run([str(a) for a in args],env=env,cwd=ROOT,text=True,capture_output=True,timeout=timeout)
    log.write(r.stdout+r.stderr+'\nexit='+str(r.returncode)+'\n');log.flush()
    print(shlex.join([str(a) for a in args]),'exit=',r.returncode,flush=True)
    if expected is not None: assert r.returncode==expected,r.stdout+r.stderr
    return r
run(['git','init','-q','-b','main',PROJECT])
(PROJECT/'README.md').write_text('Disposable Firstmate Orca control acceptance fixture.\n')
run(['git','-C',PROJECT,'add','README.md'])
run(['git','-C',PROJECT,'-c','user.name=Test','-c','user.email=test@example.invalid','-c','commit.gpgsign=false','commit','-qm','Disposable fixture'])
(FM/'data/orca-live/brief.md').write_text('# Task\n## Captain\'s intent\nValidate isolated Orca control delivery without provider calls.\n\n## Firstmate spec\nThe operator test drives an idle OMP. No business tasks or external credentials.\n')
launch='HOME='+shlex.quote(str(USER))+' ZDOTDIR='+shlex.quote(str(USER))+' PI_CODING_AGENT_DIR='+shlex.quote(str(LAB/'orca-omp-profile'))+' OMP_SKIP_SETUP=1 omp --no-extensions --no-skills --no-rules --no-lsp --no-title --no-tools --no-session'
run([ROOT/'bin/fm-spawn.sh','orca-live',PROJECT,'--scout',launch,'--backend','orca'],timeout=180)
meta={line.split('=',1)[0]:line.split('=',1)[1] for line in (FM/'state/orca-live.meta').read_text().splitlines() if '=' in line}
(EV/'orca-spawn-metadata.json').write_text(json.dumps(meta,indent=2))
assert meta['backend']=='orca'
assert str(ROOT) in meta['worktree'],meta
terminal=meta['terminal']
for i in range(60):
    r=run([ROOT/'bin/fm-peek.sh','fm-orca-live'],expected=None)
    if '❯' in r.stdout or 'No API key' in r.stdout or 'No models available' in r.stdout:break
    time.sleep(1)
run([ROOT/'bin/fm-control.sh','orca-live','interrupt'])
for action,extra in [('exit',[]),('relaunch',['--note','Disposable boundary probe'])]:
    r=run([ROOT/'bin/fm-control.sh','orca-live',action,*extra],expected=None)
    assert r.returncode!=0
    assert 'no recovery-grade agent-state classifier' in r.stderr
run([ROOT/'bin/fm-peek.sh','fm-orca-live'])
(FM/'data/orca-live/report.md').write_text('# Isolated Orca verification\nThe real runtime received the interrupt. Exit and relaunch were refused without a recovery-grade classifier. This disposable task has no pending decisions.\n')
run([ROOT/'bin/fm-captain-hold.sh','complete','orca-live','--none'])
run([ROOT/'bin/fm-teardown.sh','orca-live'],timeout=180)
run(['orca','terminal','read','--terminal',terminal,'--json'],expected=None)
print('PASS: real Orca spawn/control/verified-exit refusal/teardown',flush=True)
log.close()
