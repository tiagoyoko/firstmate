"""Audit generated protocol/state contracts, never implementation source."""
import datetime, hashlib, json, subprocess
from pathlib import Path

ROOT = Path('/Users/tiagoyoko/.no-mistakes/worktrees/2b0478335959/01M4WR85EFRRBS83H0J31Q5KXX')
E = Path('/Users/tiagoyoko/.no-mistakes/evidence/01M4WR85EFRRBS83H0J31Q5KXX')
R = E / 'MAC-r3-live'
D = E / 'MAC-final-review'
TARGET = '64befcb503c6ee1eb07426e5c7ee802d5077cb30'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p): return [json.loads(x) for x in p.read_text().splitlines() if x]
def meta(p): return dict(x.split('=',1) for x in p.read_text().splitlines() if '=' in x)
def moment(s): return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))

head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert head == TARGET
checks = {}
for filename in ['hashes.json','MAC-final-hashes.json']:
    hashes = json.loads((R/filename).read_text())['files']
    for name,value in hashes.items():
        assert sha(R/name)==value, (filename,name)
    checks[filename]=len(hashes)
audit = json.loads((E/'MAC-followup-evidence-audit.json').read_text())
for name,value in audit['hashes_dos_artefatos_originais_preservados'].items():
    assert sha(E/name)==value, name
checks['originais']=len(audit['hashes_dos_artefatos_originais_preservados'])

driver, herdr, pi = [lines(R/name) for name in ['driver.jsonl','herdr-raw.jsonl','pi-events.jsonl']]
for name,events in [('driver',driver),('herdr',herdr),('pi',pi)]:
    times=[moment(x['timestamp']) for x in events]
    assert times == sorted(times), name
assert next(x for x in driver if x.get('phase')=='preflight')['target']==TARGET
attempt = next(x for x in driver if x.get('phase')=='single-live-attempt')
nonce_event=next(x for x in driver if x.get('phase')=='nonce-introduced-only-in-note')
nonce=nonce_event['nonce']
remove=[x for x in herdr if 'workspace' in x.get('command',[]) and 'close' in x['command']]
assert len(remove)==1 and remove[0]['exit_code']==0
old=meta(R/'before-removal-ready/projected.meta')
new=meta(R/'after-work/projected.meta')
assert old['herdr_workspace_id'] == 'w2' and new['herdr_workspace_id']=='w1'
assert old['window'] != new['window'] and new['herdr_session']==old['herdr_session']=='fm-lab-r3'
for field in ['worktree','project','endpoint_task_id','kind','mode','yolo','durable_probe','harness','backend']:
    assert old[field]==new[field], field
stages=['before-removal-ready','after-removal','before-fixed-verification','after-fixed-relaunch','after-work']
preserved={}
for name in ['continuar.json','continuar.txt','projected.herdr-presentation']:
    hashes=[sha(R/stage/name) for stage in stages]
    assert len(set(hashes))==1,name
    preserved[name]=hashes[0]
for stage in stages[:-1]: assert not (R/stage/'resultado.json').exists()
assert (R/'before-fixed-verification/workspaces.stdout').read_bytes()==(R/'after-removal/workspaces.stdout').read_bytes()
missing=[x for x in driver if x.get('stdout','').strip()=='missing']
assert len(missing)>=2
heads=[x['stdout'].strip() for x in driver if x.get('command',[])[-2:]==['rev-parse','HEAD'] and '.test-phase/wt' in ' '.join(x['command'])]
assert heads and set(heads)=={attempt['head']}
input_json=json.loads((R/'before-removal-ready/continuar.json').read_text())
output=json.loads((R/'after-work/resultado.json').read_text())
assert output=={'nonce':nonce,'sum':sum(input_json['values']),'count':len(input_json['values'])}
user_messages=[x for x in pi if x['kind']=='message_end' and x['event'].get('message',{}).get('role')=='user']
assert len(user_messages)==1
message=''.join(x.get('text','') for x in user_messages[0]['event']['message']['content'])
assert nonce in message
calls=[x for x in pi if x['kind']=='tool_call']
assert [x['event']['toolName'] for x in calls]==['read','write']
for call in calls:
    event=call['event']
    matches=[x for x in pi if x['kind']=='tool_result' and x['event']['toolCallId']==event['toolCallId']]
    assert len(matches)==1 and matches[0]['event']['isError'] is False
    assert moment(user_messages[0]['timestamp'])<moment(call['timestamp'])<=moment(matches[0]['timestamp'])
assert calls[0]['event']['input']['path']==old['worktree']+'/continuar.json'
assert calls[1]['event']['input']['path']==old['worktree']+'/resultado.json'
assert calls[1]['event']['input']['content'].encode()==(R/'after-work/resultado.json').read_bytes()
assert any(x['kind']=='agent_end' for x in pi)
assert nonce in (R/'after-work/ansi.stdout').read_text()
assert json.loads((R/'after-work/process.stdout').read_text())['result']['process_info']['foreground_processes'][0]['argv0']=='pi'
report={
 'title':'MAC auditoria final dos contratos de estado e protocolo',
 'audited_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'run_id':E.name,'tested_head_sha':head,'live_execution_already_completed_in_this_run':True,
 'new_live_execution_in_this_audit':False,
 'verified_hash_inventories':checks,'old_endpoint':old['window'],'new_endpoint':new['window'],
 'single_workspace_removal_at':remove[0]['timestamp'],'nonce_introduced_at':nonce_event['timestamp'],
 'pi_note_received_at':user_messages[0]['timestamp'],
 'pi_tool_calls':[{'timestamp':x['timestamp'],'tool':x['event']['toolName'],'path':x['event']['input']['path']} for x in calls],
 'result':output,'output_sha256':sha(R/'after-work/resultado.json'),'preserved_sha256':preserved,
 'fixture_head':attempt['head'],'missing_state_checks':len(missing),
 'limits':['A primeira chamada recusou fixture sem # Task. Houve teardown e reprovision da mesma sessao antes da retomada bem-sucedida.',
           'Comprova recuperacao do estado persistido em apresentacao flat; nao restaura o workspace aninhado nem comprova continuidade do processo Herdr original.',
           'O manifesto firstmate-followup-live-evidence.json nao foi usado como prova isolada de sucesso.'],
 'worktree_status':subprocess.check_output(['git','status','--short','--untracked-files=all'],cwd=ROOT,text=True),
 'transient_fixture_absent':not (ROOT/'.test-phase').exists(),
}
assert report['worktree_status']=='' and report['transient_fixture_absent']
(D/'audit-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'endpoint_before':old['window'],'endpoint_after':new['window'],'pi_result':output,'work_preserved_sha256':preserved,'raw_artifact_hashes_match':True,'live_rerun_repeated':False},ensure_ascii=False))
