import { startProxyServer } from "./server.js";

const handle = await startProxyServer();
console.log(`pi-port-proxy listening at ${handle.baseUrl}`);
console.log(`Dashboard: ${handle.baseUrl}/`);

const shutdown = async () => {
  await handle.close();
  process.exit(0);
};

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
