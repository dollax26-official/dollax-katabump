# Dollax Panel — Python Edition (FastAPI + SQLite)

A self-hosted VPN management panel for **KataBump** and any Python host: web dashboard + REST API + Telegram control bot, powered by **Xray-core** as the protocol engine.

This is a fresh, standalone package (new files) — includes the **WireGuard config inbound** support and the 3x-ui–style Outbounds / Routing JSON editors.

---

## Features

- **Inbounds**: VLESS, VMess, Trojan, Shadowsocks, **WireGuard** — with WS / gRPC / xhttp / HTTPUpgrade / TCP / RAW transports, TLS & **Reality** (auto X25519 keys + raw-TCP listeners).
- **Clients**: quota, expiry (calendar), IP/connection limits, per-client config count, edit / reset / disable from panel or bot.
- **Subscriptions**: per-inbound graphical pages (xui · aurora · pasarguard · xg templates), base64 & raw outputs, `Subscription-Userinfo` headers, per-client token links, and a `SUB INFO` summary entry.
- **Nodes**: panel-to-panel remote inbounds, auto health loop.
- **Hosts pool**: clean-IP rotation for links.
- **Outbounds & Routing**: 3x-ui–style JSON editors with presets, validation, and live apply (core restarts on save).
- **Telegram bot**: button-first control surface (owner menus; non-owner gets exactly "Get config" + "My profile"), trial provisioning, full client edit/delete, per-user language (FA/EN).
- **Multi-admin**: per-admin section/inbound access lists, per-admin prefs, activity log with admin IPs.
- **Appearance**: 7 themes, glass/solid styles, fonts, background presets, per-admin music.

## Quick start (KataBump / any Python host)

```bash
# 1) install dependencies
pip install -r requirements.txt

# 2) set the environment (see .env.example)
export SECRET_KEY="change-me-please"     # required for session signing
export PORT=8080                          # your host may inject this automatically
export DATA_DIR=./data                    # SQLite + generated configs live here

# 3) run
python main.py
```

Open `http://localhost:8080` — the owner account is seeded on first boot
(default `dollax26` / `dollax26` — change it immediately, see below).

Change the owner password:

```bash
python set_password.py newpassword
```

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `8080` | HTTP port (most hosts inject this) |
| `SECRET_KEY` | random per boot | session-signing key — set it to keep sessions across restarts |
| `DATA_DIR` | `./data` | database + xray config location |
| `XRAY_MODE` | `auto` | `auto` uses the bundled/known xray-core; `off` runs panel-only |
| `DOLLAX_SINGLE_PORT` | off | run exactly one listener on `$PORT` |

> The app listens on `$PORT` **and** on `:8080` by default (safety net for hosts that route to a fixed target port).

## WireGuard inbound

Create an inbound with protocol **wireguard** in the builder — keys are generated for you
(private key + public key). The core listens on a raw UDP/TCP port; clients get a standard
WireGuard config. Sample config and step-by-step notes: see [WIREGUARD.md](WIREGUARD.md).

## Telegram bot

1. Create a bot with @BotFather → copy the token.
2. In the panel → Settings → Bot: set **Token** and your numeric **Owner ID**.
3. Press **Start** (or `/start` in Telegram). One poller per panel — the bot holds a lock file so a second replica stays quiet.

## Project structure

| File | Role |
|---|---|
| `main.py` | FastAPI app, auth, settings, Xray supervision |
| `api_extras.py` | API surface: nodes, hosts, subscriptions, bot config, JSON editors |
| `db.py` | SQLite layer (WAL) + schema/migrations |
| `protocol.py` | Link/config builders, Reality/WG key tools |
| `xray_core.py` | Xray config generation + process control |
| `tg_bot.py` | Telegram control bot |
| `pages.py` | HTML pages + subscription templates |
| `relay.py` | native WS relay (VLESS-WS / Trojan-WS) |
| `static/` | panel UI (app.js, app2.js, style.css, sub-templates/) |
| `set_password.py` | owner password reset helper |

## Security notes

- Change the default owner password before exposing the panel.
- Reality needs a **raw TCP** endpoint: use a TCP proxy / second port and set `reality_host` + `reality_public_port` in Settings → Xray-core.
- Only VLESS-WS and Trojan-WS are relayed natively; everything else uses the bundled Xray-core (bridge to `127.0.0.1:10000+i`).
