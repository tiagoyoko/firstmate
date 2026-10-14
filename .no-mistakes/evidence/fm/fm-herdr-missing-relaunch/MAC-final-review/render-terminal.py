import hashlib, html, re
from pathlib import Path
E=Path('/Users/tiagoyoko/.no-mistakes/evidence/01M4WR85EFRRBS83H0J31Q5KXX')
p=E/'MAC-r3-live/after-work/ansi.stdout'
s=p.read_text()
colors=['#000000','#cd0000','#00cd00','#cdcd00','#0000ee','#cd00cd','#00cdcd','#e5e5e5','#7f7f7f','#ff0000','#00ff00','#ffff00','#5c5cff','#ff00ff','#00ffff','#ffffff']
def color(n):
 if n<16:return colors[n]
 if n<232:
  v=n-16;a=[0,95,135,175,215,255]
  return '#%02x%02x%02x'%(a[v//36],a[v//6%6],a[v%6])
 return '#%02x%02x%02x'%((8+(n-232)*10,)*3)
style={};out=[];last=0
for m in re.finditer(r'\x1b\[([0-9;]*)m',s):
 if m.start()>last:
  value=html.escape(s[last:m.start()])
  css=';'.join(k+':'+v for k,v in style.items())
  out.append('<span style="'+css+'">'+value+'</span>')
 nums=[int(x or 0) for x in m.group(1).split(';')];i=0
 while i<len(nums):
  n=nums[i]
  if n==0:style={}
  elif n==1:style['font-weight']='700'
  elif n==2:style['opacity']='0.62'
  elif n==3:style['font-style']='italic'
  elif n==7:style.update({'color':'#121212','background':'#dedede'})
  elif n in [38,48] and nums[i+1:i+2]==[5]:
   style['color' if n==38 else 'background']=color(nums[i+2]);i+=2
  elif 30<=n<=37:style['color']=color(n-30)
  elif n==39:style.pop('color',None)
  elif n==49:style.pop('background',None)
  i+=1
 last=m.end()
if last<len(s):out.append(html.escape(s[last:]))
assert '\x1b' not in ''.join(out)
body=''.join(out)
page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>MAC Pi recuperado — captura ANSI</title><style>
body{margin:0;background:#161616;color:#ddd;font-family:ui-monospace,Menlo,monospace;padding:24px;width:fit-content;box-sizing:border-box}header{font:13px system-ui;color:#ccc;margin:0 0 18px;max-width:960px}header strong{font-weight:600}pre{margin:0;background:#101010;color:#dedede;border:1px solid #333;padding:16px;font:12px/18px Menlo,monospace;white-space:pre;tab-size:8}footer{max-width:940px;font:11px/1.5 system-ui;color:#999;margin-top:14px;overflow-wrap:anywhere}
</style><header><strong>MAC · Pi recuperado — captura ANSI real</strong><br>Run 01M4WR85EFRRBS83H0J31Q5KXX · endpoint fm-lab-r3:w1:p2 · 14/10/2026 10:53 UTC</header><pre>'''+body+'''</pre><footer>Renderização fiel da captura ANSI fornecida pelo Herdr; não é imagem da janela nativa. Fonte: MAC-r3-live/after-work/ansi.stdout<br>SHA-256: '''+hashlib.sha256(p.read_bytes()).hexdigest()+'''</footer></html>'''
(E/'MAC-final-review/pi-recovered-live.html').write_text(page)
print('Captura ANSI renderizada; nonce, ferramentas read/write e resultado final preservados.')
