export default function(pi:any) {
  pi.registerProvider('lab-local',{baseUrl:'http://127.0.0.1:9/v1',apiKey:'disposable-no-requests',api:'openai-completions',models:[{id:'echo',name:'No-call fixture',reasoning:false,input:['text'],cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:128000,maxTokens:1000}]});
}
