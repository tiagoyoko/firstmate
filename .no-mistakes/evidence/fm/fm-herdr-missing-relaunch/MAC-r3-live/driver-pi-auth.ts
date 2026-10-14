import fs from 'node:fs';
export default function(pi) {
 const credential=JSON.parse(fs.readFileSync('/Users/tiagoyoko/.pi/agent/auth.json','utf8'))['openai-codex'];
 if(credential.type!=='oauth'||typeof credential.access!=='string'||credential.expires < Date.now()+600000) throw new Error('Existing OAuth not valid for isolated test; no login or refresh allowed');
 pi.registerProvider('openai-codex',{apiKey:credential.access});
 for (const kind of ['session_start','message_end','tool_call','tool_result','agent_end']) pi.on(kind,(event)=>{
  fs.appendFileSync("/Users/tiagoyoko/.no-mistakes/worktrees/2b0478335959/01M4WR85EFRRBS83H0J31Q5KXX/.test-phase/pi-events.jsonl",JSON.stringify({timestamp:new Date().toISOString(),kind,event})+'\n');
 });
}
