// Default E2E only: reset IP counters before each case in a dedicated, labelled Redis.
// The real limiter remains enabled; user keys remain intact. One worker prevents another
// test from erasing this case's counters. Dedicated RN31 tests still prove the limit.
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { test as base } from "@playwright/test";

const run = promisify(execFile);
const script = `
local total = 0
repeat
  local cursor = '0'
  local removed = 0
  repeat
    local batch = redis.call('SCAN', cursor, 'MATCH', 'varal:rn31::ip:*', 'COUNT', 100)
    cursor = batch[1]
    for _, key in ipairs(batch[2]) do
      removed = removed + redis.call('UNLINK', key)
    end
  until cursor == '0'
  total = total + removed
until removed == 0
return total
`;

type Isolation = { rn31E2eIsolation: void };
export const test = base.extend<Isolation>({
  rn31E2eIsolation: [async ({}, use, info) => {
    if (process.env.E2E_RN31_ISOLATED === "1") {
      const id = process.env.E2E_RN31_REDIS_CONTAINER;
      if (!id || !/^[a-f0-9]{12,64}$/.test(id) || process.env.E2E_RN31_PROJECT !== "varal" || process.env.E2E_RN31_SERVICE !== "redis-e2e" || info.config.workers !== 1) {
        throw new Error("RN31 isolation requires an explicit Redis container ID, expected project/service and exactly one worker");
      }
      const inspected = await run("docker", ["inspect", id], { maxBuffer: 2 * 1024 * 1024 });
      const [item] = JSON.parse(inspected.stdout) as [{
        Id: string; State: { Running: boolean }; Config: { Cmd: string[]; Labels: Record<string, string> };
        Mounts: { Type: string; Destination: string }[]; HostConfig: { PortBindings: Record<string, unknown> | null; Tmpfs: Record<string, string> | null; ReadonlyRootfs: boolean };
      }];
      const labels = item?.Config?.Labels;
      const mountsValidos = item?.Mounts.every((mount) => mount.Type === "tmpfs" && mount.Destination === "/data");
      const tmpfs = Object.keys(item?.HostConfig.Tmpfs ?? {});
      const tmpfsValidos = tmpfs.length === 1 && tmpfs[0] === "/data";
      if (!item?.State.Running || !item.Id.startsWith(id) || item.Config.Cmd?.[0] !== "redis-server" || labels?.["com.docker.compose.project"] !== "varal" || labels?.["com.docker.compose.service"] !== "redis-e2e" || labels?.["br.varal.e2e.rn31"] !== "isolated" || !mountsValidos || !tmpfsValidos || !item.HostConfig.ReadonlyRootfs || Object.keys(item.HostConfig.PortBindings ?? {}).length !== 0) {
        throw new Error("Refusing RN31 cleanup: container is not the isolated Redis E2E service");
      }
      const cleared = await run("docker", ["exec", id, "redis-cli", "--raw", "EVAL", script, "0"], { maxBuffer: 1024 });
      if (!/^\d+\s*$/.test(cleared.stdout)) throw new Error("RN31 IP counter cleanup failed");
    }
    await use();
  }, { auto: true }],
});
