import http, { type IncomingHttpHeaders, type IncomingMessage, type ServerResponse } from "node:http";
import type { AddressInfo } from "node:net";
import type { Duplex } from "node:stream";
import { discoverListeningPorts, isListening, type ListeningPort } from "./ports.js";

export interface ProxyServerOptions {
  host?: string;
  port?: number;
  allowedPorts?: number[];
  initialPorts?: number[];
}

export interface ManagedProxy {
  port: number;
  listening: boolean;
  listener?: ListeningPort;
}

export interface ProxyServerHandle {
  host: string;
  port: number;
  baseUrl: string;
  close(): Promise<void>;
  discoverPorts(): Promise<ListeningPort[]>;
  listManagedPorts(): Promise<ManagedProxy[]>;
  registerPort(port: number): Promise<ManagedProxy>;
  unregisterPort(port: number): boolean;
  isManaged(port: number): boolean;
  proxyUrl(port: number): string;
  pathProxyUrl(port: number): string;
}

const DEFAULT_HOST = "127.0.0.1";
const DEFAULT_PORT = 8787;

function isLoopbackHost(host: string): boolean {
  return host === "127.0.0.1" || host === "localhost" || host === "::1";
}

function parseProxyPath(url: string | undefined): { port: number; path: string } | null {
  const parsed = new URL(url ?? "/", "http://localhost");
  const match = parsed.pathname.match(/^\/proxy\/(\d+)(\/.*)?$/);
  if (!match) return null;

  const port = Number(match[1]);
  if (!Number.isInteger(port) || port < 1 || port > 65535) return null;

  return {
    port,
    path: `${match[2] ?? "/"}${parsed.search}`,
  };
}

function parseHostProxyPort(hostHeader: string | undefined): number | null {
  if (!hostHeader) return null;
  const hostname = hostHeader.replace(/:\d+$/, "");
  const match = hostname.match(/^p(\d+)\.localhost$/i);
  if (!match) return null;

  const port = Number(match[1]);
  return Number.isInteger(port) && port >= 1 && port <= 65535 ? port : null;
}

function htmlEscape(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderDashboard(proxies: ManagedProxy[], proxyPort: number): string {
  const rows = proxies
    .filter((item) => item.port !== proxyPort)
    .map((item) => {
      const proc = item.listener?.process ? htmlEscape(item.listener.process) : "unknown";
      const pid = item.listener?.pid ? ` <span class="muted">pid ${item.listener.pid}</span>` : "";
      const bind = item.listener?.host ? `<code>${htmlEscape(item.listener.host)}</code>` : '<span class="muted" data-i18n="offline">offline</span>';
      const status = item.listening
        ? '<span class="status ok"><span class="status-dot"></span><span data-i18n="listening">listening</span></span>'
        : '<span class="status bad"><span class="status-dot"></span><span data-i18n="offline">offline</span></span>';
      const hostUrl = `http://p${item.port}.localhost:${proxyPort}/`;
      return `<tr>
        <td><code>${item.port}</code></td>
        <td>${proc}${pid}</td>
        <td>${bind}</td>
        <td>${status}</td>
        <td class="actions">
          <a class="button has-tooltip" href="${hostUrl}" data-i18n="open" data-tooltip-key="openTip">Open</a>
          <a class="button secondary has-tooltip" href="/proxy/${item.port}/" data-i18n="pathMode" data-tooltip-key="pathTip">Path mode</a>
          <form method="post" action="/api/proxies/${item.port}/remove">
            <button class="button secondary danger has-tooltip" type="submit" data-i18n="remove" data-tooltip-key="removeTip">Remove</button>
          </form>
        </td>
      </tr>`;
    })
    .join("\n");

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <meta name="color-scheme" content="light dark" />
  <title>Pi Port Proxy</title>
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect x='7' y='7' width='50' height='50' rx='14' fill='none' stroke='%23666' stroke-width='5'/%3E%3Cpath d='M20 22h14c8 0 12 4 12 10s-4 10-12 10H27v8h-7V22Zm7 7v6h7c3 0 5-1 5-3s-2-3-5-3h-7Z' fill='%23666'/%3E%3C/svg%3E" />
  <style>
    :root {
      color-scheme: light dark;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      --line: color-mix(in srgb, currentColor 16%, transparent);
      --line-strong: color-mix(in srgb, currentColor 30%, transparent);
      --surface: color-mix(in srgb, currentColor 5%, transparent);
      --surface-hover: color-mix(in srgb, currentColor 10%, transparent);
      --shadow: 0 10px 30px color-mix(in srgb, black 12%, transparent);
    }
    * { box-sizing: border-box; }
    body { max-width: 1080px; margin: 0 auto; padding: 28px 18px 48px; }
    .topbar { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; }
    .brand { display: flex; gap: 13px; align-items: center; }
    .logo {
      width: 44px; height: 44px; flex: 0 0 auto; display: grid; place-items: center;
      border: 1px solid var(--line-strong); border-radius: 13px; background: var(--surface); box-shadow: var(--shadow);
    }
    .logo svg { width: 27px; height: 27px; }
    h1 { margin: 0 0 4px; font-size: clamp(1.55rem, 4vw, 2rem); letter-spacing: -.025em; }
    .subtitle { margin: 0; opacity: .66; font-size: .92rem; }
    .language-switch { display: inline-flex; padding: 3px; gap: 2px; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }
    .language-switch button {
      border: 0; border-radius: 7px; padding: 6px 9px; color: inherit; background: transparent; cursor: pointer; font: inherit; font-size: .82rem; opacity: .58;
    }
    .language-switch button:hover { opacity: 1; background: var(--surface-hover); }
    .language-switch button.active { opacity: 1; background: var(--surface-hover); font-weight: 600; }
    .intro { margin: 22px 0 0; opacity: .76; line-height: 1.6; max-width: 820px; }
    .panel { margin-top: 22px; border: 1px solid var(--line); border-radius: 14px; padding: 16px; background: var(--surface); }
    .add { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin: 0; }
    .add label { font-weight: 600; margin-right: 2px; }
    .add input { padding: 8px 10px; border: 1px solid var(--line-strong); border-radius: 8px; background: transparent; color: inherit; font: inherit; width: 9em; outline: none; }
    .add input:focus { border-color: currentColor; box-shadow: 0 0 0 2px color-mix(in srgb, currentColor 12%, transparent); }
    .table-wrap { width: 100%; overflow-x: auto; margin-top: 24px; }
    table { width: 100%; border-collapse: collapse; min-width: 680px; }
    th, td { text-align: left; padding: 12px 10px; border-bottom: 1px solid var(--line); vertical-align: middle; }
    th { font-size: .8rem; text-transform: uppercase; letter-spacing: .05em; opacity: .55; }
    tbody tr:hover { background: color-mix(in srgb, currentColor 3%, transparent); }
    .button { display: inline-block; position: relative; padding: 7px 12px; border: 1px solid var(--line-strong); border-radius: 8px; text-decoration: none; background: transparent; color: inherit; cursor: pointer; font: inherit; white-space: nowrap; transition: transform .12s ease, background .12s ease, border-color .12s ease, opacity .12s ease; }
    .button:hover, .button:focus-visible { background: var(--surface-hover); border-color: currentColor; transform: translateY(-1px); opacity: 1; }
    .button:active { transform: translateY(0); }
    .secondary { opacity: .72; }
    .danger:hover, .danger:focus-visible { opacity: 1; }
    .muted { opacity: .55; font-size: .9em; }
    .status { display: inline-flex; align-items: center; gap: 7px; }
    .status-dot { width: 7px; height: 7px; border-radius: 999px; background: currentColor; opacity: .72; }
    .ok { opacity: .82; }
    .bad { opacity: .5; }
    .actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .actions form { margin: 0; }
    code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
    .empty { padding: 26px 10px; text-align: center; opacity: .62; }

    .has-tooltip::after {
      content: attr(data-tooltip);
      pointer-events: none;
      position: absolute;
      z-index: 20;
      left: 50%;
      bottom: calc(100% + 8px);
      transform: translate(-50%, 4px);
      width: max-content;
      max-width: 260px;
      padding: 6px 8px;
      border-radius: 7px;
      background: CanvasText;
      color: Canvas;
      font-size: 12px;
      line-height: 1.35;
      font-weight: 400;
      white-space: normal;
      opacity: 0;
      visibility: hidden;
      transition: opacity .12s ease, transform .12s ease, visibility .12s ease;
      box-shadow: var(--shadow);
    }
    .has-tooltip:hover::after, .has-tooltip:focus-visible::after { opacity: .94; visibility: visible; transform: translate(-50%, 0); }

    @media (max-width: 620px) {
      body { padding-top: 20px; }
      .topbar { align-items: center; }
      .logo { width: 40px; height: 40px; border-radius: 12px; }
      .intro { margin-top: 18px; }
      .panel { padding: 13px; }
      .add label { width: 100%; }
    }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="brand">
      <div class="logo" aria-hidden="true">
        <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="8" y="8" width="48" height="48" rx="14" stroke="currentColor" stroke-width="4" opacity=".65" />
          <path d="M20 21h14c8.5 0 13 4.1 13 10.8 0 6.8-4.5 10.8-13 10.8h-6.8V51H20V21Zm7.2 7.2v7.4h6.5c4 0 6-1.2 6-3.8 0-2.5-2-3.6-6-3.6h-6.5Z" fill="currentColor" />
        </svg>
      </div>
      <div>
        <h1>Pi Port Proxy</h1>
        <p class="subtitle" data-i18n="tagline">Local port proxy for Pi, WSL2, Linux & Termux</p>
      </div>
    </div>
    <div class="language-switch" aria-label="Language">
      <button type="button" data-language="en" class="active">EN</button>
      <button type="button" data-language="zh">中文</button>
    </div>
  </header>

  <p class="intro" data-i18n="intro">Only ports you explicitly add are managed. Host mode (pPORT.localhost) is recommended because root-relative paths such as /_next/ keep working.</p>

  <section class="panel">
    <form class="add" method="post" action="/api/proxies">
      <label for="port" data-i18n="proxyListeningPort">Proxy a listening port:</label>
      <input id="port" name="port" type="number" min="1" max="65535" required placeholder="5173" data-i18n-placeholder="portPlaceholder" />
      <button class="button has-tooltip" type="submit" data-i18n="addProxy" data-tooltip-key="addTip">Add proxy</button>
    </form>
  </section>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th data-i18n="port">Port</th>
          <th data-i18n="process">Process</th>
          <th data-i18n="bind">Bind</th>
          <th data-i18n="status">Status</th>
          <th data-i18n="actions">Actions</th>
        </tr>
      </thead>
      <tbody>${rows || '<tr><td class="empty" colspan="5" data-i18n="empty">No managed proxies yet. Add a port above or use /proxy &lt;port&gt; inside Pi.</td></tr>'}</tbody>
    </table>
  </div>

  <script>
    (function () {
      var translations = {
        en: {
          tagline: "Local port proxy for Pi, WSL2, Linux & Termux",
          intro: "Only ports you explicitly add are managed. Host mode (pPORT.localhost) is recommended because root-relative paths such as /_next/ keep working.",
          proxyListeningPort: "Proxy a listening port:",
          portPlaceholder: "5173",
          addProxy: "Add proxy",
          port: "Port",
          process: "Process",
          bind: "Bind",
          status: "Status",
          actions: "Actions",
          listening: "listening",
          offline: "offline",
          open: "Open",
          pathMode: "Path mode",
          remove: "Remove",
          empty: "No managed proxies yet. Add a port above or use /proxy <port> inside Pi.",
          addTip: "Add this listening port to the managed proxy list.",
          openTip: "Open with host-based routing. Recommended for Next.js and root-relative URLs.",
          pathTip: "Open through /proxy/<port>/. Some apps with absolute paths may not support this mode.",
          removeTip: "Stop managing this port. The underlying service is not stopped."
        },
        zh: {
          tagline: "适用于 Pi、WSL2、Linux 与 Termux 的本地端口代理",
          intro: "只管理你明确添加的端口。推荐使用 Host 模式（pPORT.localhost），因为 /_next/ 等根路径资源可以正常工作。",
          proxyListeningPort: "代理一个正在监听的端口：",
          portPlaceholder: "5173",
          addProxy: "添加代理",
          port: "端口",
          process: "进程",
          bind: "绑定地址",
          status: "状态",
          actions: "操作",
          listening: "监听中",
          offline: "已离线",
          open: "打开",
          pathMode: "路径模式",
          remove: "移除",
          empty: "还没有已管理的代理。请在上方添加端口，或在 Pi 中使用 /proxy <端口>。",
          addTip: "把这个正在监听的端口加入代理管理列表。",
          openTip: "使用基于 Host 的代理打开。推荐用于 Next.js 和使用根绝对路径的应用。",
          pathTip: "通过 /proxy/<端口>/ 打开。部分使用绝对路径的应用可能不兼容。",
          removeTip: "从管理列表移除该端口，不会停止端口背后的服务。"
        }
      };

      function applyLanguage(language) {
        var lang = translations[language] ? language : "en";
        var strings = translations[lang];
        document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";

        document.querySelectorAll("[data-i18n]").forEach(function (element) {
          var key = element.getAttribute("data-i18n");
          if (key && strings[key] !== undefined) element.textContent = strings[key];
        });
        document.querySelectorAll("[data-i18n-placeholder]").forEach(function (element) {
          var key = element.getAttribute("data-i18n-placeholder");
          if (key && strings[key] !== undefined) element.setAttribute("placeholder", strings[key]);
        });
        document.querySelectorAll("[data-tooltip-key]").forEach(function (element) {
          var key = element.getAttribute("data-tooltip-key");
          if (key && strings[key] !== undefined) element.setAttribute("data-tooltip", strings[key]);
        });
        document.querySelectorAll("[data-language]").forEach(function (button) {
          button.classList.toggle("active", button.getAttribute("data-language") === lang);
        });

        try { localStorage.setItem("pi-port-proxy-language", lang); } catch (_) {}
      }

      var initialLanguage = "en";
      try { initialLanguage = localStorage.getItem("pi-port-proxy-language") || "en"; } catch (_) {}
      applyLanguage(initialLanguage);

      document.querySelectorAll("[data-language]").forEach(function (button) {
        button.addEventListener("click", function () {
          applyLanguage(button.getAttribute("data-language") || "en");
        });
      });
    })();
  </script>
</body>
</html>`;
}

function sendJson(res: ServerResponse, status: number, value: unknown): void {
  res.writeHead(status, { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" });
  res.end(JSON.stringify(value, null, 2));
}

function buildForwardHeaders(req: IncomingMessage, port: number, prefix?: string): IncomingHttpHeaders {
  const headers: IncomingHttpHeaders = { ...req.headers };
  const originalHost = req.headers.host;
  headers.host = `127.0.0.1:${port}`;
  headers["x-forwarded-host"] = originalHost ?? "";
  headers["x-forwarded-proto"] = "http";
  if (prefix) headers["x-forwarded-prefix"] = prefix;
  else delete headers["x-forwarded-prefix"];
  return headers;
}

async function readRequestBody(req: IncomingMessage, limit = 8192): Promise<string> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    let size = 0;

    req.on("data", (chunk: Buffer) => {
      size += chunk.length;
      if (size > limit) {
        reject(new Error("Request body too large"));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

function parsePortFromBody(body: string, contentType: string | undefined): number | null {
  try {
    if (contentType?.includes("application/json")) {
      const value = JSON.parse(body) as { port?: unknown };
      const port = Number(value.port);
      return Number.isInteger(port) ? port : null;
    }
  } catch {
    return null;
  }

  const form = new URLSearchParams(body);
  const port = Number(form.get("port"));
  return Number.isInteger(port) ? port : null;
}

function proxyHttp(
  req: IncomingMessage,
  res: ServerResponse,
  port: number,
  path: string,
  prefix?: string,
): void {
  const upstream = http.request(
    {
      hostname: "127.0.0.1",
      port,
      method: req.method,
      path,
      headers: buildForwardHeaders(req, port, prefix),
    },
    (upstreamRes) => {
      res.writeHead(upstreamRes.statusCode ?? 502, upstreamRes.statusMessage, upstreamRes.headers);
      upstreamRes.pipe(res);
    },
  );

  upstream.on("error", (error) => {
    if (!res.headersSent) res.writeHead(502, { "content-type": "text/plain; charset=utf-8" });
    res.end(`Bad Gateway: ${error.message}`);
  });

  req.pipe(upstream);
}

function writeUpgradeResponse(client: Duplex, upstreamRes: IncomingMessage): void {
  const statusCode = upstreamRes.statusCode ?? 101;
  const statusMessage = upstreamRes.statusMessage ?? "Switching Protocols";
  let head = `HTTP/1.1 ${statusCode} ${statusMessage}\r\n`;

  for (let i = 0; i < upstreamRes.rawHeaders.length; i += 2) {
    head += `${upstreamRes.rawHeaders[i]}: ${upstreamRes.rawHeaders[i + 1]}\r\n`;
  }

  client.write(`${head}\r\n`);
}

function proxyWebSocket(
  req: IncomingMessage,
  clientSocket: Duplex,
  clientHead: Buffer,
  port: number,
  path: string,
  prefix?: string,
): void {
  const upstreamReq = http.request({
    hostname: "127.0.0.1",
    port,
    method: req.method ?? "GET",
    path,
    headers: buildForwardHeaders(req, port, prefix),
  });

  upstreamReq.on("upgrade", (upstreamRes, upstreamSocket, upstreamHead) => {
    writeUpgradeResponse(clientSocket, upstreamRes);
    if (clientHead.length) upstreamSocket.write(clientHead);
    if (upstreamHead.length) clientSocket.write(upstreamHead);
    upstreamSocket.pipe(clientSocket);
    clientSocket.pipe(upstreamSocket);
  });

  upstreamReq.on("response", (upstreamRes) => {
    clientSocket.write(
      `HTTP/1.1 ${upstreamRes.statusCode ?? 502} ${upstreamRes.statusMessage ?? "Bad Gateway"}\r\nConnection: close\r\n\r\n`,
    );
    clientSocket.destroy();
  });

  upstreamReq.on("error", () => {
    clientSocket.write("HTTP/1.1 502 Bad Gateway\r\nConnection: close\r\n\r\n");
    clientSocket.destroy();
  });

  upstreamReq.end();
}

export async function startProxyServer(options: ProxyServerOptions = {}): Promise<ProxyServerHandle> {
  const host = options.host ?? process.env.PI_PORT_PROXY_HOST ?? DEFAULT_HOST;
  const requestedPort = options.port ?? Number(process.env.PI_PORT_PROXY_PORT ?? DEFAULT_PORT);
  const envAllowed = (process.env.PI_PORT_PROXY_ALLOWED_PORTS ?? "")
    .split(",")
    .map((value) => Number(value.trim()))
    .filter((value) => Number.isInteger(value) && value > 0 && value <= 65535);
  const allowedPorts = new Set<number>(options.allowedPorts ?? envAllowed);
  const managedPorts = new Set<number>(options.initialPorts ?? []);

  if (!isLoopbackHost(host) && allowedPorts.size === 0) {
    throw new Error(
      "Refusing to bind pi-port-proxy beyond loopback without PI_PORT_PROXY_ALLOWED_PORTS. " +
        "Set an explicit allow-list before exposing the proxy to LAN/public interfaces.",
    );
  }

  let actualPort = requestedPort;

  const discoverPorts = () => discoverListeningPorts();

  const listManagedPorts = async (): Promise<ManagedProxy[]> => {
    const discovered = await discoverListeningPorts();
    const byPort = new Map(discovered.map((item) => [item.port, item]));
    return [...managedPorts]
      .sort((a, b) => a - b)
      .map((port) => ({ port, listening: byPort.has(port), listener: byPort.get(port) }));
  };

  const canRegister = async (port: number): Promise<boolean> => {
    if (!Number.isInteger(port) || port < 1 || port > 65535 || port === actualPort) return false;
    if (!isLoopbackHost(host) && !allowedPorts.has(port)) return false;
    return isListening(port);
  };

  const registerPort = async (port: number): Promise<ManagedProxy> => {
    if (!(await canRegister(port))) {
      throw new Error(`Port ${port} is not allowed or is not currently listening.`);
    }
    managedPorts.add(port);
    const listener = (await discoverListeningPorts()).find((item) => item.port === port);
    return { port, listening: Boolean(listener), listener };
  };

  const canUseManagedPort = async (port: number): Promise<boolean> => {
    return managedPorts.has(port) && port !== actualPort && (await isListening(port));
  };

  const server = http.createServer(async (req: IncomingMessage, res: ServerResponse) => {
    const hostTargetPort = parseHostProxyPort(req.headers.host);
    if (hostTargetPort !== null) {
      if (!(await canUseManagedPort(hostTargetPort))) {
        res.writeHead(403, { "content-type": "text/plain; charset=utf-8" });
        res.end(`Port ${hostTargetPort} is not a managed listening proxy.`);
        return;
      }
      proxyHttp(req, res, hostTargetPort, req.url ?? "/");
      return;
    }

    const parsed = new URL(req.url ?? "/", "http://localhost");

    if (parsed.pathname === "/") {
      res.writeHead(200, { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" });
      res.end(renderDashboard(await listManagedPorts(), actualPort));
      return;
    }

    if (parsed.pathname === "/api/ports" && req.method === "GET") {
      sendJson(res, 200, await listManagedPorts());
      return;
    }

    if (parsed.pathname === "/api/discover" && req.method === "GET") {
      sendJson(
        res,
        200,
        (await discoverListeningPorts()).filter((item) => item.port !== actualPort),
      );
      return;
    }

    if (parsed.pathname === "/api/proxies" && req.method === "POST") {
      try {
        const body = await readRequestBody(req);
        const port = parsePortFromBody(body, req.headers["content-type"]);
        if (port === null || port < 1 || port > 65535) {
          sendJson(res, 400, { error: "port must be an integer from 1 to 65535" });
          return;
        }
        const proxy = await registerPort(port);
        if (req.headers.accept?.includes("application/json") || req.headers["content-type"]?.includes("application/json")) {
          sendJson(res, 201, proxy);
        } else {
          res.writeHead(303, { location: "/" });
          res.end();
        }
      } catch (error) {
        sendJson(res, 400, { error: (error as Error).message });
      }
      return;
    }

    const removeMatch = parsed.pathname.match(/^\/api\/proxies\/(\d+)\/remove$/);
    if (removeMatch && req.method === "POST") {
      const port = Number(removeMatch[1]);
      managedPorts.delete(port);
      res.writeHead(303, { location: "/" });
      res.end();
      return;
    }

    const target = parseProxyPath(req.url);
    if (!target) {
      res.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
      res.end("Use the dashboard to add a port first, then open p<port>.localhost:<proxy-port> or /proxy/<port>/.");
      return;
    }

    if (!(await canUseManagedPort(target.port))) {
      res.writeHead(403, { "content-type": "text/plain; charset=utf-8" });
      res.end(`Port ${target.port} is not a managed listening proxy.`);
      return;
    }

    proxyHttp(req, res, target.port, target.path, `/proxy/${target.port}`);
  });

  server.on("upgrade", async (req, socket, head) => {
    const hostTargetPort = parseHostProxyPort(req.headers.host);
    if (hostTargetPort !== null) {
      if (!(await canUseManagedPort(hostTargetPort))) {
        socket.write("HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n");
        socket.destroy();
        return;
      }
      proxyWebSocket(req, socket, head, hostTargetPort, req.url ?? "/");
      return;
    }

    const target = parseProxyPath(req.url);
    if (!target || !(await canUseManagedPort(target.port))) {
      socket.write("HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n");
      socket.destroy();
      return;
    }

    proxyWebSocket(req, socket, head, target.port, target.path, `/proxy/${target.port}`);
  });

  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(requestedPort, host, () => {
      server.off("error", reject);
      resolve();
    });
  });

  const address = server.address() as AddressInfo;
  actualPort = address.port;
  const displayHost = host === "::1" ? "[::1]" : host;
  const baseUrl = `http://${displayHost}:${actualPort}`;

  return {
    host,
    port: actualPort,
    baseUrl,
    discoverPorts,
    listManagedPorts,
    registerPort,
    unregisterPort(port: number) {
      return managedPorts.delete(port);
    },
    isManaged(port: number) {
      return managedPorts.has(port);
    },
    proxyUrl(port: number) {
      return isLoopbackHost(host) ? `http://p${port}.localhost:${actualPort}/` : `${baseUrl}/proxy/${port}/`;
    },
    pathProxyUrl(port: number) {
      return `${baseUrl}/proxy/${port}/`;
    },
    async close() {
      await new Promise<void>((resolve, reject) => {
        server.close((error) => (error ? reject(error) : resolve()));
      });
    },
  };
}
