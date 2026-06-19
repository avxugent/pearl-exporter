# CLAUDE.md

Prometheus exporter for Epiphan Pearl Mini devices. Sanic app queries the Pearl
HTTP API and exposes metrics on `/probe`.

## Layout

- `pearl_exporter.py` — Sanic app. `/probe?target=<url>` builds a Prometheus
  registry and returns metrics. Resolves device credentials, then calls `prober`.
- `prober.py` — Pearl API client. `do_request` uses HTTP Basic Auth; `verify=False`
  for the device's self-signed cert.
- `bao.py` — OpenBao credential lookup.

## Run

```bash
pip install -r requirements.txt
sanic pearl_exporter:app --port=8000 --host=0.0.0.0
# or: docker build -t pearl-exporter . && docker run -p 8000:8000 pearl-exporter
```

Probe: `curl "http://localhost:8000/probe?target=http://pearl.local"`

## Credentials (OpenBao)

`/probe` looks up each device's `username`/`password` in OpenBao (Vault-compatible,
KV v2) keyed by the hostname parsed from `target`. URL `user`/`password` params are a
**fallback** when the OpenBao lookup returns nothing.

Secret layout — hostname is the final path segment under a common prefix:

```bash
bao kv put secret/pearl-mini/pearl.local username=admin password=secret
```

Read path: `<BAO_KV_MOUNT>/data/<BAO_PATH_PREFIX>/<hostname>`.

### Env config (`bao.py`)

`BAO_*` take precedence; `VAULT_*` accepted as fallbacks so Nomad's native
integration vars work directly.

| Variable | Default | Description |
|----------|---------|-------------|
| `BAO_ADDR` / `VAULT_ADDR` | — | OpenBao address |
| `BAO_TOKEN` / `VAULT_TOKEN` | — | Auth token (Nomad renders it into the task env) |
| `BAO_KV_MOUNT` | `secret` | KV v2 mount point |
| `BAO_PATH_PREFIX` | (empty) | Common path under the mount before the hostname |
| `BAO_CACERT` / `VAULT_CACERT` | — | Optional CA bundle for TLS verify |

`get_credentials(hostname)` returns `(username, password)` or `None` on any failure
(missing config/token, secret not found, network) — never logs secret values.

## Notes

- Never log credentials. The probe handler logs only hostname + credential source
  (`openbao` / `url-param`).
- Deployed on Nomad; the `vault`/`template` stanza injects `VAULT_TOKEN`.
