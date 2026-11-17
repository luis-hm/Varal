// Run only in an exclusive window with the production-like lab and internal browser attested by DevOps.
import { chromium, request } from '@playwright/test';
import { readFileSync, realpathSync, openSync, writeSync, ftruncateSync, closeSync } from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const calibration = process.argv[2] === '--calibrate-exclusive-lab';
if (!calibration && process.argv[2] !== '--run-exclusive-lab') throw new Error('Explicit exclusive-lab flag required');
// This process runs inside the non-root browser container. /qa contains only
// synthetic metadata, public CA and private output; never mount lab.env or keys.
const dir = realpathSync('/qa');
if (dir !== '/qa') throw new Error('Expected isolated /qa artifact mount');
const origin = process.env.LAB_BASE_URL;
if (!origin || !/^https:\/\/varal\.local:\d+$/.test(origin)) throw new Error('Canonical origin required');
const cdp = process.env.LAB_CDP_URL;
if (!cdp || !/^http:\/\/127\.0\.0\.1:\d+$/.test(cdp)) throw new Error('Expected loopback-only CDP control');
const proofPath = realpathSync(path.join(dir, 'browser-proof.json'));
if (!proofPath.startsWith(`${dir}/`)) throw new Error('Internal browser network proof required');
const proof = JSON.parse(readFileSync(proofPath, 'utf8'));
const project = process.env.LAB_PROJECT;
if (!project || !/^varal11-stack-[a-z0-9]{8}$/.test(project)) throw new Error('Invalid laboratory project');
if (proof.origin !== origin || proof.network !== `${project}_frontend` || proof.direct !== true || !proof.browser_image_id || proof.docker_socket !== false || proof.egress !== false) throw new Error('Browser network proof incomplete');
const fixture = JSON.parse(readFileSync(path.join(dir, 'benchmark11-fixture.json'), 'utf8'));
if (!/^e2e-benchmark11-[0-9a-f]{32}@varal\.invalid$/.test(fixture.email) || fixture.grupos?.length !== 20 || fixture.ocultas?.length !== 20 || fixture.avisos !== 20) throw new Error('Invalid benchmark fixture');
const filename = path.join(dir, calibration ? 'benchmark11-calibration.json' : 'benchmark11-results.json');
const fd = openSync(filename, 'wx', 0o600);
const result = { status: 'running', origin, browser_network: proof.network, browser_image_id: proof.browser_image_id,
  host_cpu: os.cpus()[0]?.model, host_logical_cpus: os.cpus().length, host_memory_bytes: os.totalmem(),
  mode: calibration ? 'calibration' : 'benchmark', cpu_throttle: 4, download_bps: 9_000_000, upload_bps: 1_500_000, rtt_ms: 150, series: [], errors: [] };
function save() { const data = JSON.stringify(result, null, 2); ftruncateSync(fd, 0); writeSync(fd, data, 0, 'utf8'); }
save();
let api, browser;
try {
  api = await request.newContext({ baseURL: origin });
  const config = await api.get('/api/auth/browser/v1/config');
  if (config.status() !== 200) throw new Error('Auth bootstrap failed');
  const csrf = (await api.storageState()).cookies.find((c) => c.name === 'csrftoken')?.value;
  if (!csrf) throw new Error('CSRF absent');
  const login = await api.post('/api/auth/browser/v1/auth/login', { headers: { Origin: origin, 'X-CSRFToken': csrf }, data: { email: fixture.email, password: 'Varal-e2e!93-Linha' } });
  if (login.status() !== 200) throw new Error('Synthetic login failed');
  const me = await api.get('/api/me/');
  if (me.status() !== 200 || (await me.json()).id !== fixture.owner) throw new Error('Fixture identity mismatch');
  const headers = { 'X-Varal-Identidade-Esperada': fixture.owner };
  const get = async (url) => { const r = await api.get(url, { headers }); if (r.status() !== 200) throw new Error(`Preflight ${new URL(r.url()).pathname} returned ${r.status()}`); return r.json(); };
  const notices = await get('/api/notificacoes/resumo/');
  if (notices.nao_lidas !== 20) throw new Error('Fixture notice count is not 20');
  const grupoLista = await get(`/api/espacos/${fixture.grupos[0]}/lancamentos/`);
  if (!Array.isArray(grupoLista.itens) || JSON.stringify(grupoLista).includes(fixture.ocultas[0])) throw new Error('Hidden restricted bill leaked in group list');
  const scenarios = [];
  for (const [label, space] of [['pessoal', fixture.pessoal], ['grupo', fixture.grupos[0]]]) {
    const resumo = await get(`/api/espacos/${space}/resumo/`);
    if (!resumo.qtd || resumo.valores_indefinidos_qtd < 1 || resumo.pagas_qtd < 1) throw new Error(`Fixture incomplete: ${label}`);
    if (JSON.stringify(resumo).includes(fixture.ocultas[0])) throw new Error('Hidden restricted bill leaked in summary');
    scenarios.push({ label, space, total: resumo.total_centavos, qtd: resumo.qtd });
  }
  const state = await api.storageState();
  state.cookies.push({ name: 'varal_owner', value: fixture.owner, domain: 'varal.local', path: '/', expires: -1, httpOnly: false, secure: true, sameSite: 'Lax' });
  browser = await chromium.connectOverCDP(cdp);
  result.browser_version = browser.version();
  async function makeContext(scenario) {
    const context = await browser.newContext({ baseURL: origin, storageState: state, viewport: { width: 390, height: 844 }, reducedMotion: 'no-preference' });
    await context.addCookies([{ name: 'espaco', value: scenario.space, url: origin, secure: true, sameSite: 'Lax' }]);
    return context;
  }
  async function sample(context, scenario, run) {
    const item = { index: run, ready_ms: null, ttfb_ms: null, lcp_ms: null, api: [], errors: [] };
    const page = await context.newPage();
    const session = await context.newCDPSession(page);
    try {
      await session.send('Network.enable');
      await session.send('Network.emulateNetworkConditions', { offline: false, latency: 150, downloadThroughput: 9_000_000 / 8, uploadThroughput: 1_500_000 / 8 });
      await session.send('Emulation.setCPUThrottlingRate', { rate: 4 });
      await page.addInitScript(({ total, qtd }) => {
        const data = window;
        data.__qa11 = { lcp: null };
        new PerformanceObserver((list) => { const entries = list.getEntries(); if (entries.length) data.__qa11.lcp = entries.at(-1).startTime; }).observe({ type: 'largest-contentful-paint', buffered: true });
        const ready = () => {
          const root = document.querySelector('[data-sessao-privada]');
          const hero = document.querySelector('section[aria-label^="Total"]');
          const value = hero?.querySelector('p > span[aria-hidden="true"]');
          const text = Number((value?.textContent ?? '').replace(/\D/g, ''));
          const qtdText = hero?.textContent ?? '';
          const action = Array.from(document.querySelectorAll('a[href="/contas"]')).find((el) => el.getBoundingClientRect().width >= 44 && el.getBoundingClientRect().height >= 44 && el.checkVisibility());
          if (performance.getEntriesByName('inicio_pronto').length && root?.checkVisibility() && hero?.checkVisibility() && text === total && qtdText.includes(`${qtd} ${qtd === 1 ? 'conta' : 'contas'}`) && action) {
            performance.mark('qa11_pronto');
          } else requestAnimationFrame(ready);
        };
        requestAnimationFrame(ready);
      }, { total: scenario.total, qtd: scenario.qtd });
      page.on('requestfinished', (r) => { const u = new URL(r.url()); if (u.origin === origin && u.pathname.startsWith('/api/')) void r.response().then((response) => { const status = response?.status() ?? 0; item.api.push({ path: u.pathname, status, duration_ms: r.timing().responseEnd }); if (status >= 400 || !status) item.errors.push(`HTTP ${status} ${u.pathname}`); }); });
      page.on('requestfailed', (r) => { const u = new URL(r.url()); item.errors.push(`request failed ${u.origin === origin ? u.pathname : '[external]'}`); });
      page.on('pageerror', () => item.errors.push('pageerror'));
      await page.goto('/', { waitUntil: 'commit', timeout: 45_000 });
      await page.waitForFunction(() => performance.getEntriesByName('qa11_pronto').length > 0, null, { timeout: 45_000 });
      await page.waitForLoadState('load', { timeout: 45_000 });
      await page.evaluate(() => new Promise((resolve) => setTimeout(resolve, 500)));
      const t = await page.evaluate(() => ({ ready: performance.getEntriesByName('qa11_pronto')[0].startTime,
        ttfb: performance.getEntriesByType('navigation')[0].responseStart,
        lcp: window.__qa11.lcp, ua: navigator.userAgent, logical_cpus: navigator.hardwareConcurrency }));
      item.ready_ms = t.ready; item.ttfb_ms = t.ttfb; item.lcp_ms = t.lcp;
      result.browser_user_agent = t.ua; result.browser_logical_cpus = t.logical_cpus;
      if (t.lcp === null) item.errors.push('LCP unavailable');
      if (item.errors.length) throw new Error('Network or page errors in sample');
    } catch (e) { item.errors.push(e instanceof Error ? e.message : 'Unknown sample failure'); }
    finally { await page.close(); await session.detach().catch(() => {}); }
    return item;
  }
  for (const scenario of scenarios) {
    for (const thermal of ['cold', 'warm']) {
      const series = { scenario: scenario.label, cache: thermal, samples: [], p95_ms: null, passed: false };
      result.series.push(series); save();
      let warm;
      if (thermal === 'warm') {
        warm = await makeContext(scenario);
        const priming = await sample(warm, scenario, 0);
        if (priming.errors.length) result.errors.push(`${scenario.label} warm priming failed`);
      }
      for (let n = 1; n <= (calibration ? 1 : 20); n++) {
        const context = warm ?? await makeContext(scenario);
        try { series.samples.push(await sample(context, scenario, n)); }
        finally { if (!warm) await context.close(); }
        save();
      }
      if (warm) await warm.close();
      if (series.samples.length === 20 && series.samples.every((s) => !s.errors.length && typeof s.ready_ms === 'number')) {
        series.p95_ms = series.samples.map((s) => s.ready_ms).sort((a, b) => a - b)[18];
        series.passed = series.p95_ms <= 2000;
      }
      save();
    }
  }
  result.status = calibration
    ? (result.errors.length === 0 && result.series.length === 4 && result.series.every((s) => s.samples.length === 1 && !s.samples[0].errors.length) ? 'calibrated' : 'failed')
    : (result.errors.length === 0 && result.series.length === 4 && result.series.every((s) => s.passed) ? 'passed' : 'failed');
} catch (e) {
  result.errors.push(e instanceof Error ? e.message : 'Unknown runner failure');
  result.status = 'failed';
} finally {
  if (browser) await browser.close();
  if (api) await api.dispose();
  save(); closeSync(fd);
}
console.log(`Benchmark result: ${result.status}; details: ${filename}`);
process.exitCode = ['passed', 'calibrated'].includes(result.status) ? 0 : 1;
