import uvicorn
import sys
import webbrowser
import threading
import time


def open_browser(port):
    time.sleep(1.2)
    webbrowser.open(f"http://127.0.0.1:{port}")


if __name__ == "__main__":
    port = 8000
    print(f"================================================================")
    print(f"🚀 Launching LitAutoResearch Workbench on http://127.0.0.1:{port}")
    print(f"================================================================")

    # Launch browser automatically
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    uvicorn.run("backend.app:app", host="127.0.0.1", port=port, reload=True)
