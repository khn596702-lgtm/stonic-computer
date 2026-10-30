from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
from datetime import datetime, timezone

ROOT = Path(__file__).parent
DATA = ROOT / "stonic-data"
DATA.mkdir(exist_ok=True)
TASKS = DATA / "tasks.json"
if not TASKS.exists():
    TASKS.write_text("[]", encoding="utf-8")

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>STONIC Computer</title><style>
*{box-sizing:border-box}body{margin:0;background:#0d1320;color:#edf3ff;font:16px system-ui,Arial}
main{max-width:850px;margin:auto;padding:22px}header{padding:22px 0}h1{margin:0;font-size:30px}
p{color:#aebbd0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.card{background:#172235;border:1px solid #2a3b55;border-radius:16px;padding:18px;margin:12px 0}
input,button{font:inherit;border-radius:9px;padding:12px;border:1px solid #405572}
input{background:#0d1728;color:white;width:70%;max-width:460px}button{background:#347df4;color:white;border:0}
li{margin:9px 0;overflow-wrap:anywhere}.muted{font-size:13px;color:#91a4bf}
</style></head><body><main>
<header><div class="muted">YOUR ONLINE WORKSPACE</div><h1>STONIC Computer</h1><p>First working foundation · Mobile-friendly dashboard</p></header>
<div class="grid"><section class="card"><div class="muted">SYSTEM STATUS</div><h2 id="status">Checking…</h2><p class="muted">This dashboard runs while its server is running.</p></section>
<section class="card"><div class="muted">WORKSPACE</div><h2>STONIC v0.1</h2><p class="muted">Task list and project files</p></section></div>
<section class="card"><h2>Task manager</h2><form id="taskForm"><input id="taskInput" maxlength="200" placeholder="Write a task…" required> <button>Add task</button></form><ul id="tasks"></ul></section>
<section class="card"><h2>Workspace files</h2><ul id="files"></ul></section>
<p class="muted">Starter version: does not yet execute arbitrary commands or control external websites.</p>
</main><script>
async function refresh(){try{
let h=await fetch('/api/health');let hd=await h.json();document.querySelector('#status').textContent=hd.status;
let t=await(await fetch('/api/tasks')).json();document.querySelector('#tasks').innerHTML=t.map(x=>'<li>'+esc(x)+'</li>').join('')||'<li>No tasks yet</li>';
let f=await(await fetch('/api/files')).json();document.querySelector('#files').innerHTML=f.map(x=>'<li>'+esc(x)+'</li>').join('');
}catch(e){document.querySelector('#status').textContent='Disconnected'}}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
document.querySelector('#taskForm').addEventListener('submit',async e=>{e.preventDefault();let i=document.querySelector('#taskInput');
let r=await fetch('/api/tasks',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:i.value})});if(r.ok){i.value='';refresh()}});
refresh();setInterval(refresh,10000);
</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def reply(self, data, ctype="application/json; charset=utf-8", status=200):
        body=data if isinstance(data,bytes) else json.dumps(data).encode()
        self.send_response(status);self.send_header("Content-Type",ctype);self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def do_GET(self):
        if self.path=="/": return self.reply(PAGE.encode(),"text/html; charset=utf-8")
        if self.path=="/api/health": return self.reply({"status":"Online","version":"0.1","utc":datetime.now(timezone.utc).isoformat()})
        if self.path=="/api/tasks": return self.reply(json.loads(TASKS.read_text(encoding="utf-8")))
        if self.path=="/api/files": return self.reply(sorted(p.name for p in ROOT.iterdir() if p.name not in {".git","__pycache__"}))
        return self.reply({"error":"Not found"},status=404)
    def do_POST(self):
        if self.path!="/api/tasks": return self.reply({"error":"Not found"},status=404)
        try:
            n=min(int(self.headers.get("Content-Length","0")),4096);data=json.loads(self.rfile.read(n) or b"{}")
            task=str(data.get("task","")).strip()[:200];tasks=json.loads(TASKS.read_text(encoding="utf-8"))
            if task: tasks.append(task);TASKS.write_text(json.dumps(tasks,ensure_ascii=False,indent=2),encoding="utf-8")
            return self.reply(tasks)
        except Exception: return self.reply({"error":"Invalid request"},status=400)
    def log_message(self,fmt,*args): print(fmt%args)

if __name__=="__main__":
    print("STONIC Computer starting on port 8000")
    ThreadingHTTPServer(("0.0.0.0",8000),Handler).serve_forever()
