import json, os, sys, time, urllib.request, urllib.error
tok = json.load(open(os.path.expanduser("~/.kaggle/kaggle.json")))["key"]
user, slug = sys.argv[1], sys.argv[2]
def status():
    r = urllib.request.Request(f"https://www.kaggle.com/api/v1/kernels/status?user_name={user}&kernel_slug={slug}")
    r.add_header("Authorization","Bearer "+tok)
    return json.loads(urllib.request.urlopen(r, timeout=60).read())
deadline = time.time() + 4500
last = None
while time.time() < deadline:
    try:
        s = status(); st = s.get("status","?")
    except Exception as e:
        st = f"poll-error:{e}"; s={}
    if st != last:
        print(f"[{int(time.time())}] status={st} {s.get('failureMessage') or ''}", flush=True)
        last = st
    if st in ("complete","error","cancelAcknowledged","cancelRequested"):
        print("TERMINAL:", st, "|", s.get("failureMessage") or "(no message)", flush=True)
        break
    time.sleep(20)
else:
    print("TIMEOUT waiting for kernel", flush=True)
