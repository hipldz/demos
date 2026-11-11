import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export interface ListeningPort {
  port: number;
  host: string;
  process?: string;
  pid?: number;
  raw: string;
}

function parseSsLine(line: string): ListeningPort | null {
  const parts = line.trim().split(/\s+/);
  if (parts.length < 5 || parts[0] !== "LISTEN") return null;

  const local = parts[3];
  const match = local.match(/^(.*):(\d+)$/);
  if (!match) return null;

  const host = match[1].replace(/^\[(.*)\]$/, "$1");
  const port = Number(match[2]);
  if (!Number.isInteger(port) || port < 1 || port > 65535) return null;

  const processMatch = line.match(/users:\(\(\"([^\"]+)\"/);
  const pidMatch = line.match(/pid=(\d+)/);

  return {
    port,
    host,
    process: processMatch?.[1],
    pid: pidMatch ? Number(pidMatch[1]) : undefined,
    raw: line,
  };
}

export async function discoverListeningPorts(): Promise<ListeningPort[]> {
  try {
    const { stdout } = await execFileAsync("ss", ["-ltnpH"], {
      timeout: 2500,
      maxBuffer: 1024 * 1024,
    });

    const byPort = new Map<number, ListeningPort>();
    for (const line of stdout.split("\n")) {
      if (!line.trim()) continue;
      const parsed = parseSsLine(line);
      if (!parsed) continue;

      const current = byPort.get(parsed.port);
      if (!current || (!current.process && parsed.process)) {
        byPort.set(parsed.port, parsed);
      }
    }

    return [...byPort.values()].sort((a, b) => a.port - b.port);
  } catch {
    return [];
  }
}

export async function isListening(port: number): Promise<boolean> {
  const ports = await discoverListeningPorts();
  return ports.some((item) => item.port === port);
}
