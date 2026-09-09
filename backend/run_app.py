"""
Launcher script inside backend/ folder.
Launches FastAPI backend server and Vite frontend server simultaneously.
"""

import subprocess
import sys
import time
import os

def main():
    backend_dir = os.path.abspath(os.path.dirname(__file__))
    base_dir = os.path.abspath(os.path.join(backend_dir, ".."))
    
    print("=" * 70)
    print(" 🛸 AUTONOMOUS DISASTER-RESPONSE DRONE — 20% SOFTWARE PROTOTYPE")
    print(" Pipeline: Detect -> Locate -> Assess -> Prioritize -> Visualize")
    print("=" * 70)

    # 1. Start FastAPI Backend
    print("[Launcher] Starting FastAPI backend on http://localhost:8000...")
    backend_env = os.environ.copy()
    backend_env["PYTHONPATH"] = base_dir

    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=base_dir,
        env=backend_env
    )

    time.sleep(2)

    # 2. Start Vite Frontend
    frontend_dir = os.path.join(base_dir, "frontend")
    print(f"[Launcher] Starting Vite React Command Center on http://localhost:3000...")
    
    frontend_proc = subprocess.Popen(
        ["npx.cmd" if sys.platform == "win32" else "npx", "vite", "--port", "3000"],
        cwd=frontend_dir
    )

    print("\n[Launcher] Both services are running!")
    print("  • Command Center Dashboard: http://localhost:3000")
    print("  • FastAPI Swagger Docs:     http://localhost:8000/docs")
    print("  • WebSocket Endpoint:        ws://localhost:8000/ws/live\n")

    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\n[Launcher] Shutting down services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
