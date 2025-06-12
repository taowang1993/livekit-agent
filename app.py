import threading
import subprocess
import time
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
import uvicorn
import logging
import os

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def index():
    # Serve the static index.html
    with open(os.path.join(os.path.dirname(__file__), "index.html"), encoding="utf-8") as f:
        return Response(content=f.read(), media_type="text/html")

def run_agent_subprocess():
    logging.basicConfig(level=logging.INFO)
    while True:
        logging.info("Starting agent subprocess...")
        proc = subprocess.Popen(["python", "agent.py", "start"])
        proc.wait()
        logging.error(f"Agent subprocess exited with code {proc.returncode}. Restarting in 5 seconds...")
        time.sleep(5)  # Prevent rapid restart loop

if __name__ == "__main__":
    # Start the agent subprocess in a daemon thread
    agent_thread = threading.Thread(target=run_agent_subprocess, daemon=True)
    agent_thread.start()
    # Block main thread with FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=7860)
