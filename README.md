# TOPS 2.0

A full-stack measurement system for controlling laboratory instruments, performing automated 2D spatial scans, and analyzing thermal properties of materials using FD-PBD (Frequency-Domain Photothermal Beam Deflection).

## Overview

- **Backend**: FastAPI server handling instrument communication via GPIB (General Purpose Interface Bus) / USB, WebSocket streaming, data acquisition, and physics-based analysis
- **Frontend**: Next.js dashboard for instrument control, scan configuration, heatmap visualization, and FD-PBD analysis

### Supported Instruments

- **Lock-in Amplifier**: Stanford Research Systems SR865A (GPIB/USB via PyVISA)
- **Digital Multimeter**: BK Precision 5493C (GPIB/USB via PyVISA)
- **Motorized Stage**: Thorlabs BBD302 2-channel brushless motor controller (.NET SDK via pythonnet)

## Getting Started

1. **Setup and build** (one-time, or after code changes):

   Open PowerShell in the repo root and run:

   ```powershell
   .\build.ps1
   ```

   This creates a Python virtual environment, installs all Python and Node dependencies, builds the Next.js frontend, and copies the output to `backend/static/`.

2. **Run the application**:

   Double-click `start.bat` or run it from a terminal. This starts the server and opens the browser to `http://localhost:8000`.

   Other machines on the same network can access the app at `http://<server-ip>:8000`.

3. **Stop the application**: Close the terminal window or press `Ctrl+C`.

## Development (two servers with hot reload)

For frontend development with live reloading:

1. **Start the backend** (terminal 1):

   ```
   cd backend
   myenv\Scripts\activate
   set CORS_ORIGINS=http://localhost:3000
   uvicorn main:app --reload
   ```

2. **Start the frontend** (terminal 2):

   ```
   cd frontend\tops-2.0-measurement-system
   npm run dev
   ```

   The frontend runs at `http://localhost:3000` with hot reload. API and WebSocket calls are proxied to the backend at `http://localhost:8000` via environment variables in `.env.development`.

## Project Structure

```
├── backend/           Python FastAPI backend + instrument drivers
│   ├── main.py        Application entry point
│   ├── app/
│   │   ├── core/      Instrument drivers (lockin, multimeter, stage) and analysis
│   │   ├── models/    Pydantic models and global state
│   │   ├── routers/   REST API endpoints
│   │   └── utils/     File I/O helpers
│   ├── myenv/         Python virtual environment (not committed)
│   └── static/        Built frontend output (not committed)
├── frontend/          Next.js frontend
│   └── tops-2.0-measurement-system/
│       └── src/
│           ├── app/           Pages (dashboard, FD-PBD analysis)
│           ├── components/    UI components (controls, heatmaps, settings)
│           └── lib/           API configuration
├── build.ps1          PowerShell build script
├── start.bat          Production launcher
└── README.md
```

See [backend/README.md](backend/README.md) and [frontend/README.md](frontend/tops-2.0-measurement-system/README.md) for detailed documentation on each layer.
