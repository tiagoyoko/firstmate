import os, subprocess, json, shlex, time
from pathlib import Path
ROOT=Path.cwd();LAB=ROOT/'.test-phase';EV=Path('/Users/tiagoyoko/.no-mistakes/evidence/01M6CNQCPVNR4SAVF8VXRHBNKZ')
env={'PATH':os.environ['PATH'],'HOME':str(LAB/'orca-user'),'ZDOTDIR':str(LAB/'orca-user'),'TMPDIR':str(LAB/'tmp'),'ORCA_USER_DATA_PATH':str(ROOT/'o')}
log=(EV/'orca-capability-live.log').open('w')
def run(args,e=env):
    r=subprocess.run(args,env=e,cwd=ROOT,text=True,capture_output=True,timeout=45)
    log.write('$ '+shlex.join(args)+'\n'+r.stdout+r.stderr+'\nexit='+str(r.returncode)+'\n');log.flush()
    return r
code='import os,tty,time; tty.setraw(0); print("RECEIVER_READY",flush=True); b=os.read(0,1); print("RECEIVED_BYTE="+b.hex(),flush=True); time.sleep(30)'
created=run(['orca','terminal','create','--worktree','path:'+str(LAB/'product'),'--title','Escape-capability-guard','--command','python3 -u -c '+shlex.quote(code),'--json'])
data=json.loads(created.stdout);assert data['ok'],data
t=data['result']['terminal']['handle']
def read():return json.loads(run(['orca','terminal','read','--terminal',t,'--limit','20','--json']).stdout)
try:
    for i in range(40):
        tail=read()
        if 'RECEIVER_READY' in tail['result']['terminal']['tail']: break
        time.sleep(.2)
    assert 'RECEIVER_READY' in tail['result']['terminal']['tail']
    old={**env,'PATH':str(LAB/'old-orca/Orca.app/Contents/Resources/bin')+':'+env['PATH']}
    cmd=['bash','-c','. bin/backends/orca.sh; fm_backend_orca_send_key "$1" Escape','_',t]
    rejected=run(cmd,old)
    assert rejected.returncode!=0
    assert 'does not document verbatim control-byte input' in rejected.stderr
    after_old=read()
    assert not any(x=='RECEIVED_BYTE=1b' for x in after_old['result']['terminal']['tail'])
    assert run(cmd).returncode==0
    for i in range(30):
        after_new=read()
        if 'RECEIVED_BYTE=1b' in after_new['result']['terminal']['tail']:break
        time.sleep(.2)
    assert 'RECEIVED_BYTE=1b' in after_new['result']['terminal']['tail']
    (EV/'orca-capability-result.json').write_text(json.dumps({'oldVersion':'1.4.230','currentVersion':'1.4.245','oldRejected':True,'afterOld':after_old,'afterCurrent':after_new},indent=2))
    print('PASS: old real CLI refused before byte delivery; current real CLI delivered 1b',flush=True)
finally:
    run(['orca','terminal','close','--terminal',t,'--json'])
    log.close()
