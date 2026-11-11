import { spawn } from "node:child_process";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { startProxyServer, type ProxyServerHandle } from "./server.js";
import type { ListeningPort } from "./ports.js";

function isTermux(): boolean {
  return Boolean(process.env.TERMUX_VERSION || process.env.PREFIX?.includes("com.termux"));
}

async function openUrl(url: string): Promise<boolean> {
  if (!isTermux()) return false;

  return new Promise((resolve) => {
    const child = spawn("termux-open-url", [url], {
      detached: true,
      stdio: "ignore",
    });
    child.once("error", () => resolve(false));
    child.once("spawn", () => {
      child.unref();
      resolve(true);
    });
  });
}

interface PortProxyToolDetails {
  managedPorts: number[];
  discoveredPorts: ListeningPort[];
  port: number | null;
  url: string | null;
  pathUrl: string | null;
  opened: boolean;
}

function emptyDetails(): PortProxyToolDetails {
  return {
    managedPorts: [],
    discoveredPorts: [],
    port: null,
    url: null,
    pathUrl: null,
    opened: false,
  };
}

export default function piPortProxyExtension(pi: ExtensionAPI) {
  let server: ProxyServerHandle | undefined;

  const ensureServer = async () => {
    if (server) return server;
    server = await startProxyServer();
    return server;
  };

  const stopServer = async () => {
    const current = server;
    server = undefined;
    if (current) await current.close();
  };

  pi.on("session_start", async (_event, ctx) => {
    try {
      const running = await ensureServer();
      if (ctx.hasUI) {
        ctx.ui.setStatus("pi-port-proxy", `proxy ${running.port}`);
      }
    } catch (error) {
      if (ctx.hasUI) {
        ctx.ui.notify(`pi-port-proxy failed: ${(error as Error).message}`, "error");
      }
    }
  });

  pi.on("session_shutdown", async (_event, ctx) => {
    if (ctx.hasUI) ctx.ui.setStatus("pi-port-proxy", undefined);
    await stopServer();
  });

  pi.registerCommand("ports", {
    description: "List managed proxies. Use /ports discover to inspect listening candidates.",
    handler: async (args, ctx) => {
      const running = await ensureServer();

      if (args.trim() === "discover") {
        const ports = (await running.discoverPorts()).filter((item) => item.port !== running.port);
        const text = ports.length
          ? ports.map((item) => `${item.port}\t${item.process ?? "unknown"}\t${item.host}`).join("\n")
          : "No listening TCP ports detected.";
        ctx.ui.notify(text, "info");
        return;
      }

      const proxies = await running.listManagedPorts();
      const text = proxies.length
        ? proxies
            .map((item) => `${item.port}\t${item.listening ? item.listener?.process ?? "unknown" : "offline"}\t${running.proxyUrl(item.port)}`)
            .join("\n")
        : "No managed proxies. Use /proxy <port> to add one.";
      ctx.ui.notify(text, "info");
    },
  });

  pi.registerCommand("proxy", {
    description: "Add/manage a local port and show its browser URL: /proxy 5173",
    handler: async (args, ctx) => {
      const port = Number(args.trim());
      if (!Number.isInteger(port) || port < 1 || port > 65535) {
        ctx.ui.notify("Usage: /proxy <1-65535>", "warning");
        return;
      }

      const running = await ensureServer();
      try {
        await running.registerPort(port);
      } catch (error) {
        ctx.ui.notify((error as Error).message, "warning");
        return;
      }

      const url = running.proxyUrl(port);
      const opened = await openUrl(url);
      ctx.ui.notify(opened ? `Opened ${url}` : `${url}\nPath fallback: ${running.pathProxyUrl(port)}`, "info");
    },
  });

  pi.registerCommand("unproxy", {
    description: "Stop managing a proxied port: /unproxy 5173",
    handler: async (args, ctx) => {
      const port = Number(args.trim());
      if (!Number.isInteger(port) || port < 1 || port > 65535) {
        ctx.ui.notify("Usage: /unproxy <1-65535>", "warning");
        return;
      }
      const running = await ensureServer();
      ctx.ui.notify(running.unregisterPort(port) ? `Removed proxy ${port}.` : `Port ${port} was not managed.`, "info");
    },
  });

  pi.registerTool({
    name: "port_proxy",
    label: "Port Proxy",
    description:
      "Discover local TCP listeners, manage explicit browser proxies, or remove a managed proxy. " +
      "Use host-mode URLs for web apps with root-relative assets such as Next.js.",
    promptSnippet: "Discover local listeners and explicitly manage localhost browser proxy URLs",
    promptGuidelines: [
      "Do not treat every listening port as proxied. Only add a proxy when the user asks to open, preview, or expose that port.",
      "Prefer the returned host-mode p<port>.localhost URL; path mode is only a fallback for apps that support subpaths.",
    ],
    parameters: Type.Object({
      action: Type.Union([
        Type.Literal("list"),
        Type.Literal("discover"),
        Type.Literal("url"),
        Type.Literal("remove"),
      ]),
      port: Type.Optional(Type.Number({ minimum: 1, maximum: 65535 })),
      open: Type.Optional(
        Type.Boolean({ description: "On Termux, open the generated URL with termux-open-url." }),
      ),
    }),
    async execute(_toolCallId, params) {
      const running = await ensureServer();

      if (params.action === "discover") {
        const discoveredPorts = (await running.discoverPorts()).filter((item) => item.port !== running.port);
        const details: PortProxyToolDetails = { ...emptyDetails(), discoveredPorts };
        return {
          content: [
            {
              type: "text",
              text: discoveredPorts.length
                ? discoveredPorts.map((item) => `${item.port}\t${item.process ?? "unknown"}\t${item.host}`).join("\n")
                : "No listening TCP ports detected.",
            },
          ],
          details,
        };
      }

      if (params.action === "list") {
        const proxies = await running.listManagedPorts();
        const managedPorts = proxies.map((item) => item.port);
        const details: PortProxyToolDetails = { ...emptyDetails(), managedPorts };
        return {
          content: [
            {
              type: "text",
              text: proxies.length
                ? proxies
                    .map((item) => `${item.port}\t${item.listening ? item.listener?.process ?? "unknown" : "offline"}\t${running.proxyUrl(item.port)}`)
                    .join("\n")
                : "No managed proxies.",
            },
          ],
          details,
        };
      }

      if (!params.port) throw new Error(`port is required when action=${params.action}`);

      if (params.action === "remove") {
        const removed = running.unregisterPort(params.port);
        const details: PortProxyToolDetails = { ...emptyDetails(), port: params.port };
        return {
          content: [{ type: "text", text: removed ? `Removed proxy ${params.port}.` : `Port ${params.port} was not managed.` }],
          details,
        };
      }

      await running.registerPort(params.port);
      const url = running.proxyUrl(params.port);
      const pathUrl = running.pathProxyUrl(params.port);
      const opened = params.open ? await openUrl(url) : false;
      const details: PortProxyToolDetails = {
        ...emptyDetails(),
        managedPorts: (await running.listManagedPorts()).map((item) => item.port),
        port: params.port,
        url,
        pathUrl,
        opened,
      };
      return {
        content: [{ type: "text", text: opened ? `Opened ${url}` : `${url}\nPath fallback: ${pathUrl}` }],
        details,
      };
    },
  });
}
