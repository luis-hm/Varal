// Run only with root's explicit lab GO; no shell interpolation, no output of credentials.
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, realpathSync, openSync, writeFileSync, closeSync, unlinkSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

if (process.argv[2] !== '--run-isolated-lab') throw new Error('Explicit --run-isolated-lab required');
const input = process.env.LAB_DIR;
if (!input) throw new Error('LAB_DIR required');
const root = realpathSync(input);
if (root !== input || !/^\/tmp\/varal11-stack\.[A-Za-z0-9]{8}$/.test(root)) throw new Error('Invalid lab directory');
const project = path.basename(root).replace('.', '-').toLowerCase();
if (readFileSync(path.join(root, 'project'), 'utf8').trim() !== project) throw new Error('Lab project marker mismatch');
const markerPath = path.join(root, 'ACTIVE_RESTORE');
const markerText = readFileSync(markerPath, 'utf8');
const marker = JSON.parse(markerText);
if (Object.keys(marker).sort().join(',') !== 'operation_id,project,restore_id,state,version' || marker.version !== 1 || marker.project !== project || marker.state !== 'cutover' || !/^[a-f0-9]{32}$/.test(marker.restore_id) || !/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/.test(marker.operation_id)) throw new Error('Active restore marker invalid');
if (existsSync(path.join(root, 'CA08_GATE_PENDING')) || existsSync(path.join(root, 'ACL_GATE_PENDING'))) throw new Error('Restore gate pending');
const config = readFileSync(path.join(root, 'lab.env'), 'utf8');
const port = config.match(/^LAB_PORT=(\d+)$/m)?.[1];
const declared = config.match(/^LAB_ENV_FILE=(.+)$/m)?.[1];
if (!port || declared !== path.join(root, 'lab.env') || process.env.LAB_BASE_URL !== `https://varal.local:${port}`) throw new Error('Lab metadata mismatch');
const docker = (args, options = {}) => execFileSync('docker', args, { encoding: 'utf8', ...options });
const base = realpathSync(path.join(path.dirname(fileURLToPath(import.meta.url)), '../../../infra/lab'));
const expectedConfigs = [path.join(base, 'compose.yml'), path.join(base, 'compose.active-restore.yml')].join(',');
function container(service) {
  const ids = docker(['ps', '-q', '--filter', `label=com.docker.compose.project=${project}`, '--filter', `label=com.docker.compose.service=${service}`]).trim().split(/\s+/).filter(Boolean);
  if (ids.length !== 1) throw new Error(`Expected exactly one running ${service} in lab`);
  const details = JSON.parse(docker(['inspect', ids[0]]))[0];
  const labels = details.Config.Labels;
  if (!details.State.Running || labels['com.docker.compose.project'] !== project || labels['com.docker.compose.service'] !== service || labels['com.docker.compose.project.config_files'] !== expectedConfigs) throw new Error('Container labels do not prove active restore provenance');
  return details;
}
const api = container('api');
const db = container('postgres');
const storage = container('storage');
for (const [role, instance, destination] of [['pg', db, '/var/lib/postgresql/data'], ['objects', storage, '/data'], ['staging', api, '/varal/staging']]) {
  const name = `${project}_restore_${role}_${marker.restore_id}`;
  const mounts = instance.Mounts.filter((mount) => mount.Destination === destination);
  if (mounts.length !== 1 || mounts[0].Type !== 'volume' || mounts[0].Name !== name) throw new Error('Active restore volume mount mismatch');
  const volume = JSON.parse(docker(['volume', 'inspect', name]))[0];
  if (volume.Labels?.['varal.restore'] !== marker.restore_id || volume.Labels?.['varal.parent'] !== project) throw new Error('Active restore volume labels mismatch');
}
if (!Object.keys(api.NetworkSettings.Networks).some((key) => key === `${project}_data` && key in db.NetworkSettings.Networks)) throw new Error('API and lab database must share the isolated data network');
const network = JSON.parse(docker(['network', 'inspect', `${project}_data`]))[0];
if (!network.Internal || network.Labels?.['com.docker.compose.project'] !== project || network.Labels?.['com.docker.compose.network'] !== 'data') throw new Error('Lab data network must be internal and labelled');
if (!process.env.LAB_API_IMAGE || api.Image !== process.env.LAB_API_IMAGE) throw new Error('Explicit final API image ID must match container');
const env = Object.fromEntries(api.Config.Env.map((item) => { const i = item.indexOf('='); return [item.slice(0, i), item.slice(i + 1)]; }));
if (env.POSTGRES_DB !== 'varal_lab' || env.DJANGO_DEBUG !== '0') throw new Error('API container is not the isolated production-like lab');
const dest = path.join(root, 'benchmark11-fixture.json');
const fd = openSync(dest, 'wx', 0o600);
try {
  if (readFileSync(markerPath, 'utf8') !== markerText || existsSync(path.join(root, 'CA08_GATE_PENDING')) || existsSync(path.join(root, 'ACL_GATE_PENDING'))) throw new Error('Restore state changed');
  const source = readFileSync(path.join(path.dirname(fileURLToPath(import.meta.url)), 'fixture.py'));
  const result = docker(['exec', '-i', '-e', 'VARAL_QA11_LAB=1', api.Id, 'python', 'manage.py', 'shell', '-c', 'import sys; exec(sys.stdin.read())'], { input: source, maxBuffer: 1024 * 1024, stdio: ['pipe', 'pipe', 'pipe'] });
  const data = JSON.parse(result.trim().split('\n').at(-1));
  if (!/^e2e-benchmark11-[0-9a-f]{32}@varal\.invalid$/.test(data.email) || data.grupos?.length !== 20 || data.ocultas?.length !== 20 || data.avisos !== 20) throw new Error('Unexpected fixture result');
  writeFileSync(fd, JSON.stringify(data));
  closeSync(fd);
} catch {
  closeSync(fd);
  unlinkSync(dest); // only the exclusive empty output file created above
  throw new Error('Fixture failed; review isolated lab without printing secrets');
}
console.log(`Fixture metadata written to ${dest} (0600)`);
