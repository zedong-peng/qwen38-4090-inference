#!/usr/bin/env python3
import json, os, socket, subprocess, sys, time, urllib.request
from pathlib import Path
ROOT=Path.home()/"qwen38-4090"
OUT=ROOT/"results/http-bench-matched"
OUT.mkdir(parents=True,exist_ok=True)
PORT=18039
URL="http://127.0.0.1:"+str(PORT)
ENV=dict(os.environ,CUDA_VISIBLE_DEVICES="3",LD_LIBRARY_PATH=str(ROOT/"tools/build-env/lib"))
EVENTS=[]
for k in [0,3,7]:
    try:
        with socket.create_connection(("127.0.0.1",PORT),timeout=1):
            raise RuntimeError("Refusing active pre-existing server on benchmark port")
    except ConnectionRefusedError:
        pass
    label="llama-udq4-k"+str(k)
    cmd=[str(ROOT/"repos/native-llama/llama.cpp/build-sm89/bin/llama-server"),"-m",str(ROOT/"models/Qwen3.8-27B-UD-Q4_K_M.gguf"),"-ngl","all","-fa","on","-c","4096","-np","1","--fit","off","--no-cache-prompt","--reasoning","off","--alias","qwen3.8-27b","--host","127.0.0.1","--port",str(PORT)]
    if k:
        cmd += ["-md",str(ROOT/"models/mtp-Qwen3.8-27B-Q4_0.gguf"),"--spec-type","draft-mtp","--spec-draft-n-max",str(k),"-ngld","all"]
    event={"label":label,"command":cmd,"visible_gpu":3}
    logpath=OUT/(label+".server.log")
    with logpath.open("w") as log:
        proc=subprocess.Popen(cmd,stdout=log,stderr=log,env=ENV)
        try:
            start=time.monotonic(); ready=False
            while proc.poll() is None and time.monotonic()-start<180:
                try:
                    with urllib.request.urlopen(URL+"/health",timeout=2) as response:
                        ready=response.status==200
                    text=logpath.read_text(errors="replace")
                    ready=ready and proc.poll() is None and ("listening on "+URL) in text
                    if ready: break
                except OSError: pass
                time.sleep(0.5)
            event.update(startup_s=time.monotonic()-start,ready=ready)
            if ready:
                event["benchmark_exit_code"]=subprocess.run([sys.executable,str(ROOT/"benchmark_http.py"),"--base-url",URL,"--label",label,"--engine","llama","--out",str(OUT),"--reps","3"],env=ENV).returncode
            else:
                event["startup_exit_code"]=proc.poll()
                print(label+": startup failed "+str(logpath),flush=True)
        except BaseException as error:
            event["error"]=repr(error); raise
        finally:
            if proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    proc.kill(); proc.wait(timeout=10)
            event["server_exit_code"]=proc.poll()
            EVENTS.append(event)
            (OUT/"llama-udq4.runs.json").write_text(json.dumps(EVENTS,indent=2))
