# TOPS 2.0 Backend

FastAPI backend for the TOPS (Thermo-Optic Phase Spectroscopy) 2.0 measurement system, providing real-time instrument control, WebSocket streaming, and physics-based data analysis.

## Overview

This backend provides:

- **Instrument Control**: Direct communication with hardware via GPIB (General Purpose Interface Bus) / USB (PyVISA)
- **Real-Time Streaming**: WebSocket endpoints for live data
- **Data Acquisition**: Automated 2D scanning with continuous logging
- **Physics Analysis**: FD-PBD (Frequency-Domain Photothermal Beam Deflection) thermal property extraction

### Supported Instruments

- **Lock-in Amplifier**: Stanford Research Systems SR865A (GPIB/USB)
- **Digital Multimeter**: BK Precision 5493C (GPIB/USB)
- **Motorized Stage**: Thorlabs BBD302 2-channel brushless motor controller (.NET SDK)

## Tech Stack

| Category           | Technology                                 |
| ------------------ | ------------------------------------------ |
| **Framework**      | FastAPI                                    |
| **Language**       | Python 3.10+                               |
| **Validation**     | Pydantic                                   |
| **Instrument I/O** | PyVISA                                     |
| **.NET Bridge**    | pythonnet                                  |
| **Scientific**     | NumPy, SciPy, Matplotlib                   |
| **Code Quality**   | Ruff (format + lint), mypy (type checking) |
| **Git Hooks**      | Husky, lint-staged (configured in root)    |

## Getting Started

### Prerequisites

- **Python 3.10 or higher**
- **Hardware Instruments** (see Configuration section to customize):
  - SR865A Lock-in Amplifier (default USB Product ID: 3769)
  - BK Precision 5493C Multimeter (default serial: W114239033)
  - Thorlabs BBD302 Stage Controller (default serial: 103387864)
- **Thorlabs Kinesis Software**: Required for BBD302 .NET DLLs
  - Install from [Thorlabs Kinesis](https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=Motion_Control)
  - Default path: `C:\Program Files\Thorlabs\Kinesis\` (configurable via environment variables)
- **NI-VISA or Keysight IO Libraries**: Required by PyVISA as the low-level backend for GPIB/USB instrument communication (SR865A, BK5493C)
  - May already be installed if Thorlabs Kinesis or other instrument software is present
  - Check for existing installation at: `C:\Program Files\IVI Foundation\VISA\` or `C:\Program Files (x86)\IVI Foundation\VISA\`
  - If not installed, download [NI-VISA](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html) from National Instruments

### Installation

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv myenv

# Activate virtual environment
# Windows:
myenv\Scripts\activate
# Unix/MacOS:
source myenv/bin/activate

# Install dependencies (production and development)
pip install -e .
```

### Running the Server

```bash
# Start FastAPI server with auto-reload
uvicorn main:app --reload
```

The API will be available at:

- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **OpenAPI Spec**: http://localhost:8000/openapi.json

## Configuration

All hardware-specific settings (device IDs, DLL paths) are centralized in [app/config.py](app/config.py) using Pydantic Settings. This eliminates hardcoded values and enables environment-based configuration.

### Environment Variables

Override defaults by creating a `.env` file in the `backend/` directory (use [.env.example](.env.example) as template):

```bash
# Hardware Device Identifiers
TOPS_STAGE_SERIAL=103387864
TOPS_MULTIMETER_SERIAL=W114239033
TOPS_LOCKIN_PID=3769

# Thorlabs Kinesis Installation Path
TOPS_THORLABS_KINESIS_PATH=C:\Program Files\Thorlabs\Kinesis

# Data Directory (for storing measurement data files)
TOPS_DATA_DIRECTORY=./data

# CORS Origins (comma-separated list of allowed origins)
# Example for development: http://localhost:3000,http://localhost:3001
TOPS_CORS_ORIGINS=
```

**All settings are optional** — defaults in `config.py` match the current lab hardware. Only create a `.env` file if you need to customize values (e.g., different lab setup, different serial numbers).

### Configuration Files

- **[app/config.py](app/config.py)** — Settings class with defaults and computed properties (e.g., DLL paths)
- **[.env.example](.env.example)** — Template showing all available environment variables
- **`.env`** (git-ignored) — Your local overrides (create from `.env.example` if needed)

### Usage in Code

```python
from app.config import settings

# Hardware IDs auto-configured
if settings.lockin_pid in resource_string:
    connect_to_device(resource_string)

# DLL paths computed from base path
clr.AddReference(settings.kinesis_device_manager_dll)
```

## Architecture

### Project Structure

```
backend/
├── main.py                          # FastAPI app, lifespan, static file serving
├── .env.example                     # Environment variable template
├── app/
│   ├── config.py                    # Centralized configuration (Pydantic Settings)
│   │
│   ├── core/
│   │   ├── lockin.py                # SR865A lock-in amplifier driver
│   │   ├── multimeter.py            # BK Precision 5493C multimeter driver
│   │   ├── stage.py                 # Thorlabs BBD302 stage controller
│   │   ├── fdpbd_analysis.py        # FD-PBD fitting pipeline
│   │   ├── anisotropic_analysis.py  # Anisotropic thermal analysis
│   │   └── fdpbd/
│   │       ├── thermal_model.py     # Multilayer heat transfer solver
│   │       ├── fitting.py           # Nonlinear least-squares fitting
│   │       ├── integration.py       # Romberg numerical integration
│   │       └── data_processing.py   # Signal processing utilities
│   │
│   ├── routers/                     # FastAPI routers (domain-organized)
│   │   ├── stage.py                 # Stage control endpoints (10 endpoints)
│   │   ├── lockin.py                # Lock-in amplifier endpoints (5 endpoints)
│   │   ├── multimeter.py            # Multimeter endpoints (3 endpoints)
│   │   ├── analysis.py              # FD-PBD analysis endpoints (2 endpoints)
│   │   └── websockets.py            # WebSocket streaming endpoints (4 endpoints)
│   │
│   ├── dependencies.py              # FastAPI dependency injection functions
│   │
│   ├── models/
│   │   ├── state.py                 # Global state (instrument instances, thread pool)
│   │   ├── lockin.py                # Pydantic models for lock-in
│   │   ├── multimeter.py            # Pydantic models for multimeter
│   │   ├── stage.py                 # Pydantic models for stage
│   │   ├── fdpbd.py                 # Pydantic models for FD-PBD analysis
│   │   └── models.py                # Shared data models
│   │
│   └── utils/
│       ├── file_utils.py            # CSV saving with timestamps
│       └── file_upload.py           # File upload handling
│
├── data/                            # CSV output directory (auto-created)
└── pyproject.toml                   # Project config, dependencies, ruff/mypy settings
```

### Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
└───────────┬────────────────────────────────────┬─────────────┘
            │ HTTP POST (move, scan)             │ WebSocket
            ▼                                    ▼
┌─────────────────────┐              ┌──────────────────────────┐
│  REST API Routers   │              │  WebSocket Router        │
│  (domain-organized) │              │  (websockets.py)         │
│                     │              │                          │
│  - stage.py         │              │  - /ws/lockin            │
│  - lockin.py        │              │  - /ws/multimeter        │
│  - multimeter.py    │              │  - /ws/stage             │
│  - analysis.py      │              │  - /ws/scan_data         │
└──────────┬──────────┘              └──────────┬───────────────┘
           │                                    │
           │ Dependency Injection               │
           │ (dependencies.py)                  │
           ▼                                    ▼
    ┌────────────────────────────────────────────────────┐
    │           Global State (state.py)                  │
    │  - stage: ThorlabsBBD302                           │
    │  - lockin: SR865A                                  │
    │  - multimeter: BKPrecision5493C                    │
    │  - executor: ThreadPoolExecutor                    │
    │  - ws_* WebSocket connections                      │
    │  - latest_* cached values (thread-safe)            │
    │  - pause_* coordination flags (threading.Event)    │
    │  - scan_active, scan_generation, scan_data_queue   │
    └──────────┬─────────────────────────────────────────┘
               │
               ▼
    ┌────────────────────────────────────────────────────┐
    │          Hardware Instruments (PyVISA)             │
    │  - SR865A Lock-in (GPIB/USB)                       │
    │  - BK Precision 5493C Multimeter (GPIB/USB)        │
    │  - Thorlabs BBD302 Stage (.NET SDK via pythonnet)  │
    └────────────────────────────────────────────────────┘
```

## Key Components

### 1. Instrument Drivers

#### Lock-in Amplifier (`lockin.py`)

- **Device**: Stanford Research SR865A
- **Communication**: PyVISA (GPIB/USB)
- **Auto-detection**: Searches for `settings.lockin_pid` (default: "3769") in VISA resource string

**What it does**: A lock-in amplifier measures extremely weak AC signals buried in noise. It works by correlating the input signal with a known reference frequency — anything not at that exact frequency gets rejected. This is how the FD-PBD experiment detects tiny photothermal beam deflections.

**Readings**:

- **X (in-phase)**: The component of the signal in sync with the reference. Represents `amplitude × cos(phase)`.
- **Y (quadrature)**: The component 90° out of phase with the reference. Represents `amplitude × sin(phase)`.
- **Frequency**: The reference frequency the lock-in is locked to.
- From X and Y you can compute: signal amplitude = `√(X² + Y²)` and phase = `arctan(Y/X)`.

**Settings**:

- **Sensitivity** (codes 0–27): Sets the full-scale input range — the maximum signal level the instrument expects. Think of it like a volume knob on a microphone: if your signal is very weak (nanovolts), you need high sensitivity so the instrument amplifies it enough to measure. If set too low (e.g., 1V range for a nanovolt signal), you lose resolution. If set too high (e.g., 1nV range for a millivolt signal), the instrument overloads.
  - Code 0 = 1V full-scale (least sensitive, for large signals)
  - Code 27 = 1nV full-scale (most sensitive, for tiny signals)
  - Values follow a 1-2-5 sequence: 1V, 500mV, 200mV, 100mV, 50mV, ...down to 1nV
- **Time Constant** (codes 0–23): Controls how long the lock-in averages each measurement. A longer time constant means more averaging, which reduces random noise but makes the measurement respond more slowly to changes. Choose based on how fast your signal changes.
  - Code 0 = 1µs (fastest response, most noise)
  - Code 23 = 300ks (slowest response, cleanest signal)
  - Values follow a 1-3-10 sequence: 1µs, 3µs, 10µs, 30µs, 100µs, ...up to 300ks

#### Multimeter (`multimeter.py`)

- **Device**: BK Precision 5493C
- **Communication**: PyVISA (GPIB/USB)
- **Auto-detection**: Searches for `settings.multimeter_serial` (default: "W114239033") in VISA resource string

**What it does**: A digital multimeter measures voltage (and optionally current, resistance, etc.). In this setup, it reads DC voltage from the position-sensitive photodetector, which converts the probe laser beam's deflection into a voltage signal.

**Settings**:

- **NPLC — Number of Power Line Cycles** (valid values: 0.02, 0.2, 1, 10, 100): Controls how long the multimeter integrates (averages) each reading. The time is measured in cycles of the 60 Hz AC power line (~16.67ms per cycle). Why power line cycles? The biggest noise source in sensitive voltage measurements is 60 Hz mains interference from nearby power lines and equipment. Integrating for a whole number of power line cycles cancels this interference.
  - 0.02 NPLC ≈ 0.33ms → very fast readings, but noisy
  - 0.2 NPLC ≈ 3.3ms → good balance for scanning (current default)
  - 1 NPLC ≈ 16.7ms → cancels one full 60 Hz cycle of noise
  - 100 NPLC ≈ 1.67s → very clean readings, but slow
- **Terminal** (`"fron"` or `"rear"`): Selects which physical input jacks to read from. The multimeter has two sets of banana jack inputs — front panel and rear panel. Rear terminals (current default) are typically used when the instrument is rack-mounted or when cables are semi-permanently connected to avoid accidental disconnection.

**Default initialization**: On startup, the driver resets the multimeter, configures DC voltage mode, sets 0.2 NPLC, and selects rear terminals.

#### Motorized Stage (`stage.py`)

- **Device**: Thorlabs BBD302 (2-channel brushless motor controller)
- **Communication**: .NET DLLs via pythonnet (not PyVISA — uses Thorlabs' own SDK)
- **Auto-detection**: Searches for `settings.stage_serial` (default: "103387864")
- **DLL Loading**: Uses `settings.kinesis_*_dll` properties for DLL paths

**What it does**: Controls a motorized X-Y translation stage that physically moves the sample (or optics) to different positions. This is how the system performs 2D spatial scans — stepping through a grid of positions while recording lock-in and multimeter data at each point.

**Channels**: The BBD302 has 2 independent motor channels:

- **Channel 1** = X axis (horizontal movement)
- **Channel 2** = Y axis (vertical movement)

**Key concepts**:

- **Homing**: On startup, each axis drives to its limit switch (a physical end-stop) to establish an absolute zero reference. Without homing, the stage doesn't know where it is.
- **Polling**: The stage periodically reports its current position back to the software. Default polling rate is 250ms (4 updates/sec). During scans, this is increased to 1ms (1000 updates/sec) for higher spatial resolution.
- **Positioning**: Movements are commanded in millimeters using `Decimal` type for precision. Each `MoveTo` call blocks until the stage reaches its target (with a 60s timeout).

**Initialization sequence**:

1. Build device list from Thorlabs SDK
2. Connect to controller by serial number
3. For each channel: StartPolling(250ms) → EnableDevice → LoadMotorConfiguration → Home(60s timeout)

### 2. WebSocket Streaming

Four WebSocket endpoints provide real-time data streams:

- **`/ws/lockin`**: Lock-in X, Y, frequency
- **`/ws/multimeter`**: Multimeter voltage
- **`/ws/stage`**: Stage X, Y position
- **`/ws/scan_data`**: Live scan measurement points (queue-based, sends `{"type": "scan_complete"}` when done)

**Connection Management**:

- Only one client allowed per instrument (prevents bandwidth conflicts)
- Previous connection automatically closed when new client connects
- Data cached in `global_state` for synchronous access during scans

**VISA/GPIB Conflict Prevention**:

- Lock-in, multimeter, and stage readings paused during scans using `global_state.pause_*_reading` Event flags
- Prevents simultaneous GPIB/VISA queries which can cause communication errors
- Cached values in `global_state` used during pause

### 3. Data Acquisition Modes

Both scan modes are launched via `POST /start` which fires a daemon thread and returns immediately. Scan progress is streamed to the frontend via `/ws/scan_data`. The `scan_generation` counter prevents zombie scans when stopping and restarting rapidly.

#### Step-and-Measure (`move_in_rectangle`)

- Stage moves to each grid point, pauses, reads instruments, then moves to the next point
- Supports both steps and step-size input modes
- Bidirectional or unidirectional scan patterns
- Configurable delay between measurements
- **Output**: Timestamped CSV (`{sample_id}_tops2_YYYYMMDD_HHMMSS.csv`)

#### Continuous Scan (`continuous_scan`)

- Fast axis moves continuously while slow axis steps between sweeps
- Lock-in and multimeter are read in parallel via `ThreadPoolExecutor`
- Position gating: bin-based (`round((pos - grid_origin) / step_size)`) ensures one reading per grid cell
- Supports bidirectional and unidirectional patterns (with optional retrace recording)
- Configurable fast axis (X or Y)
- **Output**: Timestamped CSV (`{sample_id}_tops2_YYYYMMDD_HHMMSS.csv`)

**Scan Abort Mechanism**:

- `POST /stop` sets `scan_active = False` and calls `stage.stop()` on both channels
- `scan_generation` counter: each new scan increments the counter; old scan threads detect the mismatch via an `aborted()` closure and exit immediately
- `_safe_move_to()` retries `MoveTo` on `DeviceMovingException` with abort callback for fast exit
- Move threads use `join(timeout=2.0)` to cap wait time after SDK `Stop(0)` call

### 4. FD-PBD Analysis

**Physical Principle**:

Frequency-Domain Photothermal Beam Deflection (FD-PBD) measures thermal properties by:

1. Modulated pump laser heats sample → creates temperature oscillations
2. Temperature gradient → refractive index gradient in substrate
3. Probe laser beam deflects by angle ∝ ∇n (mirage effect)
4. Position-sensitive detector measures deflection vs. frequency

**Mathematical Model** (`thermal_model.py`):

- **Hankel Transform**: Solves 3D heat diffusion in cylindrical coordinates
- **Transfer Matrix Method**: Computes thermal Green's function G(k,ω) for multilayer samples
- **Beam Profiles**: Gaussian pump/probe overlap in Fourier space
- **Output**: Complex deflection angle θ(ω) = amplitude × e^(iφ)

**Fitting Pipeline** (`fdpbd_analysis.py`):

1. Load experimental data (in-phase, out-of-phase, frequency, sum voltage)
2. Apply leaking correction (frequency rolloff and phase delay compensation)
3. Nonlinear least-squares fit to extract:
   - Thermal conductivity (λ)
   - Thermo-optic coefficient (dn/dT)
4. Compute confidence intervals (95%)
5. Generate fit quality plots

**Endpoint**: `POST /fdpbd/analyze`

**Input**:

- Text file with columns: `in`, `out`, `freq`, `vSum`
- Material parameters (Poisson ratio, layer properties, beam radii)

**Output**:

- Fitted parameters with uncertainties
- Plots: in-phase fit, out-of-phase fit, combined fit

## Development Workflow

### Code Quality Tools

Pre-commit hooks (configured in root `.lintstagedrc.json`):

- **Ruff format**: Code formatter
- **Ruff check**: Linter + import sorter
- **mypy**: Static type checker

```bash
# Format code manually
ruff format .

# Lint and auto-fix
ruff check . --fix

# Check without fixing
ruff check .

# Type check
mypy app
```

### Adding New Instruments

1. **Create driver** in `app/core/`:

   ```python
   from app.config import settings
   import pyvisa

   class NewInstrument:
       """Driver for XYZ Instrument."""
       def __init__(self, resource_name=None):
           # Auto-detect using settings
           if resource_name is None:
               resources = self.rm.list_resources()
               for res in resources:
                   if settings.new_instrument_id in res:
                       resource_name = res
                       break
           # Connect, initialize
           pass

       def read_values(self):
           # Return dict of measurements
           pass
   ```

2. **Add configuration** in `app/config.py`:

   ```python
   class Settings(BaseSettings):
       new_instrument_id: str = "default_id"
   ```

3. **Add to global state** in `app/models/state.py`:

   ```python
   class GlobalState:
       new_instrument: NewInstrument | None = None
   ```

4. **Create dependency function** in `app/dependencies.py`:

   ```python
   def get_new_instrument() -> "NewInstrument":
       if global_state.new_instrument is None:
           raise HTTPException(status_code=503, detail="New instrument not initialized")
       return global_state.new_instrument
   ```

5. **Initialize in lifespan** (`main.py`):

   ```python
   @asynccontextmanager
   async def lifespan(app: FastAPI):
       global_state.new_instrument = NewInstrument()
       yield
       # Cleanup if needed
   ```

6. **Create router** in `app/routers/new_instrument.py`:

   ```python
   from fastapi import APIRouter, Depends
   from app.dependencies import get_new_instrument

   router = APIRouter()

   @router.get("/new_instrument/settings")
   async def get_settings(instrument: NewInstrument = Depends(get_new_instrument)):
       # Endpoint logic
       pass
   ```

7. **Create WebSocket endpoint** in `app/routers/websockets.py` (if needed):

   ```python
   @router.websocket("/ws/new_instrument")
   async def websocket_new_instrument(websocket: WebSocket):
       # Follow pattern from /ws/lockin
       pass
   ```

8. **Register router** in `main.py`:

   ```python
   from app.routers import new_instrument
   app.include_router(new_instrument.router, tags=["new_instrument"])
   ```

### Adding New Analysis Methods

1. Create analysis function in `app/core/`
2. Define Pydantic models in `app/models/`
3. Add endpoint in `app/routers/analysis.py` with proper type annotations
4. If creating a new analysis domain, create a new router file and register in `main.py`

## API Reference

All endpoints are organized by domain in separate routers. Visit http://localhost:8000/docs for interactive API documentation with automatic tagging by domain.

### Stage Control ([routers/stage.py](app/routers/stage.py))

- **`POST /move`**: Move to absolute (X, Y) position in mm
- **`POST /start`**: Unified scan endpoint — routes to step-and-measure or continuous scan based on `motion_type`. Runs in daemon thread, returns immediately.
- **`POST /stop`**: Immediately stop all stage motion and abort any running scan
- **`POST /home`**: Home specified channel (X, Y, or both)
- **`GET /get_movement_params`**: Get velocity and homing parameters
- **`POST /set_movement_params`**: Set velocity and homing parameters
- **`GET /get_current_position`**: Get current stage position
- **`GET /default-save-dir`**: Get backend's current working directory
- **`GET /choose-save-dir`**: Show native OS folder-picker dialog

### Lock-in Control ([routers/lockin.py](app/routers/lockin.py))

- **`GET /lockin/settings`**: Get current sensitivity, time constant, frequency, and filter slope
- **`POST /lockin/sensitivity`**: Increment/decrement sensitivity (codes 0-27)
- **`POST /lockin/time_constant`**: Increment/decrement time constant (codes 0-23)
- **`POST /lockin/frequency`**: Set reference frequency
- **`POST /lockin/filter_slope`**: Set output filter slope

### Multimeter Control ([routers/multimeter.py](app/routers/multimeter.py))

- **`GET /multimeter/settings`**: Get current aperture (NPLC) and terminal
- **`POST /multimeter/aperture`**: Set NPLC (0.02, 0.2, 1, 10, 100)
- **`POST /multimeter/terminal`**: Set terminal ('fron', 'rear')

### Analysis ([routers/analysis.py](app/routers/analysis.py))

- **`POST /fdpbd/analyze`**: FD-PBD thermal property extraction
- **`POST /fdpbd/analyze_anisotropy`**: Anisotropic FD-PBD analysis

### WebSockets ([routers/websockets.py](app/routers/websockets.py))

- **`WS /ws/lockin`**: Real-time lock-in X, Y, frequency stream
- **`WS /ws/multimeter`**: Real-time multimeter voltage stream
- **`WS /ws/stage`**: Real-time stage X, Y position stream
- **`WS /ws/scan_data`**: Live scan data points (queue-based, completes with `{"type": "scan_complete"}`)

## Troubleshooting

### Instrument Connection Issues

**Lock-in or Multimeter not found**:

- Verify USB connection
- Install NI-VISA or Keysight IO Libraries
- Check device identifiers match your hardware:
  - Lock-in: `TOPS_LOCKIN_PID` (default: "3769")
  - Multimeter: `TOPS_MULTIMETER_SERIAL` (default: "W114239033")
  - Override in `.env` file if your hardware differs
- Test with PyVISA:
  ```python
  import pyvisa
  rm = pyvisa.ResourceManager()
  print(rm.list_resources())  # Should show instrument
  ```

**Stage not found**:

- Verify USB connection
- Install Thorlabs Kinesis software
- Check configuration:
  - Serial number: `TOPS_STAGE_SERIAL` (default: "103387864")
  - DLL path: `TOPS_THORLABS_KINESIS_PATH` (default: `C:\Program Files\Thorlabs\Kinesis`)
  - Override in `.env` file if your hardware differs
- Verify DLLs exist at configured path

### Import Errors

**`E402: Module level import not at top of file` in stage.py**:

- This is intentional! pythonnet requires `clr.AddReference()` before imports
- Exception configured in `pyproject.toml`:
  ```toml
  [tool.ruff.lint.per-file-ignores]
  "app/core/stage.py" = ["E402", "F403", "F405"]
  ```

**`Import 'System' could not be resolved` in VS Code**:

- This is expected for pythonnet dynamic imports
- Runtime imports work correctly even if linter shows error
- Configure Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter" → `backend/myenv`

## Additional Resources

### Lock-in Amplifiers

- **[Lock-in Amplifier Fundamentals](https://www.allaboutcircuits.com/technical-articles/basic-fundamentals-of-lock-in-amplifiers/)** - Comprehensive introduction to lock-in detection
- **[Principles of Lock-in Detection (Zurich Instruments)](https://www.zhinst.com/europe/en/resources/principles-of-lock-in-detection)** - Detailed explanation of phase-sensitive detection
- **[Stanford Research Systems Application Note](https://www.thinksrs.com/downloads/pdfs/applicationnotes/AboutLIAs.pdf)** - "About Lock-In Amplifiers" technical guide
- **[Wikipedia: Lock-in Amplifier](https://en.wikipedia.org/wiki/Lock-in_amplifier)** - Overview and theory

### Digital Multimeter Concepts

- **[NPLC Explained (Tektronix)](https://www.tek.com/en/support/faqs/what-nplc-and-why-it-important)** - Number of Power Line Cycles fundamentals
- **[Adjusting NPLC for High-Speed Measurements (Keysight)](https://www.keysight.com/us/en/lib/resources/training-materials/adjusting-nplc-and-aperture-to-make-high-speed-measurements.html)** - Speed vs. accuracy tradeoffs
- **[Integration Time and Resolution](http://rfmw.em.keysight.com/bihelpfiles/BenchVue/_Latest/DMMApp/English/Content/Measurement/Integration%20Time%20and%20Resolution.htm)** - Keysight technical guide

### Thermal Conductivity Measurement

- **[Frequency Domain Thermoreflectance (FDTR)](https://www.nist.gov/publications/instrumentation-guide-measuring-thermal-conductivity-using-frequency-domain)** - NIST instrumentation guide
- **[FDTR Technique Overview (JOVE)](https://www.jove.com/t/68908/the-frequency-domain-thermoreflectance-technique-for-thermal-property)** - Video and protocol
- **[Thermal Conductivity Measurement (Wikipedia)](https://en.wikipedia.org/wiki/Thermal_conductivity_measurement)** - Overview of measurement methods

### Mathematical Methods

- **[Hankel Transform Tutorial](https://sci.uobasrah.edu.iq/images/Math/Hankel_Transforms_and_Their_Applications.pdf)** - Theory and applications in cylindrical coordinates
- **[Wikipedia: Hankel Transform](https://en.wikipedia.org/wiki/Hankel_transform)** - Mathematical foundations
- **[Transfer Matrix Method in Heat Transfer](https://www.sciencedirect.com/science/article/abs/pii/S0360544223016742)** - Novel TMM approach for thermal systems
- **[Matrix Analysis of Heat Transfer](https://www.sciencedirect.com/science/article/abs/pii/0016003257909274)** - Classic paper on matrix methods

### Optical Properties

- **[Thermo-optic Coefficient (dn/dT)](https://www.nature.com/articles/s41598-022-08232-x)** - Temperature dependence in semiconductors
- **[Position-Sensitive Detectors](https://www.rp-photonics.com/position_sensitive_detectors.html)** - Types and applications of beam deflection detectors
- **[Thorlabs: Position-Sensing Detectors](https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_ID=4400)** - Commercial detector overview
