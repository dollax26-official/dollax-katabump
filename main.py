#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  Dollax Panel  -  KataBump edition  (deploy = 2 files: main.py + requirements.txt)
=============================================================================

  HOW TO DEPLOY ON KATABUMP            (control.katabump.com)
  ----------------------------------------------------------
  1) Create a server:  type = Python  (3.11 recommended; free plan works).
  2) Upload these 2 files (Web file manager, SFTP, or connect this GitHub repo):
        main.py            <- this launcher
        requirements.txt   <- dependencies (KataBump installs them automatically)
  3) Startup tab -> start command:      python main.py
  4) Open your server URL / free *.kdns.fr domain and log in.
     Default owner:  dollax26 / dollax26   <- change it right after login.
  5) Optional environment variables:
        PORT / SERVER_PORT    port to listen on (auto-detected: 8080/3000/8000 too)
        SECRET_KEY            keeps sessions across restarts (auto-saved if unset)
        ADMIN_USERNAME / ADMIN_PASSWORD
                              custom first-login owner account
        DOLLAX_SINGLE_PORT=1  one listener only (low-memory mode)
        DOLLAX_REFETCH=1      re-download the panel files on next start

  WHAT THIS FILE DOES
  -------------------
  On first start it downloads the panel source (~23 small files) from the
  official repo and caches it in ./dollax_app, then boots the panel.
  Panel data (database, keys) lives in ./dollax_data.

  Offline fallback: from the KataBump console run
      git clone https://github.com/dollax26-official/dollax26railwaytest.git dollax_app
  and start again.
=============================================================================
"""
import os
import subprocess
import sys
import threading
import time
import urllib.request

APP_VERSION = "2026.10.02-r1"

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
    extra = 8080 if (primary != 8080 and os.environ.get("DOLLAX_SINGLE_PORT") != "1") else None
    if extra:
        def extra_server():
            try:
                log("also listening on 0.0.0.0:%d (safety net)" % extra)
                uvicorn.run("main:app", host="0.0.0.0", port=extra, proxy_headers=True,
                            forwarded_allow_ips="*",
                            log_level=(os.environ.get("LOG_LEVEL") or "info"))
            except BaseException as exc:  # noqa: BLE001
                log("extra listener stopped: %s" % exc.__class__.__name__)
        threading.Thread(target=extra_server, daemon=True).start()
    last = None
    for port in ports:
        try:
            log("starting on 0.0.0.0:%d" % port)
            uvicorn.run("main:app", host="0.0.0.0", port=port, proxy_headers=True,
                        forwarded_allow_ips="*",
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
