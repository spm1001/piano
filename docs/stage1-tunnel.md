# Stage 1 — ping on the web via a Cloudflare tunnel

How `ping` became callable from claude.ai web chat at a stable HTTPS URL, with
**one Python source** (no Worker, no TS twin) — the deliberate choice from the
build plan's iron rule.

## Architecture

```
claude.ai chat
  → Cloudflare named tunnel  (ping.planetmodha.com)
  → 127.0.0.1:8791 on hezza
  → the canonical Python FastMCP ping  (uv run ping-server, PING_TRANSPORT=http)
```

There is **no Cloudflare Worker**. The edge URL looks Worker-shaped from outside;
underneath it is the exact binary the stdio smoke runs. Transport is one runtime
switch (`PING_TRANSPORT`), so stdio (Stage 0) and HTTP (Stage 1) share a source.

## Resolved unknowns (verified 2026-05-31)

- **claude.ai accepts a NO-AUTH remote MCP connector** — no OAuth shim needed.
- **FastMCP's DNS-rebinding protection** rejects any non-localhost Host header
  with `421 Invalid Host header`. Behind a tunnel the public hostname must be
  allowlisted — `ping` reads `PING_ALLOWED_HOSTS` and sets
  `TransportSecuritySettings`.

## One-time setup (Phase B)

### 1. Login (the only interactive step — needs a browser)

```sh
cloudflared tunnel login
```

cloudflared prints a one-time URL and **polls** while it waits. Open that URL in
**any** browser signed into Cloudflare (it need not be on the same machine —
that's why this works headless on hezza), authorize the `planetmodha.com` zone,
and cloudflared writes `~/.cloudflared/cert.pem`. The browser/identity half and
the credential-landing half are bridged by the unguessable token in the URL —
same shape as `gcloud auth login --no-browser` / device-code OAuth.

### 2. Create the tunnel + route DNS

```sh
cloudflared tunnel create ping
cloudflared tunnel route dns ping ping.planetmodha.com
```

`create` writes `~/.cloudflared/<UUID>.json` — **secret; never commit it.**
`route dns` adds the CNAME `ping.planetmodha.com → <UUID>.cfargotunnel.com`.

### 3. Config

`~/.cloudflared/config.yml` (UUID is yours from step 2; not a secret):

```yaml
tunnel: <UUID>
credentials-file: /home/modha/.cloudflared/<UUID>.json
ingress:
  - hostname: ping.planetmodha.com
    service: http://127.0.0.1:8791
  - service: http_status:404
```

### 4. Services

The two units live in [`deploy/systemd/`](../deploy/systemd/). Install and start:

```sh
cp deploy/systemd/piano-*.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now piano-ping.service piano-tunnel.service
```

`piano-ping` runs the canonical ping in HTTP mode on `127.0.0.1:8791` with
`PING_ALLOWED_HOSTS=ping.planetmodha.com`. `piano-tunnel` runs cloudflared with
the config above and `Requires=piano-ping`. Lingering must be on
(`loginctl enable-linger modha`) so they survive logout — it already is on hezza.

### 5. Connector

In claude.ai → Connectors → add/edit a custom connector pointing at:

```
https://ping.planetmodha.com/mcp
```

No auth. Then `call ping` in a chat → `pong @ <timestamp> pid=<pid>`.

## Verify

```sh
# local
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8791/mcp   # 400/406 = up
# public, full MCP round trip (pid proves it hit the real process)
uv run scripts/smoke_ping_http.py        # loopback
systemctl --user status piano-ping piano-tunnel --no-pager
```

## Secrets

`~/.cloudflared/cert.pem` and `~/.cloudflared/<UUID>.json` are credentials. They
live in `$HOME`, outside this repo, and must **never** be committed.
