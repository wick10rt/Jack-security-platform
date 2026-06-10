#!/usr/bin/env python3
"""一鍵啟動 Jack Security Platform（開發 / 展示模式）。

用法：
  python run.py              # 啟動所有服務（需先 setup 過）
  python run.py --setup      # 首次：起 infra、建 venv、裝依賴、migrate，然後啟動
  python run.py --no-frontend  # 不起前端 dev server（只跑後端 + Celery + infra）
  python run.py --dry-run    # 只做檢查並印出將執行的指令，不真的啟動
  python run.py --stop       # 關掉 infra（Postgres/Redis）容器後結束

會啟動：Postgres/Redis（docker，背景）＋ Django runserver ＋ Celery worker ＋
Celery beat ＋ 前端 Vite dev server。Ctrl+C 一次收掉所有前景子程序（infra 留背景）。

跨平台：自動偵測 venv 的 python、Windows 上 Celery 自動加 -P solo、npm 走 cmd /c。
純標準庫，無第三方相依。正式部署請改用 deploy/SETUP.md 的 gunicorn + nginx + systemd。
"""
import argparse
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
VENV = BACKEND / "venv"
IS_WINDOWS = os.name == "nt"

# 對應根目錄 docker-compose.yml 的 host 綁定（皆 127.0.0.1）
DB_PORT = 25000
REDIS_PORT = 6379


def log(msg):
    print(f"[run] {msg}", flush=True)


def die(msg):
    print(f"[run] 錯誤：{msg}", file=sys.stderr, flush=True)
    sys.exit(1)


def venv_python():
    return VENV / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")


def npm_command(args_list):
    # Windows 的 npm 是 npm.cmd，需經 cmd /c；POSIX 直接呼叫
    if IS_WINDOWS:
        return ["cmd", "/c", "npm", *args_list]
    return ["npm", *args_list]


def find_docker_compose():
    for cmd in (["docker", "compose"], ["docker-compose"]):
        try:
            r = subprocess.run(
                [*cmd, "version"], capture_output=True, text=True
            )
            if r.returncode == 0:
                return cmd
        except FileNotFoundError:
            continue
    return None


def wait_for_port(host, port, timeout=90):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            time.sleep(1)
    return False


def require_env_file():
    if not (ROOT / ".env").exists():
        die(
            "找不到根目錄 .env（後端與 infra 都需要）。\n"
            "       先複製範本：cp .env.example .env，填入 SECRET_KEY / "
            "DATABASE_PASSWORD 後再跑。"
        )


def do_setup(compose):
    require_env_file()

    log("啟動 Postgres/Redis（docker）...")
    subprocess.run([*compose, "up", "-d"], cwd=ROOT, check=True)

    if not venv_python().exists():
        log("建立 venv ...")
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)

    log("安裝後端依賴（pip）...")
    subprocess.run(
        [str(venv_python()), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")],
        check=True,
    )

    if not shutil.which("npm"):
        die("找不到 npm，請先安裝 Node.js（20+）。")
    log("安裝前端依賴（npm install）...")
    subprocess.run(npm_command(["install"]), cwd=FRONTEND, check=True)

    log("等待資料庫就緒 ...")
    if not wait_for_port("127.0.0.1", DB_PORT):
        die(f"資料庫（127.0.0.1:{DB_PORT}）未就緒，無法 migrate。")
    log("套用資料庫遷移（migrate）...")
    subprocess.run([str(venv_python()), "manage.py", "migrate"], cwd=BACKEND, check=True)

    log("首次設定完成。")
    log("提醒：要進管理後台（F5）請建管理員：")
    log(f"      cd backend && {venv_python()} manage.py createsuperuser")


def preflight(args):
    require_env_file()
    if not venv_python().exists():
        die("尚未建立 venv —— 第一次請跑：python run.py --setup")
    if not args.no_frontend and not (FRONTEND / "node_modules").exists():
        die("前端尚未安裝依賴 —— 跑 python run.py --setup，或加 --no-frontend")
    if not args.no_frontend and not (FRONTEND / ".env").exists():
        log("提醒：frontend/.env 不存在，前端可能連不到後端（需設 VITE_API_BASE_URL）。")


def build_service_commands(args):
    py = str(venv_python())
    services = [
        ("backend", [py, "manage.py", "runserver"], BACKEND),
    ]
    worker = [py, "-m", "celery", "-A", "myproject", "worker", "-l", "info"]
    if IS_WINDOWS:
        worker += ["-P", "solo"]  # Windows 的 prefork 不可用
    services.append(("celery-worker", worker, BACKEND))
    services.append(
        ("celery-beat", [py, "-m", "celery", "-A", "myproject", "beat", "-l", "info"], BACKEND)
    )
    if not args.no_frontend:
        services.append(("frontend", npm_command(["run", "dev"]), FRONTEND))
    return services


def spawn(name, cmd, cwd):
    log(f"啟動 {name}")
    kwargs = {}
    if IS_WINDOWS:
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(cmd, cwd=str(cwd), **kwargs)


def stop_all(procs):
    for name, p in procs:
        if p.poll() is not None:
            continue
        try:
            if IS_WINDOWS:
                p.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except Exception:
            pass

    deadline = time.time() + 10
    for name, p in procs:
        try:
            p.wait(timeout=max(0.0, deadline - time.time()))
        except Exception:
            try:
                if IS_WINDOWS:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(p.pid)],
                        capture_output=True,
                    )
                else:
                    os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            except Exception:
                pass


def start(args, compose):
    preflight(args)
    services = build_service_commands(args)

    if args.dry_run:
        log("--dry-run：以下指令將被執行（不實際啟動）")
        print(f"  infra : {' '.join(compose)} up -d   (cwd={ROOT})")
        for name, cmd, cwd in services:
            print(f"  {name:13}: {' '.join(cmd)}   (cwd={cwd})")
        return

    log("啟動 Postgres/Redis（docker）...")
    subprocess.run([*compose, "up", "-d"], cwd=ROOT, check=True)
    if not wait_for_port("127.0.0.1", DB_PORT):
        die(f"資料庫（127.0.0.1:{DB_PORT}）未就緒。")
    if not wait_for_port("127.0.0.1", REDIS_PORT):
        die(f"Redis（127.0.0.1:{REDIS_PORT}）未就緒，Celery 會連不上。")

    procs = []
    for name, cmd, cwd in services:
        procs.append((name, spawn(name, cmd, cwd)))

    log("—" * 30)
    log("全部啟動。前端 http://localhost:5173  後端 http://127.0.0.1:8000")
    log("Ctrl+C 結束所有服務（Postgres/Redis 會留在背景）。")

    try:
        while True:
            for name, p in procs:
                if p.poll() is not None:
                    log(f"{name} 結束（code {p.returncode}），收掉其餘服務")
                    raise KeyboardInterrupt
            time.sleep(1)
    except KeyboardInterrupt:
        log("正在收掉所有服務 ...")
        stop_all(procs)
        log("已結束。infra 仍在背景，需要時用 `python run.py --stop` 或 `docker compose down` 關閉。")


def main():
    parser = argparse.ArgumentParser(
        description="一鍵啟動 Jack Security Platform（開發/展示模式）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--setup", action="store_true", help="首次設定（venv/依賴/migrate）後再啟動")
    parser.add_argument("--no-frontend", action="store_true", help="不啟動前端 dev server")
    parser.add_argument("--dry-run", action="store_true", help="只檢查並印出指令，不啟動")
    parser.add_argument("--stop", action="store_true", help="關閉 infra（Postgres/Redis）後結束")
    args = parser.parse_args()

    compose = find_docker_compose()
    if compose is None:
        die("找不到 docker compose / docker-compose，請先安裝 Docker。")

    if args.stop:
        log("關閉 Postgres/Redis ...")
        subprocess.run([*compose, "down"], cwd=ROOT)
        return

    if args.setup:
        do_setup(compose)

    start(args, compose)


if __name__ == "__main__":
    main()
