import assert from 'node:assert/strict';
import {existsSync, readFileSync, appendFileSync} from 'node:fs';

export default async function(pi: any) {
  const root = process.env.FM_HOME!;
  const log = process.env.LAB_PROBE_LOG!;
  const {loadExtensions, bindPreparedExtensions} = await import(process.env.LAB_NATIVE_PACKAGE + '/src/extensibility/extensions/loader.ts');
  const {ExtensionRunner} = await import(process.env.LAB_NATIVE_PACKAGE + '/src/extensibility/extensions/runner.ts');
  const {SessionManager} = await import(process.env.LAB_NATIVE_PACKAGE + '/src/session/session-manager.ts');
  const paths = ['fm-primary-turnend-guard.ts','fm-primary-omp-watch.ts'].map(p=>root+'/.omp/extensions/'+p);
  const record = (name: string, data: any) => appendFileSync(log, JSON.stringify({name,data,time:Date.now()})+'\n');
  assert.equal(existsSync(root+'/state'), false);
  const prepared = await loadExtensions(paths,root);
  assert.deepEqual(prepared.errors, []);
  assert.equal(existsSync(root+'/state'), false);
  function host(loaded: any, kind: string, id: string) {
    const identity = {kind,id,name:id,depth:0,...(kind==='sub'?{parentId:'main'}:{})};
    const sessionManager = SessionManager.inMemory(root);
    const runner = new ExtensionRunner(loaded.extensions,loaded.runtime,root,sessionManager,{},undefined,undefined,undefined,undefined,identity);
    const errors: any[]=[]; runner.onError((e:any)=>errors.push(e));
    const arm=loaded.extensions.flatMap((x:any)=>[...x.tools.values()]).find((x:any)=>x.definition.name==='fm_watch_arm_omp').definition;
    return {runner, errors, arm:()=>arm.execute('probe',{},undefined,undefined,runner.createContext())};
  }
  const early=host(prepared,'sub','early-child');
  for (const type of ['session_start','session_compact','session_stop','session_shutdown']) await early.runner.emit({type});
  assert.equal((await early.arm()).details.ok,false);
  assert.equal(existsSync(root+'/state'),false);
  record('early-child-no-state',{depth:0,stateExists:false,errors:early.errors});
  const dormant=host(await bindPreparedExtensions(prepared.preparedExtensions,root),'main','dormant');
  assert.equal(existsSync(root+'/state'),false);
  // Bind the same vendor-prepared factories to the CLI's real main API. Using
  // another importer for main would test two independent module instances.
  const handlers = new Map<string,any[]>();
  let primaryTool:any;
  const observedAPI = new Proxy(pi,{get(target,key){
    if(key==='on')return (event:string,handler:any)=>{handlers.set(event,[...(handlers.get(event)||[]),handler]);target.on(event,handler);};
    if(key==='registerTool')return (tool:any)=>{if(tool.name==='fm_watch_arm_omp')primaryTool=tool;target.registerTool(tool);};
    return target[key];
  }});
  for (const extension of prepared.preparedExtensions) await extension.factory(observedAPI);
  pi.registerProvider('lab-local',{
    baseUrl:process.env.LAB_PROVIDER_URL,apiKey:'disposable-local-only',api:'openai-completions',
    models:[{id:'echo',name:'Disposable local responder',reasoning:false,input:['text'],cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:128000,maxTokens:1024}]
  });
  pi.registerCommand('lab-child', {description:'Exercise native depth-zero child against live primary',handler:async()=>{
    const pidBefore=readFileSync(root+'/state/.watch.lock/pid','utf8').trim();
    const child=host(await bindPreparedExtensions(prepared.preparedExtensions,root),'sub','late-child');
    for(const type of ['session_start','session_compact','session_stop','session_shutdown']) await child.runner.emit({type});
    const childArm=await child.arm();
    const dormantArm=await dormant.arm();
    await dormant.runner.emit({type:'session_shutdown'});
    assert.equal(childArm.details.ok,false);
    assert.equal(dormantArm.details.ok,false);
    assert.deepEqual(child.errors,[]);
    const pidAfter=readFileSync(root+'/state/.watch.lock/pid','utf8').trim();
    assert.equal(pidAfter,pidBefore);
    record('child-dormant-preserve-primary',{pidBefore,pidAfter,childArm:childArm.details,dormantArm:dormantArm.details});
    pi.sendMessage({customType:'lab-observation',content:'LIVE_CHILD_DORMANT_OK',display:true});
  }});
  pi.registerCommand('lab-replace-primary',{description:'Drive real native session replacement and stale callbacks',handler:async(_args:any,ctx:any)=>{
    const before=readFileSync(root+'/state/.watch.lock/pid','utf8').trim();
    const loaded=await bindPreparedExtensions(prepared.preparedExtensions,root);
    loaded.runtime.sendUserMessage=(content:any,options:any)=>pi.sendUserMessage(content,options);
    const replacement=host(loaded,'main','replacement-primary');
    await replacement.runner.emit({type:'session_start'});
    let after='';
    for(let i=0;i<300;i++){
      try{after=readFileSync(root+'/state/.watch.lock/pid','utf8').trim();}catch{}
      if(after && after!==before)break;
      await new Promise(r=>setTimeout(r,20));
    }
    assert.notEqual(after,before);
    const staleArm=await primaryTool.execute('stale',{},undefined,undefined,ctx);
    assert.equal(staleArm.details.ok,false);
    for(const handler of handlers.get('session_shutdown')||[])await handler({type:'session_shutdown'},ctx);
    assert.equal((await replacement.arm()).details.ok,true);
    assert.equal(readFileSync(root+'/state/.watch.lock/pid','utf8').trim(),after);
    await replacement.runner.emit({type:'session_shutdown'});
    assert.equal((await replacement.arm()).details.ok,false);
    await replacement.runner.emit({type:'session_start'});
    assert.equal((await replacement.arm()).details.ok,true);
    assert.deepEqual(replacement.errors,[]);
    record('native-replacement-stale-rejection',{before,after,staleArm:staleArm.details,shutdownArmRejected:true,sameInstanceRestart:true});
    pi.sendMessage({customType:'lab-observation',content:'LIVE_REPLACEMENT_STALE_OK',display:true});
  }});
  pi.on('session_start',(_event:any,ctx:any)=>record('native-primary-start',{agent:ctx.agent,stateExists:existsSync(root+'/state')}));
  pi.on('session_shutdown',()=>record('native-primary-shutdown',{}));
}
