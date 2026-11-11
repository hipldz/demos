# pi-port-proxy

[返回项目索引](../README.md)

A small localhost reverse proxy and Pi extension for WSL2, Linux, and Termux.

## Proxy behavior

- Ports are **not** auto-managed just because they are listening.
- Add a proxy explicitly from the dashboard, `/proxy <port>`, or the `port_proxy` tool.
- The dashboard only shows explicitly managed proxies.
- `/ports discover` and `GET /api/discover` are discovery-only and do not change state.
- Preferred URL form is host-based: `http://p5173.localhost:8787/`.
  - This preserves root-relative URLs (`/_next/*`, `/api/*`, `/ws`, etc.).
  - It is much more compatible with Next.js/Vite/WebSocket apps than a subpath proxy.
- Compatibility path mode remains available at `http://127.0.0.1:8787/proxy/5173/`.

Managed proxies are currently kept in memory for the lifetime of the proxy process. Persistence can be added later once the behavior is stable.

## Run standalone

```bash
npm install
npm run typecheck
npm run dev
```

Dashboard:

```text
http://127.0.0.1:8787/
```

## Pi extension development

```bash
pi -e ./src/extension.ts
```

Commands:

```text
/ports
/ports discover
/proxy 5173
/unproxy 5173
```

## Dashboard UI

The lightweight built-in dashboard includes a Pi Port Proxy icon/favicon, hover tooltips, and English/Chinese UI switching. English is the default language on first load; the browser remembers an explicit language choice locally.
