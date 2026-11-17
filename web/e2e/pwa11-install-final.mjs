// Dedicated persistent Chromium profile, Playwright pipe and full Chrome; isolated lab only.
import { chromium } from '@playwright/test';
import { mkdtempSync, openSync, writeFileSync, closeSync, readFileSync, realpathSync, rmSync } from 'node:fs';

if (process.argv[2] !== '--run-ephemeral-lab') throw new Error('Explicit ephemeral lab flag required');
const origin = process.env.LAB_BASE_URL;
const project = process.env.LAB_PROJECT;
if (!origin || !/^https:\/\/varal\.local:\d+$/.test(origin) || !project || !/^varal11-stack-[a-z0-9]{8}$/.test(project) || realpathSync('/qa') !== '/qa') throw new Error('Invalid lab parameters');
const proof = JSON.parse(readFileSync('/qa/browser-proof.json', 'utf8'));
if (proof.origin !== origin || proof.network !== `${project}_frontend` || proof.direct !== true || proof.docker_socket !== false || proof.egress !== false) throw new Error('Missing isolated browser proof');
const file = '/qa/pwa11-persistent3.json';
const fd = openSync(file, 'wx', 0o600);
const profile = mkdtempSync('/qa/pwa11-profile-');
const record = { status:'failed', stage:'launch', steps:[], limitations:['CDP install is not a user-gesture prompt or mobile installation','This does not prove push delivery'] };
let context, session, manifestId, installed = false;
function safe(error) { return (error instanceof Error ? error.message : 'unknown').replace(/(?:https?|wss?):\/\/[^\s"']+/g, '[url]').slice(0,300); }
try {
  context = await chromium.launchPersistentContext(profile, { channel:'chromium', headless:true, args:['--enable-devtools-pwa-handler'] });
  const page = context.pages()[0] ?? await context.newPage();
  const response = await page.goto(`${origin}/entrar`, { waitUntil:'load' });
  if (response?.status() !== 200) throw new Error('TLS entry page not 200');
  const href = await page.locator('link[rel="manifest"]').getAttribute('href');
  if (!href) throw new Error('Manifest link absent');
  const manifestResponse = await page.request.get(new URL(href, origin).href);
  if (manifestResponse.status() !== 200) throw new Error('Manifest unavailable');
  const manifest = await manifestResponse.json();
  const start = new URL(manifest.start_url, origin);
  manifestId = new URL(manifest.id ?? manifest.start_url, origin).href;
  if (start.origin !== origin || new URL(manifestId).origin !== origin || manifest.display !== 'standalone') throw new Error('Invalid manifest');
  record.manifest = { id: manifestId, start_url: start.href };
  record.sw_active = await page.evaluate(() => Promise.race([navigator.serviceWorker.ready.then((reg)=>!!reg.active), new Promise((_, reject)=>setTimeout(()=>reject(new Error('SW readiness timeout')),15000))]));
  if (!record.sw_active) throw new Error('Service worker inactive');
  const browser = context.browser();
  if (browser) { session = await browser.newBrowserCDPSession(); record.session_type='browser'; record.browser=browser.version(); }
  else { session = await context.newCDPSession(page); record.session_type='page'; }
  try {
    const cmd = await session.send('Browser.getBrowserCommandLine');
    record.has_pwa_switch = cmd.arguments.includes('--enable-devtools-pwa-handler');
    record.has_automation = cmd.arguments.includes('--enable-automation');
  } catch (error) { record.command_line_error=safe(error); }
  record.stage='install';
  await session.send('PWA.install', { manifestId, installUrlOrBundleUrl:`${origin}/` });
  installed=true; record.steps.push('install');
  record.stage='os-state'; await session.send('PWA.getOsAppState',{manifestId}); record.steps.push('os-app-state');
  record.stage='launch'; const launched=await session.send('PWA.launch',{manifestId});
  if (!launched.targetId) throw new Error('Missing PWA target');
  record.steps.push('launch');
  record.stage='target-origin';
  let target;
  try { await session.send('Target.activateTarget', { targetId: launched.targetId }); record.target_activated = true; }
  catch { record.target_activated = false; }
  for (let i=0;i<100;i++) {
    try { target=(await session.send('Target.getTargetInfo', { targetId: launched.targetId })).targetInfo; }
    catch { target = null; }
    record.target_observation={seen:!!target,type:target?.type ?? null,scheme:target?.url && URL.canParse(target.url) ? new URL(target.url).protocol : null};
    if (target?.url && URL.canParse(target.url) && new URL(target.url).origin === origin) break;
    await new Promise((resolve)=>setTimeout(resolve,300));
  }
  const originOk=!!target?.url && URL.canParse(target.url) && new URL(target.url).origin===origin;
  if (originOk) record.steps.push('target-origin');
  const internal=await context.newPage();
  try { await internal.goto('chrome://web-app-internals/',{waitUntil:'domcontentloaded',timeout:10000}); record.internals_visible=(await internal.locator('body').innerText()).includes(manifestId); }
  catch { record.internals_visible=false; }
  await internal.close();
  if (!originOk) throw new Error('PWA target origin mismatch');
  record.stage='uninstall'; await session.send('PWA.uninstall',{manifestId}); installed=false; record.steps.push('uninstall');
  try { await session.send('PWA.getOsAppState',{manifestId}); record.uninstall_confirmed=false; }
  catch { record.uninstall_confirmed=true; }
  if (!record.uninstall_confirmed) throw new Error('Uninstall not confirmed');
  record.status='passed';
} catch (error) { record.error=safe(error); }
finally {
  if (installed && session && manifestId) { try { await session.send('PWA.uninstall',{manifestId}); record.cleanup='uninstalled'; } catch { record.cleanup='failed'; } }
  if (session) await session.detach().catch(()=>{});
  if (context) await context.close();
  rmSync(profile,{recursive:true,force:true});
  writeFileSync(fd,JSON.stringify(record,null,2)); closeSync(fd);
}
console.log(`PWA persistent: ${record.status}; details: ${file}`);
process.exitCode=record.status==='passed'?0:1;
