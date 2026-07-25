const http = require('http');
const fs = require('fs');
const path = require('path');

const root = __dirname;
const mime = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml' };
const summary = require('./api/summary');

const server = http.createServer((req, res) => {
  if (req.url === '/api/summary') return summary(req, res);
  const requested = req.url.split('?')[0] === '/' ? '/index.html' : req.url.split('?')[0];
  const safePath = path.normalize(path.join(root, requested));
  if (!safePath.startsWith(root)) { res.writeHead(403); return res.end('Forbidden'); }
  fs.readFile(safePath, (error, file) => {
    if (error) { res.writeHead(404); return res.end('Not found'); }
    res.writeHead(200, { 'Content-Type': mime[path.extname(safePath)] || 'application/octet-stream' });
    res.end(file);
  });
});

function listen(port, attempts = 0) {
  server.once('error', (error) => {
    if (error.code === 'EADDRINUSE' && attempts < 10) {
      console.warn(`Port ${port} is in use; trying ${port + 1}.`);
      listen(port + 1, attempts + 1);
      return;
    }
    throw error;
  });
  server.listen(port, () => console.log(`GridMatch GB running at http://localhost:${port}`));
}

listen(Number(process.env.PORT) || 3000);
