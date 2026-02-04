# TOPS 2.0 Measurement System

## Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- Connected instruments: Thorlabs BBD302 stage, SR865A lock-in amplifier, BK Precision 5493C multimeter

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
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start the frontend** (terminal 2):

   ```
   cd frontend\tops-2.0-measurement-system
   npm run dev
   ```

   The frontend runs at `http://localhost:3000` with hot reload. API calls are proxied to the backend at `http://localhost:8000` via environment variables in `.env.development`.

## Project Structure

```
├── backend/           Python FastAPI backend + instrument drivers
│   ├── main.py        Application entry point
│   ├── app/           Core logic, models, and API routes
│   ├── myenv/         Python virtual environment (not committed)
│   └── static/        Built frontend output (not committed)
├── frontend/          Next.js frontend
├── build.ps1          PowerShell build script
├── start.bat          Production launcher
└── README.md
```