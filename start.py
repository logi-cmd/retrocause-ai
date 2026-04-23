import subprocess
import sys
import os
import signal
import time


def main():
    print("Starting RetroCause Full-Stack Application...")
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")
    processes = []

    try:
        print("-> Starting FastAPI Backend...")
        backend_process = subprocess.Popen(
            [
                sys.executable,
                "-B",
                "-m",
                "uvicorn",
                "retrocause.api.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            cwd=root_dir,
        )
        processes.append(backend_process)

        print("-> Starting Next.js Frontend...")
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        frontend_process = subprocess.Popen(
            [npm_cmd, "run", "dev", "--", "-p", "3005"],
            cwd=frontend_dir,
            env={**os.environ, "PORT": "3005"},
        )
        processes.append(frontend_process)

        print("\n=== Application is running! ===")
        print("Frontend: http://127.0.0.1:3005")
        print("Backend:  http://localhost:8000\n")

        for p in processes:
            p.wait()

    except KeyboardInterrupt:
        print("\nShutting down processes...")
    finally:
        for p in processes:
            if p.poll() is None:
                p.terminate()
        time.sleep(1)
        for p in processes:
            if p.poll() is None:
                p.kill()
        print("Shutdown complete.")


if __name__ == "__main__":
    main()
