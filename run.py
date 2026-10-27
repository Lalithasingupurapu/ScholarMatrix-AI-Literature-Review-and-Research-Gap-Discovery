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
    webbrowser.open(f"http://127.0.0.1:{port}")


if __name__ == "__main__":
    port = 8000
    print("================================================================")
    print(f">> Launching ScholarMatrix AI Workbench on http://127.0.0.1:{port}")
    print("================================================================")

    # Launch browser automatically
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    uvicorn.run("backend.app:app", host="127.0.0.1", port=port, reload=True)
