# WireGuard inbound (like the NeoTeNet panel)

The panel can run a **WireGuard** inbound through Xray-core, exactly like the NeoTeNet
build: the server keeps a private key, clients get a standard `wg` config, and the core
listens on a raw **UDP/TCP** port (it cannot pass the public HTTPS proxy).

## Create it in the panel

1. **Inbounds -> New inbound**
2. Protocol: `wireguard`
3. Press **🔑 Generate keys** - the server private/public key pair and a short config id are filled in.
4. Save. The core gets a new listener on its own port (`base + 1000 + index`).

## What Xray runs (server side)

```json
{
  "tag": "WG-1",
  "protocol": "wireguard",
  "listen": "0.0.0.0",
  "port": 51820,
  "settings": {
    "secretKey": "<server private key>",
    "address": ["10.66.66.1/24"],
    "peers": [
      { "publicKey": "<client public key>", "allowedIPs": ["10.66.66.2/32"] }
    ],
    "mtu": 1420
  }
}
```

## What the client imports (.conf)

```ini
[Interface]
PrivateKey = <client private key>
Address = 10.66.66.2/32
DNS = 1.1.1.1

[Peer]
PublicKey = <server public key>
Endpoint = your-host.example.com:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
```

## Notes

- Open the WireGuard port (UDP) on your host / TCP proxy - it is raw traffic, not HTTP.
- Keys are generated with the same tooling as Reality (`/api/keys/wg`), so you can rotate the server pair any time.
- Client configs are delivered through the normal subscription flow alongside the other protocols.
