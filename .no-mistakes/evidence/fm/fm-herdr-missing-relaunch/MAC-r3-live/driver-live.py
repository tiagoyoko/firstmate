import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path.cwd()
assert str(ROOT) == '/Users/tiagoyoko/.no-mistakes/worktrees/2b0478335959/01M4WR85EFRRBS83H0J31Q5KXX'
TEST = ROOT / '.test-phase'
EVIDENCE_ROOT = Path('/Users/tiagoyoko/.no-mistakes/evidence/01M4WR85EFRRBS83H0J31Q5KXX')
EVIDENCE = EVIDENCE_ROOT / 'MAC-r3-live'
SESSION = 'fm-lab-r3'
TASK = 'projected'
HOME_DIR = TEST / 'home'
WT = TEST / 'wt'
PROJ = TEST / 'proj'
REAL_HERDR = '/Users/tiagoyoko/.local/bin/herdr'

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def record(value):
    with (EVIDENCE / 'driver.jsonl').open('a') as f:
        f.write(json.dumps({'timestamp': now(), **value}, ensure_ascii=False) + '\n')

def env():
    result = os.environ.copy()
    for k in ['HERDR_ENV','HERDR_PANE_ID','HERDR_TAB_ID','HERDR_WORKSPACE_ID','HERDR_SOCKET_PATH','HERDR_SESSION','XDG_CONFIG_HOME']:
        result.pop(k, None)
    result.update({
        'PATH': str(TEST / 'bin') + ':' + result['PATH'],
        'HERDR_SESSION': SESSION,
        'HERDR_CONFIG_PATH': str(TEST / 'config.toml'),
        'FM_HERDR_LAB_STATE_DIR': str(TEST / 'lab-state'),
        'FM_HOME': str(HOME_DIR),
        'FM_SPAWN_NO_GUARD': '1',
        'FM_CONTROL_LAUNCH_WAIT': '90',
        'PI_CODING_AGENT_DIR': str(TEST / 'pi'),
        'PI_CODING_AGENT_SESSION_DIR': str(TEST / 'pi-sessions'),
        'PI_OFFLINE': '1',
        'PI_TELEMETRY': '0',
        'TMPDIR': str(TEST / 'tmp'),
        'GIT_CONFIG_GLOBAL': '/dev/null',
        'GIT_CONFIG_SYSTEM': '/dev/null',
    })
    return result

def run(args, check=True, timeout=120):
    started=now()
    p=subprocess.run([str(x) for x in args], cwd=ROOT, env=env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
    record({'started': started, 'command': [str(x) for x in args], 'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    if check and p.returncode:
        raise RuntimeError(f'Command failed ({p.returncode}): {args}: {p.stdout}{p.stderr}')
    return p

def lab(*args, check=True):
    return run([ROOT/'bin/fm-herdr-lab.sh','run',SESSION,*args], check=check)

def shell(body, *args, check=True):
    return run(['bash','-c', 'set -eu; . tests/herdr-test-safety.sh; . bin/fm-backend.sh; fm_backend_source herdr; ' + body, 'test',*args], check=check)

def meta():
    return dict(line.split('=',1) for line in (HOME_DIR/'state/projected.meta').read_text().splitlines() if '=' in line)

def snapshot(stage, pane):
    dest=EVIDENCE/stage
    dest.mkdir()
    for name in ['projected.meta','projected.herdr-presentation','projected.relaunch']:
        p=HOME_DIR/'state'/name
        if p.exists():shutil.copyfile(p,dest/name)
    for name in ['brief.md','launch-brief.md']:
        p=HOME_DIR/'data'/TASK/name
        if p.exists():shutil.copyfile(p,dest/name)
    for name in ['continuar.json','continuar.txt','resultado.json']:
        p=WT/name
        if p.exists():shutil.copyfile(p,dest/name)
    for label,args in [('workspaces',['workspace','list']),('panes',['pane','list']),('process',['pane','process-info','--pane',pane]),('screen',['pane','read',pane,'--source','recent-unwrapped','--lines','150']),('ansi',['pane','read',pane,'--source','visible','--format','ansi'])]:
        p=lab(*args,check=False)
        (dest/(label+'.stdout')).write_text(p.stdout)
        (dest/(label+'.stderr')).write_text(p.stderr)
    record({'snapshot':stage,'files':{p.name:digest(p) for p in dest.iterdir() if p.is_file()}})

def prepare():
    assert not EVIDENCE.exists(), 'Do not overwrite prior evidence'
    EVIDENCE.mkdir()
    record({'phase':'preflight','target':run(['git','rev-parse','HEAD']).stdout.strip(),'original_evidence_hashes':{p.name:digest(p) for p in EVIDENCE_ROOT.iterdir() if p.is_file()}})
    for path in ['bin','tmp','pi','pi-sessions','lab-state','home/state','home/data/projected','home/config']:
        (TEST/path).mkdir(parents=True,exist_ok=True)
    (TEST/'config.toml').write_text('[update]\nversion_check = false\nmanifest_check = false\n[terminal]\ndefault_shell = "/bin/bash"\nshell_mode = "non_login"\nnew_cwd = '+json.dumps(str(TEST))+'\n')
    settings=json.loads(Path('/Users/tiagoyoko/.pi/agent/settings.json').read_text())
    (TEST/'pi/settings.json').write_text(json.dumps({'defaultProvider':settings['defaultProvider'],'defaultModel':settings['defaultModel'],'quietStartup':True}))
    catalog=json.loads(Path('/Users/tiagoyoko/.pi/agent/models-store.json').read_text())
    def secret_field(v):
        if isinstance(v,dict):
            return any(k.lower() in ['apikey','access','refresh','token','secret','authorization','password','cookie'] or secret_field(x) for k,x in v.items())
        return isinstance(v,list) and any(secret_field(x) for x in v)
    assert not secret_field(catalog), 'Catalog may contain credentials'
    (TEST/'pi/models-store.json').write_text(json.dumps(catalog))
    (TEST/'auth.sha256').write_text(digest('/Users/tiagoyoko/.pi/agent/auth.json'))
    (TEST/'bin/herdr').write_text('''#!/usr/bin/env python3
import datetime,json,os,subprocess,sys
from pathlib import Path
args=sys.argv[1:]
p=Path('''+repr(str(EVIDENCE/'herdr-raw.jsonl'))+''')
def log(v):
 with p.open('a') as f:f.write(json.dumps({'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),**v},ensure_ascii=False)+'\\n')
if args and args[0]=='server':
 log({'command':args,'event':'exec-server'})
 os.execv('''+repr(REAL_HERDR)+''',['herdr',*args])
r=subprocess.run(['''+repr(REAL_HERDR)+''',*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
log({'command':args,'exit_code':r.returncode,'stdout':r.stdout.decode(errors='replace'),'stderr':r.stderr.decode(errors='replace')})
sys.stdout.buffer.write(r.stdout);sys.stderr.buffer.write(r.stderr);sys.exit(r.returncode)
''')
    (TEST/'pi-auth.ts').write_text('''import fs from 'node:fs';
export default function(pi) {
 const credential=JSON.parse(fs.readFileSync('/Users/tiagoyoko/.pi/agent/auth.json','utf8'))['openai-codex'];
 if(credential.type!=='oauth'||typeof credential.access!=='string'||credential.expires < Date.now()+600000) throw new Error('Existing OAuth not valid for isolated test; no login or refresh allowed');
 pi.registerProvider('openai-codex',{apiKey:credential.access});
 for (const kind of ['session_start','message_end','tool_call','tool_result','agent_end']) pi.on(kind,(event)=>{
  fs.appendFileSync('''+json.dumps(str(TEST/'pi-events.jsonl'))+''',JSON.stringify({timestamp:new Date().toISOString(),kind,event})+'\\n');
 });
}
''')
    (TEST/'bin/pi').write_text('#!/usr/bin/env bash\nexec /opt/homebrew/bin/pi --offline --no-context-files --no-skills --no-extensions --no-mcp --no-prompt-templates --no-themes --tools read,write -e '+str(TEST/'pi-auth.ts')+' --system-prompt '+"'Você participa de um teste isolado. Siga apenas as instruções específicas da nota de recuperação. Use somente read/write em arquivos no cwd. Não controle Firstmate, gates, pipeline, PR ou CI. Não leia credenciais.'"+' "$@"\n')
    for p in (TEST/'bin').iterdir(): p.chmod(0o755)
    run([ROOT/'bin/fm-herdr-lab.sh','provision',SESSION])
    run(['git','init','-q',PROJ])
    (PROJ/'README.md').write_text('MAC isolated recovery test\n')
    run(['git','-C',PROJ,'add','README.md'])
    run(['git','-C',PROJ,'-c','user.name=Firstmate Tests','-c','user.email=tests@example.invalid','commit','-qm','initial'])
    run(['git','-C',PROJ,'worktree','add','--quiet','-b',TASK,WT])
    (WT/'continuar.json').write_text(json.dumps({'values':[13,21,34],'stage':'pending'},sort_keys=True)+'\n')
    (WT/'continuar.txt').write_text('MAC preservar trabalho não commitado\n')
    brief='# MAC teste de recuperação\n\n## Captain\'s intent\nValidar apenas a retomada do trabalho em fixture isolada.\n\n## Firstmate spec\nAguarde a nota de recuperação. Ela conterá instruções completas para ler continuar.json e criar resultado.json; cumpra apenas essa operação com read/write. Não execute pipeline, PR, CI, Git ou comandos Firstmate. Preserve continuar.json e continuar.txt.\n'
    (HOME_DIR/'data/projected/brief.md').write_text(brief)
    (HOME_DIR/'data/projected/launch-brief.md').write_text(brief)
    p=shell('''
container=$(fm_backend_herdr_container_ensure "$1")
parent=${container%%$'\\t'*}; parent=${parent#*:}
token=$(fm_backend_herdr_projection_journal_create "$FM_HOME/state" projected)
label="└ projected · p:$token"
fm_backend_herdr_projection_create_task "$1" "$label" fm-projected
workspace=$FM_BACKEND_HERDR_PROJECTION_WORKSPACE_ID
tab=$FM_BACKEND_HERDR_PROJECTION_TAB_ID
pane=$FM_BACKEND_HERDR_PROJECTION_PANE_ID
fm_backend_herdr_projection_journal_bind "$FM_HOME/state/projected.herdr-presentation" projected "$FM_HOME" "$HERDR_SESSION" "$workspace" "$tab" "$pane" "$parent" firstmate "$label" fm-projected
printf '%s %s %s %s\\n' "$parent" "$workspace" "$tab" "$pane"
''',str(WT))
    parent, workspace, tab, pane=p.stdout.strip().split()
    m={'window':f'{SESSION}:{pane}','endpoint_task_id':TASK,'worktree':str(WT),'project':str(PROJ),'harness':'pi','kind':'ship','mode':'no-mistakes','yolo':'off','model':'default','effort':'default','backend':'herdr','herdr_session':SESSION,'herdr_workspace_id':workspace,'herdr_tab_id':tab,'herdr_pane_id':pane,'durable_probe':'MAC_KEEP_R3'}
    (HOME_DIR/'state/projected.meta').write_text(''.join(k+'='+v+'\n' for k,v in m.items()))
    lab('pane','run',pane,str(TEST/'bin/pi'))
    for _ in range(150):
        state=shell('fm_backend_agent_state herdr "$1"',f'{SESSION}:{pane}').stdout.strip()
        if state=='alive':break
        time.sleep(.2)
    assert state=='alive',state
    snapshot('before-removal',pane)
    print(json.dumps({'prepared':True,'session':SESSION,'endpoint':m['window'],'evidence':str(EVIDENCE)}))

def execute():
    m=meta(); pane=m['herdr_pane_id']; ws=m['herdr_workspace_id']
    old_hashes={name:digest(WT/name) for name in ['continuar.json','continuar.txt']}
    old_head=run(['git','-C',WT,'rev-parse','HEAD']).stdout.strip()
    journal_before=digest(HOME_DIR/'state/projected.herdr-presentation')
    assert not (WT/'resultado.json').exists()
    record({'phase':'single-live-attempt','old':m,'head':old_head,'work_hashes':old_hashes,'journal_hash':journal_before})
    lab('workspace','close',ws)
    snapshot('after-removal',pane)
    missing=shell('fm_backend_agent_state herdr "$1"',m['window']).stdout.strip()
    assert missing=='missing',missing
    nonce='MAC_NOTE_'+uuid.uuid4().hex
    note='Continue o trabalho preservado: leia continuar.json, calcule soma e quantidade dos values e grave resultado.json com as chaves nonce, sum e count; nonce deve ser '+nonce+'. Preserve integralmente continuar.json e continuar.txt. Responda com o resultado e o caminho. Não execute mais nada.'
    record({'phase':'nonce-introduced-only-in-note','nonce':nonce})
    p=shell('bin/fm-control.sh projected relaunch --harness pi --note "$1"',note,check=False)
    (EVIDENCE/'relaunch.stdout').write_text(p.stdout)
    (EVIDENCE/'relaunch.stderr').write_text(p.stderr)
    new=meta()
    snapshot('after-relaunch',new['herdr_pane_id'])
    assert p.returncode==0,p.stderr
    assert new['window']!=m['window']
    assert new['herdr_session']==SESSION
    for k in ['worktree','project','endpoint_task_id','kind','mode','yolo','durable_probe']:
        assert new[k]==m[k],k
    assert digest(HOME_DIR/'state/projected.herdr-presentation')==journal_before
    assert run(['git','-C',WT,'rev-parse','HEAD']).stdout.strip()==old_head
    assert {name:digest(WT/name) for name in old_hashes}==old_hashes
    record({'scenario':'removed-presentation-workspace','result':'pass','old_endpoint':m['window'],'new_endpoint':new['window'],'nonce':nonce})
    deadline=time.monotonic()+180
    while time.monotonic()<deadline:
        if (WT/'resultado.json').exists(): break
        time.sleep(1)
    assert (WT/'resultado.json').exists(),'Pi did not produce resultado.json within 180s'
    output=json.loads((WT/'resultado.json').read_text())
    assert output=={'nonce':nonce,'sum':68,'count':3},output
    time.sleep(3)
    snapshot('after-work',new['herdr_pane_id'])
    record({'scenario':'recovered-pi-processes-note-and-continues','result':'pass','nonce':nonce,'output':output,'output_sha256':digest(WT/'resultado.json'),'preserved_hashes':{name:digest(WT/name) for name in old_hashes}})
    print(json.dumps({'two_scenarios':'pass','output':output,'evidence':str(EVIDENCE)}))

def cleanup():
    if (TEST/'pi-events.jsonl').exists():shutil.copyfile(TEST/'pi-events.jsonl',EVIDENCE/'pi-events.jsonl')
    if (TEST/'pi-sessions').exists():
        shutil.copytree(TEST/'pi-sessions',EVIDENCE/'pi-sessions',dirs_exist_ok=True)
    for p in [TEST/'live.py',TEST/'pi-auth.ts',TEST/'bin/pi',TEST/'bin/herdr',TEST/'config.toml']:
        if p.exists():shutil.copyfile(p,EVIDENCE/('driver-'+p.name))
    run([ROOT/'bin/fm-herdr-lab.sh','teardown',SESSION])
    auth_unchanged=digest('/Users/tiagoyoko/.pi/agent/auth.json')==(TEST/'auth.sha256').read_text()
    record({'phase':'cleanup','global_auth_unchanged':auth_unchanged,'original_evidence_unchanged':{p.name:digest(p) for p in EVIDENCE_ROOT.iterdir() if p.is_file()}})
    assert auth_unchanged,'Global credentials changed'
    (EVIDENCE/'hashes.json').write_text(json.dumps({'timestamp':now(),'files':{str(p.relative_to(EVIDENCE)):digest(p) for p in EVIDENCE.rglob('*') if p.is_file() and p.name!='hashes.json'}},indent=2))
    print(json.dumps({'cleanup':True,'auth_unchanged':auth_unchanged}))

if __name__=='__main__':
    try:
        {'prepare':prepare,'execute':execute,'cleanup':cleanup}[sys.argv[1]]()
    except Exception as e:
        if EVIDENCE.exists():record({'error':str(e),'phase':sys.argv[1]})
        raise
