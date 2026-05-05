import socket
import subprocess
import sys
import time
import webbrowser


APP_HOST = "0.0.0.0"
APP_PORT = 8000
APP_MODULE = "app.main:app"


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


def print_header(local_ip):
    print()
    print("==============================================")
    print(" Zero2Print PrintManager")
    print("==============================================")
    print()
    print("PC:")
    print(f"  http://localhost:{APP_PORT}")
    print()
    print("Handy / Heimnetz:")
    print(f"  http://{local_ip}:{APP_PORT}")
    print()
    print("Beenden:")
    print("  CTRL + C")
    print()
    print("==============================================")
    print()


def open_browser(local_ip):
    url = f"http://{local_ip}:{APP_PORT}"

    try:
        time.sleep(1.5)
        webbrowser.open(url)
    except Exception:
        pass


def run_server():
    local_ip = get_local_ip()
    print_header(local_ip)

    open_browser(local_ip)

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        APP_MODULE,
        "--host",
        APP_HOST,
        "--port",
        str(APP_PORT),
    ]

    subprocess.run(command)


if __name__ == "__main__":
    run_server()