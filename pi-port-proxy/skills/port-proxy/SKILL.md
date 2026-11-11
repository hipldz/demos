---
name: port-proxy
description: Access local web development servers through the pi-port-proxy extension. Use when a user asks to open, preview, or access a localhost service such as Vite, Jupyter, Pi Web, or another server listening on a TCP port.
compatibility: Linux, WSL2, or Termux with the pi-port-proxy extension installed; Termux URL opening additionally requires termux-api.
---

# Port Proxy

Use the `port_proxy` tool instead of guessing ports.

1. Call `port_proxy` with `action: "list"` when the target port is unknown.
2. Call `port_proxy` with `action: "url"` and the selected port to create the local proxy URL.
3. On Termux, set `open: true` only when the user wants the Android browser opened.
4. Do not expose the proxy beyond loopback unless the user has explicitly configured an allow-list.

Subpath proxying can fail for applications that hard-code absolute root URLs such as `/api` or `/ws`. If the page loads but assets/API/WebSocket calls fail, report that as a base-path compatibility issue rather than repeatedly restarting the server.
