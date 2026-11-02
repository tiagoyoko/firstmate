import os, sys, json, time, subprocess, threading, http.server, signal, shutil
from pathlib import Path

ROOT=Path.cwd()
EV=Path('/Users/tiagoyoko/.no-mistakes/evidence/01M6CNQCPVNR4SAVF8VXRHBNKZ')
LAB=ROOT/'.test-phase'
PRODUCT=LAB/'product'
frames=[]; requests=[]
def record(name,data):
    with (EV/'omp-observations.jsonl').open('a') as f: f.write(json.dumps({'name':name,'data':data,'time':time.time()})+'\n')
    print(name,json.dumps(data),flush=True)
class Provider(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        requests.append(body)
        with (EV/'local-provider-requests.jsonl').open('a') as f: f.write(json.dumps(body)+'\n')
        self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
        for delta,finish in [({'role':'assistant','content':'LAB_RESPONSE'},None),({},'stop')]:
            chunk={'id':'chatcmpl-local','object':'chat.completion.chunk','created':int(time.time()),'model':'echo','choices':[{'index':0,'delta':delta,'finish_reason':finish}]}
            self.wfile.write(('data: '+json.dumps(chunk)+'\n\n').encode());self.wfile.flush()
        self.wfile.write(b'data: [DONE]\n\n');self.wfile.flush()
def until(fn,label,seconds=100):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if fn(): return
        if proc.poll() is not None: raise RuntimeError('OMP exited '+str(proc.returncode)+' while '+label)
        time.sleep(.1)
    raise TimeoutError(label)
(EV/'native-live-probe.jsonl').write_text('')
if (PRODUCT/'state').exists(): shutil.rmtree(PRODUCT/'state')
for p in ['user','tmp','omp-profile']:(LAB/p).mkdir(exist_ok=True)
env={'PATH':os.environ['PATH'],'HOME':str(LAB/'user'),'TMPDIR':str(LAB/'tmp'),'PI_CODING_AGENT_DIR':str(LAB/'omp-profile'),'XDG_CONFIG_HOME':str(LAB/'user/config'),'XDG_CACHE_HOME':str(LAB/'user/cache'),'XDG_DATA_HOME':str(LAB/'user/data'),'ZDOTDIR':str(LAB/'user'),'GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','FM_HOME':str(PRODUCT),'FM_ROOT_OVERRIDE':str(PRODUCT),'FM_GATE_REFUSE_BYPASS':'1','FM_OMP_HARNESS':'omp','OMP_SKIP_SETUP':'1','FM_POLL':'1','FM_SIGNAL_GRACE':'0','FM_HEARTBEAT':'600','LAB_NATIVE_PACKAGE':'/Users/tiagoyoko/.bun/install/global/node_modules/@oh-my-pi/pi-coding-agent','LAB_PROBE_LOG':str(EV/'native-live-probe.jsonl')}
subprocess.run(['git','init','-q',str(PRODUCT)],env=env,check=True)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Provider)
threading.Thread(target=server.serve_forever,daemon=True).start()
env['LAB_PROVIDER_URL']='http://127.0.0.1:'+str(server.server_port)+'/v1'
args=['omp','--mode','rpc','--no-session','--no-ui','--no-lsp','--no-pty','--no-skills','--no-rules','--no-tools','--no-title','--no-extensions','--cwd',str(PRODUCT),'--config',str(PRODUCT/'.omp/fm-worker-overlay.yml'),'--auto-approve','--model','lab-local/echo','--thinking','off','-e',str(EV/'live-probe.ts')]
record('launch',{'command':args,'stateAbsent':not (PRODUCT/'state').exists(),'provider':'disposable loopback HTTP; no operator credentials'})
err=(EV/'omp-rpc.stderr').open('w')
proc=subprocess.Popen(args,env=env,cwd=PRODUCT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,start_new_session=True)
def reader():
    with (EV/'omp-rpc.jsonl').open('w') as log:
        for line in proc.stdout:
            log.write(line);log.flush()
            try: frames.append(json.loads(line))
            except ValueError: pass
threading.Thread(target=reader,daemon=True).start()
def send(kind,**kwargs):
    record('rpc-input',{'type':kind,**kwargs});proc.stdin.write(json.dumps({'type':kind,**kwargs})+'\n');proc.stdin.flush()
try:
    until(lambda:any(x.get('type')=='ready' for x in frames),'RPC ready',120)
    until(lambda:len(list((PRODUCT/'state').glob('.omp-*-extension-loaded')))==2,'both activation markers',60)
    markers={p.name:p.read_text() for p in (PRODUCT/'state').glob('.omp-*-extension-loaded')}
    assert len(markers)==2,markers
    assert all(v.splitlines()[1]==str(proc.pid) for v in markers.values())
    record('fresh-primary-markers',markers)
    send('prompt',id='first',message='Return LAB_RESPONSE. Do not call tools.')
    until(lambda:len(requests)>0,'first local provider request',150)
    first_context=json.dumps(requests[0])
    record('first-provider-context',{'hasDigest':'SESSION START - ' in first_context,'containsStartupText':'session-start' in first_context,'extensionErrors':[x for x in frames if x.get('type')=='extension_error']})
    until(lambda:(PRODUCT/'state/.session-start-complete').exists(),'startup completion',150)
    record('startup-completed',{'pid':(PRODUCT/'state/.lock').read_text().strip(),'completion':(PRODUCT/'state/.session-start-complete').read_text().strip()})
    send('prompt',id='arm',message='/fm-watch-arm-omp')
    until(lambda:(PRODUCT/'state/.watch.lock/pid').exists(),'real watch pid',90)
    before=(PRODUCT/'state/.watch.lock/pid').read_text().strip()
    record('real-watcher-started',{'pid':before})
    send('prompt',id='child',message='/lab-child')
    until(lambda:'child-dormant-preserve-primary' in (EV/'native-live-probe.jsonl').read_text(),'native child observation',60)
    send('prompt',id='arm-after',message='/fm-watch-arm-omp')
    (PRODUCT/'state/lab-signal.meta').write_text('')
    (PRODUCT/'state/lab-signal.status').write_text('done: disposable native live signal\n')
    until(lambda:any(x.get('type')=='queue_update' and 'lab-signal.status' in json.dumps(x) for x in frames),'wake accepted in native queue',100)
    record('wake-accepted-in-native-queue',{'frames':[x for x in frames if x.get('type')=='queue_update' and 'lab-signal.status' in json.dumps(x)]})
    send('prompt',id='consume',message='Continue processing the queued follow-up.')
    until(lambda:any('FIRSTMATE WATCHER WAKE:' in json.dumps(r) and 'lab-signal.status' in json.dumps(r) for r in requests),'queued wake consumed after public prompt',90)
    until(lambda:'successor=started:' in (PRODUCT/'state/.watch-cycle-exits.log').read_text(),'real linked successor',60)
    record('real-successor-and-wake',{'ledger':(PRODUCT/'state/.watch-cycle-exits.log').read_text(),'wakeRequests':sum('FIRSTMATE WATCHER WAKE:' in json.dumps(r) and 'lab-signal.status' in json.dumps(r) for r in requests)})
    before_new=(PRODUCT/'state/.watch.lock/pid').read_text().strip()
    send('new_session',id='replace')
    until(lambda:any(x.get('id')=='replace' and x.get('success') for x in frames),'new session response',60)
    assert (PRODUCT/'state/.watch.lock/pid').exists()
    record('rpc-new-session-continuity',{'before':before_new,'after':(PRODUCT/'state/.watch.lock/pid').read_text().strip(),'note':'OMP 18.12.6 emits session_switch for new_session; existing watcher remains live'})
    send('prompt',id='child-after-new',message='/lab-child')
    until(lambda:(EV/'native-live-probe.jsonl').read_text().count('child-dormant-preserve-primary')==2,'stale/dormant check after replacement',60)
    send('prompt',id='native-replace',message='/lab-replace-primary')
    until(lambda:'native-replacement-stale-rejection' in (EV/'native-live-probe.jsonl').read_text(),'native primary replacement with real watcher',90)
    record('PASS',{'markers':True,'nativeChild':True,'dormant':True,'realWake':True,'successor':True,'replacement':True})
finally:
    for name in ['.watch-cycle-exits.log','.session-start.timings','.startup-network.timings']:
        src=PRODUCT/'state'/name
        if src.exists():shutil.copy2(src,EV/('omp'+name))
    proc.stdin.close()
    try:proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid,signal.SIGTERM)
        try:proc.wait(timeout=8)
        except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
    server.shutdown();server.server_close();err.close()
    record('cleanup',{'ompExit':proc.returncode})
