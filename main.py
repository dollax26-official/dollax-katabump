#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  Dollax Panel  -  KataBump edition        Deploy = 2 files, free-tier ready
  (main.py + requirements.txt)
=============================================================================

  FULL DEPLOYMENT GUIDE - KATABUMP
  ================================

  WHAT YOU GET
  ------------
  The complete Dollax panel: inbounds, clients, subscriptions (4 designs),
  nodes, hosts pool, Telegram control bot, 3x-ui style Outbounds/Routing
  editors, activity logs, settings, multi-admin. This launcher installs it
  on first start and runs light enough for the KataBump free tier.

  REQUIREMENTS
  ------------
  - A KataBump server with type = Python (3.11 recommended; 3.10 / 3.12 OK).
  - Free tier is enough: 308 MB RAM / 716 MB storage.
  - Exactly two files:
        main.py            <- this launcher
        requirements.txt   <- dependencies (KataBump installs them for you)

  FILE NAMES - DO NOT CONFUSE THEM (FAQ)
  --------------------------------------
  KataBump's required files depend on the server type:
      Python server:    main.py  +  requirements.txt    <- this panel
      Node.js server:   index.js +  package.json
  This is a PYTHON panel: keep main.py + requirements.txt and NEVER rename
  requirements.txt to index.js. index.js is JavaScript - it installs nothing
  here and would break the automatic dependency install. If your server was
  created as Node.js, switch it to Python in the "Startup" tab first.

  STEP BY STEP
  ------------
  1) Create the server
       control.katabump.com -> New server -> Python 3.11 -> Create.
  2) Put the two files on it (any ONE of these):
       a) Console:            git clone https://github.com/dollax26-official/dollax-katabump.git .
       b) Web file manager:   upload main.py and requirements.txt
       c) SFTP:               copy the same two files
  3) Startup tab -> Start command:   python main.py
  4) (Optional) Environment variables -> see the table below.
  5) Press START. Console shows:
       [dollax] panel files ready (23 downloaded)     <- first boot only
       [dollax] starting on 0.0.0.0:8080
  6) Open the address from your dashboard (or your free *.kdns.fr domain).
     Log in with  dollax26 / dollax26  and CHANGE THE PASSWORD right away
     (Settings).

  ENVIRONMENT VARIABLES (all optional)
  ------------------------------------
    PORT / SERVER_PORT    Port to listen on. 8080 / 3000 / 8000 are tried
                          automatically if it is not set.
    SECRET_KEY            Session signing key. Auto-generated and saved to
                          ./dollax_data/secret_key.txt when not set.
    ADMIN_USERNAME        Owner username for the first login (default dollax26).
    ADMIN_PASSWORD        Owner password for the first login (default dollax26).
    DOLLAX_SINGLE_PORT    "1" (default on KataBump) = one listener only.
                          Set "0" to also open the :8080 safety-net port.
    DOLLAX_LOW_POWER      "1" (default) = lower CPU priority, tighter limits.
                          Set "0" on bigger paid plans.
    DOLLAX_REFETCH        "1" = re-download the panel files on next start.
    LOG_LEVEL             uvicorn log level: info | warning | error.

  WHAT RUNS WHERE
  ---------------
    ./main.py             this launcher (part of the 2-file deploy)
    ./requirements.txt    dependencies
    ./dollax_app/         panel code (auto-downloaded + cached, ~2 MB)
    ./dollax_data/        your data: database, keys, xray config

  FREE TIER NOTES (CPU / RAM - ONLY HALF A CORE NEEDED)
  -----------------------------------------------------
   - One Python process and ONE HTTP listener by default -> idle ~0-2% CPU.
   - Low-power mode is on: lower OS priority + capped concurrency.
   - The Telegram poller stays off until you set a bot token.
   - Avoid adding many panel-to-panel "nodes"; each adds a health check.
   - No Xray binary is bundled: native VLESS-WS / Trojan-WS relay works
     out of the box; WireGuard / Reality need an Xray-core on the host.

  UPDATING
  --------
   Panel files are cached under ./dollax_app and refresh automatically when a
   new launcher version arrives (or set DOLLAX_REFETCH=1 to force it).
   Offline fallback:  git clone https://github.com/dollax26-official/dollax26railwaytest.git dollax_app

  TROUBLESHOOTING
  ---------------
   - "Application failed to respond":
       check the console for [dollax] starting on 0.0.0.0:PORT, then set the
       PORT environment variable to that port (or the one in your dashboard).
   - Stuck at "panel files are missing":
       no internet on first boot -> use the git clone fallback above, restart.
   - pip errors:
       restart once; KataBump reinstalls requirements automatically.
   - Forgot the password:
       stop the server, delete ./dollax_data/dollax.db, start again (fresh
       database, default login) - or reset it from the panel settings.

  فارسی (خلاصه نصب)
  -----------------
   ۱) یک سرور پایتون بسازید (۳.۱۱).
   ۲) دو فایل main.py و requirements.txt را بریزید (یا همین ریپو را
      git clone کنید).
   ۳) در تب Startup دستور شروع را بگذارید:  python main.py
   ۴) ورود پیش‌فرض:  dollax26 / dollax26  — فوراً عوضش کنید.
   حالت کم‌مصرف برای پلن رایگان به‌صورت پیش‌فرض روشن است.
=============================================================================
"""
import os
import subprocess
import sys
import threading
import time
import urllib.request

APP_VERSION = "2026.10.04-r2"

MIRRORS = [
    "https://raw.githubusercontent.com/dollax26-official/dollax26railwaytest/main/",
    "https://cdn.jsdelivr.net/gh/dollax26-official/dollax26railwaytest@main/",
]

REQUIRED = [
    "main.py", "api_extras.py", "db.py", "pages.py", "protocol.py", "relay.py",
    "xray_core.py", "tg_bot.py",
    "static/style.css", "static/app.js", "static/app2.js",
    "static/sub-templates/xui.html", "static/sub-templates/pasarguard.html",
    "static/sub-templates/xg.html",
]

OPTIONAL = [
    "static/bg/arcade.jpg.b64.part01", "static/bg/arcade.jpg.b64.part02",
    "static/bg/minimal.jpg.b64.part01",
    "static/bg/moon.jpg.b64.part01", "static/bg/moon.jpg.b64.part02",
    "static/bg/moon.jpg.b64.part03", "static/bg/moon.jpg.b64.part04",
    "static/bg/moon.jpg.b64.part05",
    "static/lost-soul.mp3",
]

HERE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(HERE, "dollax_app")
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(HERE, "dollax_data")
STAMP = os.path.join(APP_DIR, ".version")


def log(msg):
    print("[dollax] " + str(msg), flush=True)


def download(rel, dest):
    last = "?"
    for base in MIRRORS:
        try:
            req = urllib.request.Request(base + rel,
                                         headers={"User-Agent": "dollax-launcher/" + APP_VERSION})
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = resp.read()
            folder = os.path.dirname(dest)
            if folder:
                os.makedirs(folder, exist_ok=True)
            tmp = dest + ".part"
            with open(tmp, "wb") as fh:
                fh.write(data)
            os.replace(tmp, dest)
            return True
        except Exception as exc:
            last = exc
    log("download failed: %s (%s)" % (rel, last))
    return False


def ensure_files():
    try:
        os.makedirs(APP_DIR, exist_ok=True)
    except OSError as exc:
        log("cannot create %s (%s)" % (APP_DIR, exc))
        return False
    stamp = ""
    try:
        with open(STAMP, "r", encoding="utf-8") as fh:
            stamp = fh.read().strip()
    except OSError:
        stamp = ""
    refresh = (stamp != APP_VERSION) or (os.environ.get("DOLLAX_REFETCH") == "1")
    pulled = 0
    for rel in REQUIRED + OPTIONAL:
        dest = os.path.join(APP_DIR, rel.replace("/", os.sep))
        if os.path.exists(dest) and not refresh:
            continue
        if download(rel, dest):
            pulled += 1
    if pulled:
        log("panel files ready (%d downloaded)" % pulled)
    missing = [f for f in REQUIRED if not os.path.exists(os.path.join(APP_DIR, f.replace("/", os.sep)))]
    if missing:
        log("missing required files: " + ", ".join(missing[:6]))
        return False
    if refresh:
        try:
            with open(STAMP, "w", encoding="utf-8") as fh:
                fh.write(APP_VERSION)
        except OSError:
            pass
    return True


def install_deps():
    needs = []
    for mod in ("fastapi", "uvicorn", "itsdangerous", "qrcode", "httpx", "websockets"):
        try:
            __import__(mod)
        except Exception:
            needs.append(mod)
    if not needs:
        return True
    log("installing missing packages: " + ", ".join(needs))
    base = [sys.executable, "-m", "pip", "install", "--no-cache-dir", "--disable-pip-version-check"]
    for extra in ([], ["--user"]):
        try:
            if subprocess.call(base + extra + needs) == 0:
                return True
        except Exception:
            pass
    log("pip install did not complete; will try to continue")
    return False


def secret_key():
    if os.environ.get("SECRET_KEY"):
        return
    path = os.path.join(DATA_DIR, "secret_key.txt")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            saved = fh.read().strip()
        if saved:
            os.environ["SECRET_KEY"] = saved
            return
    except OSError:
        pass
    import secrets
    value = secrets.token_urlsafe(48)
    os.environ["SECRET_KEY"] = value
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(value)
    except OSError:
        pass


def low_power_default():
    val = os.environ.get("DOLLAX_LOW_POWER")
    if val is None:
        os.environ["DOLLAX_LOW_POWER"] = "1"
        val = "1"
    on = (val == "1")
    if on:
        try:
            if hasattr(os, "nice"):
                os.nice(5)
        except Exception:
            pass
    return on


def single_listener_default():
    val = os.environ.get("DOLLAX_SINGLE_PORT")
    if val is None:
        os.environ["DOLLAX_SINGLE_PORT"] = "1"
        val = "1"
    return (val == "1")


def port_candidates():
    ports = []
    for raw in (os.environ.get("PORT"), os.environ.get("SERVER_PORT"), "8080", "3000", "8000"):
        try:
            value = int(str(raw).strip())
        except Exception:
            value = 0
        if value and 0 < value < 65536 and value not in ports:
            ports.append(value)
    return ports


def main():
    log("Dollax Panel launcher %s" % APP_VERSION)
    log("start command: python main.py  |  files -> ./dollax_app  |  data -> " + DATA_DIR)
    log("default login: dollax26 / dollax26  - change it right after first login")
    os.environ.setdefault("DATA_DIR", DATA_DIR)
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    power = low_power_default()
    single = single_listener_default()
    log("low-power mode: %s  |  single listener: %s  (free-tier ready)"
        % ("on" if power else "off", "on" if single else "off"))
    if not ensure_files():
        log("cannot start: panel files are missing and could not be downloaded.")
        log("try: git clone https://github.com/dollax26-official/dollax26railwaytest.git dollax_app")
        sys.exit(1)
    secret_key()
    install_deps()
    os.chdir(APP_DIR)
    sys.path.insert(0, APP_DIR)
    try:
        import uvicorn
        import main as panel  # noqa: F401  (validates the panel imports cleanly)
    except Exception as exc:
        log("panel failed to start: %s" % exc)
        sys.exit(1)
    ports = port_candidates()
    primary = ports[0]
    extra = 8080 if (primary != 8080 and not single) else None
    if extra:
        def extra_server():
            try:
                log("also listening on 0.0.0.0:%d (safety net)" % extra)
                uvicorn.run("main:app", host="0.0.0.0", port=extra, proxy_headers=True,
                            forwarded_allow_ips="*", limit_concurrency=100, timeout_keep_alive=15,
                            log_level=(os.environ.get("LOG_LEVEL") or "info"))
            except BaseException as exc:  # noqa: BLE001
                log("extra listener stopped: %s" % exc.__class__.__name__)
        threading.Thread(target=extra_server, daemon=True).start()
    last = None
    for port in ports:
        try:
            log("starting on 0.0.0.0:%d" % port)
            uvicorn.run("main:app", host="0.0.0.0", port=port, proxy_headers=True,
                        forwarded_allow_ips="*", limit_concurrency=100, timeout_keep_alive=15,
                        log_level=(os.environ.get("LOG_LEVEL") or "info"))
            break
        except SystemExit:
            break
        except BaseException as exc:  # noqa: BLE001
            last = exc
            log("could not serve on %d: %s" % (port, exc))
            time.sleep(1)
    else:
        log("every port failed: %s" % last)
        sys.exit(1)


if __name__ == "__main__":
    main()
