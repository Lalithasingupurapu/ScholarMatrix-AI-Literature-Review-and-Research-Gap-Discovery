import os
import sys
import time
import threading
import webbrowser
import uvicorn

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def open_browser(port):
    time.sleep(1.2)
    try:
        webbrowser.open(f"http://127.0.0.1:{port}")
    except Exception:
        pass


if __name__ == "__main__":
    is_cloud = bool(os.environ.get("RENDER") or os.environ.get("PORT"))
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0" if is_cloud else "127.0.0.1"

    print("================================================================")
    print(f">> Launching ScholarMatrix AI Workbench on http://{host}:{port}")
    print("================================================================")

    if not is_cloud:
        # Launch browser automatically on local desktop
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    uvicorn.run("backend.app:app", host=host, port=port, reload=not is_cloud)
