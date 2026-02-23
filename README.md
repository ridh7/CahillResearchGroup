# TOPS (Thermo-Optic Phase Spectroscopy) 2.0

A full-stack measurement system for controlling laboratory instruments, performing automated 2D spatial scans, and analyzing thermal properties of materials using FD-PBD (Frequency-Domain Photothermal Beam Deflection).

## Overview

- **Backend**: FastAPI server handling instrument communication via GPIB (General Purpose Interface Bus) / USB, SSE streaming, data acquisition, and physics-based analysis
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
   set TOPS_CORS_ORIGINS=http://localhost:3000
   uvicorn main:app --reload
   ```

   Or create a `.env` file in `backend/` with:
   ```
   TOPS_CORS_ORIGINS=http://localhost:3000
   ```

2. **Start the frontend** (terminal 2):

   ```
   cd frontend\tops-2.0-measurement-system
   npm run dev
   ```

   The frontend runs at `http://localhost:3000` with hot reload. API calls are proxied to the backend at `http://localhost:8000` via environment variables in `.env.development`.

## Project Structure

```
├── backend/               Python FastAPI backend + instrument drivers
│   ├── main.py            Application entry point
│   ├── .env.example       Environment variable template
│   ├── app/
│   │   ├── config.py      Centralized configuration (Pydantic Settings)
│   │   ├── core/          Instrument drivers (lockin, multimeter, stage) and analysis
│   │   ├── dependencies.py FastAPI dependency injection functions
│   │   ├── models/        Pydantic models and global state
│   │   ├── routers/       REST API endpoints (domain-organized)
│   │   │   ├── stage.py      Stage control (10 endpoints)
│   │   │   ├── lockin.py     Lock-in amplifier (5 endpoints)
│   │   │   ├── multimeter.py Multimeter (3 endpoints)
│   │   │   ├── analysis.py   FD-PBD analysis (2 endpoints)
│   │   │   └── sse.py          SSE streaming (4 endpoints)
│   │   └── utils/         File I/O helpers
│   ├── myenv/             Python virtual environment (not committed)
│   └── static/            Built frontend output (not committed)
├── frontend/              Next.js frontend
│   └── tops-2.0-measurement-system/
│       └── src/
│           ├── app/           Pages (dashboard, FD-PBD analysis)
│           ├── components/    UI components (controls, heatmaps, settings)
│           └── lib/           API configuration
├── build.ps1              PowerShell build script
├── start.bat              Production launcher
└── README.md
```

See [backend/README.md](backend/README.md) and [frontend/README.md](frontend/tops-2.0-measurement-system/README.md) for detailed documentation on each layer.

## Additional Resources

### Scientific Concepts

- **[Photothermal Beam Deflection Spectroscopy](https://en.wikipedia.org/wiki/Photothermal_spectroscopy)** - Overview of photothermal measurement techniques
- **[Photothermal Deflection Theory (Jackson et al., 1981)](https://www.researchgate.net/publication/42390283_Photothermal_deflection_spectroscopy_and_detection)** - Foundational paper on PDS theory
- **[ScienceDirect: Photothermal Deflection Spectroscopy](https://www.sciencedirect.com/topics/physics-and-astronomy/photothermal-deflection-spectroscopy)** - Comprehensive technical overview

### Hardware Manuals

- **[SR865A Operation Manual (PDF)](https://www.thinksrs.com/downloads/pdfs/manuals/SR865Am.pdf)** - Full manual for the Stanford Research Systems SR865A lock-in amplifier
- **[SR865A Product Page](https://www.thinksrs.com/products/sr865a.html)** - Specifications, downloads, and application notes
- **[BK Precision 5490C Series User Manual (PDF)](https://bkpmedia.s3.amazonaws.com/downloads/manuals/en-us/5490C_Series_manual.pdf)** - Full manual for the BK Precision 5493C multimeter
- **[BK Precision 5493C Product Page](https://www.bkprecision.com/products/multimeters/5493CGPIB)** - Specifications and downloads
- **[Thorlabs BBD302 Product Page](https://www.thorlabs.com/thorproduct.cfm?partnumber=BBD302)** - 2-channel brushless DC motor controller
- **[Thorlabs BBD30x Kinesis User Manual](https://www.manualslib.com/manual/2841093/Thorlabs-Bbd301.html)** - Full manual for BBD301/BBD302/BBD303 controllers
- **[Thorlabs Kinesis Software](https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=Motion_Control)** - Required .NET SDK for stage control
