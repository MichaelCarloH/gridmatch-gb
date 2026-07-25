import { existsSync } from 'node:fs';
import { spawn } from 'node:child_process';
import { join } from 'node:path';

const root = process.cwd();
const windows = process.platform === 'win32';
const python = join(
  root,
  '.venv',
  windows ? 'Scripts' : 'bin',
  windows ? 'python.exe' : 'python'
);
const nextBin = join(root, 'node_modules', 'next', 'dist', 'bin', 'next');
const apiPort = process.env.GRIDMATCH_API_PORT ?? '8000';
const webPort = process.env.PORT ?? '3000';

if (!existsSync(python)) {
  console.error(
    'Missing .venv. Create it first with: py -3 -m uv sync --extra dev'
  );
  process.exit(1);
}

if (!existsSync(nextBin)) {
  console.error('Missing node_modules. Install them first with: npm install');
  process.exit(1);
}

const shared = {
  cwd: root,
  stdio: 'inherit',
  windowsHide: true
};

const api = spawn(
  python,
  [
    '-m',
    'uvicorn',
    'api.index:app',
    '--host',
    '127.0.0.1',
    '--port',
    apiPort
  ],
  shared
);

const web = spawn(
  process.execPath,
  [nextBin, 'dev', '--hostname', '127.0.0.1', '--port', webPort],
  {
    ...shared,
    env: {
      ...process.env,
      GRIDMATCH_API_INTERNAL_URL:
        process.env.GRIDMATCH_API_INTERNAL_URL ??
        `http://127.0.0.1:${apiPort}`
    }
  }
);

let stopping = false;
function stop(exitCode = 0) {
  if (stopping) return;
  stopping = true;
  api.kill();
  web.kill();
  setTimeout(() => process.exit(exitCode), 500).unref();
}

api.on('exit', (code) => {
  if (!stopping) {
    console.error(`FastAPI stopped unexpectedly with code ${code}.`);
    stop(code ?? 1);
  }
});
web.on('exit', (code) => {
  if (!stopping) {
    console.error(`Next.js stopped unexpectedly with code ${code}.`);
    stop(code ?? 1);
  }
});

process.on('SIGINT', () => stop(0));
process.on('SIGTERM', () => stop(0));
process.on('exit', () => {
  api.kill();
  web.kill();
});

console.log(
  `Starting GridMatch API on http://127.0.0.1:${apiPort} and product on http://127.0.0.1:${webPort}`
);
