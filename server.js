// Minimal static server for the KARDONOV site + a tiny /api/lead endpoint
// that forwards contact-form submissions to Telegram.
// Railway sets process.env.PORT — we must listen on it.
// Secrets live in env vars (set them in Railway → Variables):
//   TELEGRAM_BOT_TOKEN  — token from @BotFather
//   TELEGRAM_CHAT_ID    — chat/user/group id that should receive leads
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3000;
const DIR = path.join(__dirname, 'public');
const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || '';
const CHAT_ID = process.env.TELEGRAM_CHAT_ID || '';

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.webp': 'image/webp',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
  '.txt': 'text/plain; charset=utf-8',
  '.webmanifest': 'application/manifest+json'
};

/* ---------- helpers ---------- */
const escHtml = (s) => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function sendJson(res, code, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(body);
}

// read the request body with a hard size cap
function readBody(req, limit) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', (chunk) => {
      data += chunk;
      if (data.length > limit) { reject(new Error('payload too large')); req.destroy(); }
    });
    req.on('end', () => resolve(data));
    req.on('error', reject);
  });
}

// very small in-memory rate limit: max N submissions per window per IP
const RL = new Map();
const RL_MAX = 5, RL_WINDOW = 10 * 60 * 1000; // 5 per 10 min
function rateLimited(ip) {
  const now = Date.now();
  const hits = (RL.get(ip) || []).filter((t) => now - t < RL_WINDOW);
  if (hits.length >= RL_MAX) { RL.set(ip, hits); return true; }
  hits.push(now);
  RL.set(ip, hits);
  if (RL.size > 5000) RL.clear(); // crude memory guard
  return false;
}

async function sendToTelegram(text) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 8000);
  try {
    const r = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: CHAT_ID,
        text,
        parse_mode: 'HTML',
        disable_web_page_preview: true
      }),
      signal: ctrl.signal
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok || !j.ok) throw new Error('telegram api: ' + JSON.stringify(j));
    return true;
  } finally {
    clearTimeout(timer);
  }
}

/* ---------- POST /api/lead ---------- */
async function handleLead(req, res) {
  const ip = (req.headers['x-forwarded-for'] || '').split(',')[0].trim()
    || req.socket.remoteAddress || 'unknown';

  if (rateLimited(ip)) return sendJson(res, 429, { ok: false, error: 'rate_limited' });

  let raw;
  try { raw = await readBody(req, 8 * 1024); }
  catch { return sendJson(res, 413, { ok: false, error: 'too_large' }); }

  let data;
  try { data = JSON.parse(raw || '{}'); }
  catch { return sendJson(res, 400, { ok: false, error: 'bad_json' }); }

  // honeypot: real users never fill this hidden field
  if (data.company) return sendJson(res, 200, { ok: true });

  const phone = String(data.phone || '').trim().slice(0, 100);
  const nick = String(data.nick || '').trim().slice(0, 100);
  const method = String(data.method || '').trim().slice(0, 120);
  const comment = String(data.comment || '').trim().slice(0, 2000);

  if (!phone && !nick) return sendJson(res, 400, { ok: false, error: 'need_contact' });

  if (!BOT_TOKEN || !CHAT_ID) {
    console.error('Lead received but TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID are not set:',
      { phone, nick, method, comment });
    return sendJson(res, 503, { ok: false, error: 'not_configured' });
  }

  const when = new Date().toLocaleString('ru-RU', { timeZone: 'Europe/Moscow' });
  const lines = [
    '🆕 <b>Новая заявка с сайта KARDONOV</b>',
    '',
    phone ? `📞 Телефон: <b>${escHtml(phone)}</b>` : null,
    nick ? `👤 Ник: <b>${escHtml(nick)}</b>` : null,
    method ? `📡 Способ связи: ${escHtml(method)}` : null,
    comment ? `💬 Комментарий: ${escHtml(comment)}` : null,
    '',
    `🕒 ${escHtml(when)} (МСК)`
  ].filter((l) => l !== null);

  try {
    await sendToTelegram(lines.join('\n'));
    return sendJson(res, 200, { ok: true });
  } catch (e) {
    console.error('Telegram send failed:', e.message);
    return sendJson(res, 502, { ok: false, error: 'send_failed' });
  }
}

/* ---------- static files ---------- */
function serveStatic(req, res) {
  let urlPath = decodeURIComponent((req.url || '/').split('?')[0]);
  if (urlPath === '/') urlPath = '/index.html';

  const filePath = path.join(DIR, path.normalize(urlPath));
  // prevent path traversal outside /public
  if (!filePath.startsWith(DIR)) {
    res.writeHead(403);
    return res.end('Forbidden');
  }

  fs.readFile(filePath, (err, data) => {
    if (err) {
      // fall back to index.html
      fs.readFile(path.join(DIR, 'index.html'), (e2, d2) => {
        if (e2) { res.writeHead(404); return res.end('Not found'); }
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-cache' });
        res.end(d2);
      });
      return;
    }
    const ext = path.extname(filePath).toLowerCase();
    const headers = { 'Content-Type': TYPES[ext] || 'application/octet-stream' };
    // HTML must always revalidate (so deploys show up immediately);
    // fingerprint-free static assets are cached for a year.
    headers['Cache-Control'] = (ext === '.html')
      ? 'no-cache'
      : 'public, max-age=31536000, immutable';
    res.writeHead(200, headers);
    res.end(data);
  });
}

const server = http.createServer((req, res) => {
  const pathname = (req.url || '/').split('?')[0];
  if (pathname === '/api/lead') {
    if (req.method !== 'POST') { res.writeHead(405); return res.end('Method Not Allowed'); }
    handleLead(req, res).catch((e) => {
      console.error('lead handler error:', e);
      sendJson(res, 500, { ok: false, error: 'server_error' });
    });
    return;
  }
  serveStatic(req, res);
});

server.listen(PORT, () => {
  console.log('KARDONOV site running on port ' + PORT);
  if (!BOT_TOKEN || !CHAT_ID) {
    console.warn('⚠  TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set — /api/lead will return 503.');
  }
});
