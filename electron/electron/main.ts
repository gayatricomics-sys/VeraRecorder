import { app, BrowserWindow } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn, ChildProcess } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let mainWindow: BrowserWindow | null = null;
let apiProcess: ChildProcess | null = null;

function startBackend() {
  const isWin = process.platform === 'win32';
  const apiExecutable = isWin ? 'api.exe' : 'api';
  
  // The backend is a PyInstaller folder build (python/dist/api/), not a
  // single self-extracting exe: --onefile builds are frequently flagged by
  // Windows Defender.
  let apiPath: string;
  if (!app.isPackaged) {
    apiPath = path.join(__dirname, '../../python/dist/api', apiExecutable);
  } else {
    apiPath = path.join(process.resourcesPath, 'api', apiExecutable);
  }

  console.log('Starting Python Backend at:', apiPath);
  
  try {
    apiProcess = spawn(apiPath, [], {
      cwd: path.dirname(apiPath),
      detached: false,
      stdio: 'pipe',
      windowsHide: true,
    });

    apiProcess.stdout?.on('data', (data) => {
      console.log(`API: ${data}`);
    });

    apiProcess.stderr?.on('data', (data) => {
      console.error(`API Error: ${data}`);
    });

    // Without this, a missing/non-executable backend binary emits an
    // unhandled 'error' event and crashes the Electron main process.
    apiProcess.on('error', (err) => {
      console.error('Failed to start backend API:', err.message);
      apiProcess = null;
    });

    apiProcess.on('close', (code) => {
      console.log(`API process exited with code ${code}`);
    });
  } catch (err) {
    console.error('Failed to start backend API:', err);
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  if (process.env.VITE_DEV_SERVER_URL) {
    // In development, load from Vite dev server
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
    mainWindow.webContents.openDevTools();
  } else {
    // In production, load from the built output
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  startBackend();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (apiProcess) {
    apiProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (apiProcess) {
    apiProcess.kill();
  }
});
