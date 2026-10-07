import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.argv[2]);
const port = Number(process.argv[3] || 4180);
const redirectFile=path.join(root,'redirects.json');
const redirects = fs.existsSync(redirectFile) ? JSON.parse(fs.readFileSync(redirectFile, 'utf8')) : {};
const mime = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json',
  '.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp','.avif':'image/avif','.gif':'image/gif',
  '.woff2':'font/woff2','.md':'text/markdown; charset=utf-8','.txt':'text/plain','.xml':'application/xml',
  '.pdf':'application/pdf','.wasm':'application/wasm'};
http.createServer((req, res) => {
  let name;
  try { name = decodeURIComponent(new URL(req.url, 'http://localhost').pathname); }
  catch { res.writeHead(400); return res.end(); }
  const redirect = redirects[name];
  if (redirect) {
    // Route production-host redirects back into the fixture origin.
    const target = redirect.replace(/^https:\/\/docs\.docker\.com(?=\/)/, '');
    res.writeHead(301, {Location: target}); return res.end();
  }
  let file = path.resolve(root, '.' + name);
  if (!file.startsWith(root + '/') && file !== root) { res.writeHead(403); return res.end(); }
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) {
    if (!name.endsWith('/')) { res.writeHead(301, {Location:name+'/'}); return res.end(); }
    file = path.join(file, 'index.html');
  }
  let status = 200;
  if (!fs.existsSync(file)) { file=path.join(root,'404.html'); status=404; }
  res.writeHead(status, {'Content-Type':mime[path.extname(file)] || 'application/octet-stream', 'Cache-Control':'no-store'});
  if (!fs.existsSync(file)) return res.end('Not found in this partial fixture site');
  fs.createReadStream(file).pipe(res);
}).listen(port, '127.0.0.1', () => console.log(`Reference: http://127.0.0.1:${port}`));
