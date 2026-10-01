#!/usr/bin/env python3
from pathlib import Path
import importlib.util,json,os,subprocess,time,urllib.request
ROOT=Path.home()/"qwen38-4090"
OUT=ROOT/"results/service-verification"
OUT.mkdir(parents=True,exist_ok=True)
BASE="http://127.0.0.1:18038"
spec=importlib.util.spec_from_file_location("bench",ROOT/"benchmark_http.py")
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
records={"base_url":BASE,"context":16384,"draft_tokens":7,"gpu":3,"scope":"deployment smoke; not repeated performance or semantic correctness benchmark"}
start=time.monotonic()
while time.monotonic()-start<180:
 try:
  with urllib.request.urlopen(BASE+"/health",timeout=2) as response:
   records["health"]={"status":response.status,"body":json.load(response)}
  break
 except OSError: time.sleep(0.5)
else: raise RuntimeError("service not healthy within 180 seconds")
records["readiness_poll_s"]=time.monotonic()-start
records["systemd"]=subprocess.check_output([str(ROOT/"service_ctl.sh"),"show","-p","MainPID","-p","ActiveState","-p","SubState","-p","ExecMainStatus"],text=True)
with urllib.request.urlopen(BASE+"/v1/models",timeout=5) as response:
 records["models"]=json.load(response)
for workload,limit in [("json",512),("code",2048)]:
 body={"model":"qwen3.8-27b","messages":[{"role":"user","content":helper.CASES[workload]}],"temperature":0,"seed":42,"presence_penalty":0,"frequency_penalty":0,"enable_thinking":False,"max_tokens":limit,"stream":False}
 started=time.perf_counter(); result=helper.post(BASE+"/v1/chat/completions",body)
 content=result["choices"][0]["message"].get("content") or ""
 row={"request":body,"response":result,"wall_s":time.perf_counter()-started,"checks":helper.check_output(workload,content)}
 (OUT/(workload+".json")).write_text(json.dumps(row,indent=2))
 records[workload]={"completion_tokens":result["usage"]["completion_tokens"],"finish_reason":result["choices"][0]["finish_reason"],"checks":row["checks"]}
body={"model":"qwen3.8-27b","messages":[{"role":"user","content":"Count from one to five separated by commas."}],"temperature":0,"seed":42,"presence_penalty":0,"frequency_penalty":0,"enable_thinking":False,"max_tokens":64,"stream":True}
request=urllib.request.Request(BASE+"/v1/chat/completions",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
with urllib.request.urlopen(request,timeout=60) as response:
 stream=response.read().decode()
(OUT/"stream.sse").write_text(stream)
records["stream"]={"done": "data: [DONE]" in stream,"events":stream.count("data:"),"request":body}
for name,route,body in [("responses","/v1/responses",{"model":"qwen3.8-27b","input":"Say ready.","max_output_tokens":32,"temperature":0,"reasoning":{"effort":"none"}}),("anthropic","/v1/messages",{"model":"qwen3.8-27b","messages":[{"role":"user","content":"Say ready."}],"max_tokens":32,"temperature":0})]:
 result=helper.post(BASE+route,body)
 (OUT/(name+".json")).write_text(json.dumps({"request":body,"response":result},indent=2))
 records[name]={"response_type":result.get("type"),"status":result.get("status"),"content":result.get("content") or result.get("output")}
records["gpu_snapshot"]=helper.gpu_snapshot(3)
(OUT/"summary.json").write_text(json.dumps(records,indent=2))
print(json.dumps(records,indent=2),flush=True)
if not(records["json"]["checks"].get("valid_json") and records["json"]["checks"].get("three_districts") and records["code"]["checks"].get("python_syntax") and records["stream"]["done"]):
 raise RuntimeError("deployment smoke check failed; inspect raw evidence")
