import os,subprocess,time,json,threading,signal
from pathlib import Path
ROOT=Path.cwd();LAB=ROOT/'.test-phase';PRODUCT=LAB/'product';EV=Path('/Users/tiagoyoko/.no-mistakes/evidence/01M6CNQCPVNR4SAVF8VXRHBNKZ');FM=LAB/'foreign'
(FM/'state').mkdir(parents=True,exist_ok=True)
expected={'.lock':'1\n','.omp-turnend-extension-loaded':'foreign-guard\n1\n','.omp-watch-extension-loaded':'foreign-watch\n1\n'}
for name,content in expected.items():(FM/'state'/name).write_text(content)
env={'PATH':os.environ['PATH'],'HOME':str(LAB/'user'),'TMPDIR':str(LAB/'tmp'),'ZDOTDIR':str(LAB/'user'),'PI_CODING_AGENT_DIR':str(LAB/'foreign-profile'),'GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','FM_HOME':str(FM),'FM_ROOT_OVERRIDE':str(PRODUCT),'FM_GATE_REFUSE_BYPASS':'1','FM_OMP_HARNESS':'omp','OMP_SKIP_SETUP':'1'}
args=['omp','--mode','rpc','--no-session','--no-lsp','--no-pty','--no-skills','--no-rules','--no-tools','--no-title','--no-extensions','--cwd',str(PRODUCT),'--model','lab-local/echo','-e',str(EV/'provider-only.ts'),'-e',str(PRODUCT/'.omp/extensions/fm-primary-turnend-guard.ts'),'-e',str(PRODUCT/'.omp/extensions/fm-primary-omp-watch.ts')]
frames=[];err=(EV/'foreign-omp.stderr').open('w')
p=subprocess.Popen(args,env=env,cwd=PRODUCT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,start_new_session=True)
def reader():
 with (EV/'foreign-omp.jsonl').open('w') as f:
  for line in p.stdout:
   f.write(line);f.flush()
   try:frames.append(json.loads(line))
   except ValueError:pass
threading.Thread(target=reader,daemon=True).start()
def until(fn,seconds=100):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  if fn():return
  assert p.poll() is None,('omp exited',p.returncode)
  time.sleep(.2)
 raise TimeoutError('foreign-lock probe')
try:
 until(lambda:any(x.get('type')=='ready' for x in frames))
 p.stdin.write(json.dumps({'type':'prompt','id':'foreign-arm','message':'/fm-watch-arm-omp'})+'\n');p.stdin.flush()
 until(lambda:any(x.get('id')=='foreign-arm' and x.get('type')=='prompt_result' for x in frames))
 observed={name:(FM/'state'/name).read_text() for name in expected}
 assert observed==expected,observed
 assert not (FM/'state/.watch.lock').exists()
 errors=[x for x in frames if x.get('type')=='extension_error']
 assert not errors,errors
 notifications=[x for x in frames if x.get('type')=='extension_ui_request']
 assert any('watcher: read-only - session lock is held by another firstmate session' in json.dumps(x) for x in notifications),notifications
 (EV/'foreign-lock-result.json').write_text(json.dumps({'markersPreserved':observed,'watcherAbsent':True,'notifications':notifications,'extensionErrors':errors},indent=2))
 print('PASS: foreign live lock preserves both markers and refuses primary arming')
finally:
 p.stdin.close()
 try:p.wait(timeout=8)
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=8)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 err.close()
