import { chromium } from 'playwright';
import { createInterface } from 'node:readline';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

const START_URL = 'https://sitiosusda.sag.gob.cl/Home/Inicio';
const OUTPUT_DIR = path.resolve(import.meta.dirname, '../../docs/usda');
const userArgumentIndex = process.argv.findIndex((arg) => arg === '--user' || arg.startsWith('--user='));
const profileName = process.env.OBSERVER_USER
  || (process.argv[userArgumentIndex]?.startsWith('--user=') ? process.argv[userArgumentIndex].split('=')[1] : process.argv[userArgumentIndex + 1])
  || 'default';
const profileRoot = path.join(os.homedir(), 'AppData', 'Local', 'AgroSample', 'usda-observer', 'profiles', profileName);
const tracePath = path.join(OUTPUT_DIR, 'network-trace.json');
const events = [];
let sequence = 0;

const sensitiveKey = /password|passwd|token|csrf|xsrf|cookie|authorization|session|sid|secret|credential/i;
const sensitiveHeader = /authorization|cookie|set-cookie|x-csrf|x-xsrf/i;

function sanitizeValue(value, key = '') {
  if (sensitiveKey.test(key)) return 'TOKEN_PRESENTE = true';
  if (typeof value === 'string' && value.length > 5000) return `${value.slice(0, 5000)}...[TRUNCADO]`;
  return value;
}

function sanitizeObject(value) {
  if (!value || typeof value !== 'object') return value;
  if (Array.isArray(value)) return value.map((item) => sanitizeObject(item));
  return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, sanitizeValue(sanitizeObject(item), key)]));
}

function sanitizeHeaders(headers) {
  return Object.fromEntries(Object.entries(headers)
    .filter(([key]) => !sensitiveHeader.test(key))
    .map(([key, value]) => [key, sanitizeValue(value, key)]));
}

function sanitizeUrl(rawUrl) {
  try {
    const url = new URL(rawUrl);
    for (const key of url.searchParams.keys()) {
      if (sensitiveKey.test(key)) url.searchParams.set(key, 'TOKEN_PRESENTE = true');
    }
    return url.toString();
  } catch {
    return rawUrl;
  }
}

function sanitizeHtml(html) {
  return html
    .replace(/((?:name|id)=["'][^"']*(?:password|token|csrf|xsrf|session|sid)[^"']*["'][^>]*value=["'])[^"']*/gi, '$1TOKEN_PRESENTE = true')
    .replace(/((?:value|content)=["'])([^"']{20,})(["'])/gi, '$1[VALOR_SENSIBLE_REDACTADO]$3')
    .slice(0, 10000);
}

function parsePostData(request) {
  const raw = request.postData();
  if (!raw) return undefined;
  const contentType = request.headers()['content-type'] || '';
  if (contentType.includes('application/json')) {
    try { return sanitizeObject(JSON.parse(raw)); } catch { return '[JSON_NO_PARSEABLE]'; }
  }
  if (contentType.includes('application/x-www-form-urlencoded')) {
    return Object.fromEntries([...new URLSearchParams(raw)].map(([key, value]) => [key, sanitizeValue(value, key)]));
  }
  if (contentType.includes('multipart/form-data')) return '[MULTIPART_DATA_PRESENTE]';
  return sanitizeValue(raw);
}

async function saveTrace() {
  await mkdir(OUTPUT_DIR, { recursive: true });
  await writeFile(tracePath, JSON.stringify({ generatedAt: new Date().toISOString(), events }, null, 2), 'utf8');
}

function record(type, data) {
  events.push({ sequence: ++sequence, timestamp: new Date().toISOString(), type, ...data });
  void saveTrace();
}

function attachPage(page) {
  page.on('framenavigated', (frame) => {
    if (frame === page.mainFrame()) record('page_change', { url: frame.url() });
  });
  page.on('request', (request) => {
    record('request', {
      method: request.method(),
      url: sanitizeUrl(request.url()),
      resourceType: request.resourceType(),
      headers: sanitizeHeaders(request.headers()),
      postData: parsePostData(request),
    });
  });
  page.on('response', async (response) => {
    const request = response.request();
    const contentType = response.headers()['content-type'] || '';
    const item = {
      method: request.method(),
      url: sanitizeUrl(response.url()),
      status: response.status(),
      contentType,
    };
    if (contentType.includes('application/json')) {
      try { item.body = sanitizeObject(await response.json()); } catch { item.body = '[JSON_NO_PARSEABLE]'; }
    } else if (contentType.includes('text/html') && response.status() < 400) {
      try { item.body = sanitizeHtml(await response.text()); } catch { item.body = '[HTML_NO_DISPONIBLE]'; }
    }
    record('response', item);
  });
  page.on('console', (message) => {
    if (message.type() === 'error') record('browser_console_error', { text: message.text() });
  });
}

const launchOptions = {
  headless: false,
  viewport: { width: 1440, height: 1000 },
  executablePath: process.env.CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
};
const context = await chromium.launchPersistentContext(profileRoot, launchOptions);
const page = context.pages()[0] || await context.newPage();
attachPage(page);
await page.exposeFunction('__recordUsdaClick', (element) => record('click', { element }));
await page.addInitScript(() => {
  const describe = (element) => {
    if (!(element instanceof Element)) return null;
    const attributes = Object.fromEntries([...element.attributes]
      .filter((attribute) => attribute.name.startsWith('data-') || ['id', 'class', 'name', 'value', 'onclick', 'href', 'type'].includes(attribute.name))
      .map((attribute) => [attribute.name, attribute.value]));
    const selector = element.id ? `#${CSS.escape(element.id)}` : element.className && typeof element.className === 'string'
      ? `${element.tagName.toLowerCase()}.${element.className.trim().split(/\\s+/).filter(Boolean).map(CSS.escape).join('.')}`
      : element.tagName.toLowerCase();
    return {
      tagName: element.tagName.toLowerCase(),
      selector,
      id: element.id || '',
      className: typeof element.className === 'string' ? element.className : '',
      name: element.getAttribute('name') || '',
      value: element.getAttribute('value') || '',
      dataAttributes: Object.fromEntries(Object.entries(attributes).filter(([key]) => key.startsWith('data-'))),
      onclick: element.getAttribute('onclick') || '',
      text: (element.innerText || element.textContent || '').trim().slice(0, 500),
      outerHTML: element.outerHTML
        .replace(/((?:name|id)=["'][^"']*(?:password|token|csrf|xsrf|session|sid)[^"']*["'][^>]*value=["'])[^"']*/gi, '$1TOKEN_PRESENTE = true')
        .slice(0, 5000),
    };
  };
  window.addEventListener('click', (event) => {
    const element = event.target instanceof Element ? event.target.closest('button,a,input,select,textarea,[onclick],[role="button"]') || event.target : event.target;
    if (window.__recordUsdaClick) window.__recordUsdaClick(describe(element));
  }, true);
});

await page.goto(START_URL, { waitUntil: 'domcontentloaded' });
record('observer_started', { url: page.url(), profile: profileName });
console.log(`Navegador abierto para observación manual: ${START_URL}`);
console.log(`Perfil local aislado: ${profileName}`);
console.log('Realiza el flujo manualmente. No se ejecutarán clics ni formularios automáticamente.');
console.log('Cuando termines, vuelve a esta terminal y presiona Enter para guardar el trace.');

const readline = createInterface({ input: process.stdin, output: process.stdout });
await new Promise((resolve) => readline.question('', resolve));
readline.close();
record('observer_finished', { url: page.url() });
await saveTrace();
await context.close();
console.log(`Observación guardada en ${tracePath}`);
