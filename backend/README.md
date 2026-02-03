# TOPS 2.0 Backend

FastAPI backend for the TOPS 2.0 measurement system, providing real-time instrument control, WebSocket streaming, and physics-based data analysis.

## Overview

This backend provides:

- **Instrument Control**: Direct communication with hardware via GPIB/USB (PyVISA)
- **Real-Time Streaming**: WebSocket endpoints for live data at ~200Hz
- **Data Acquisition**: Automated 2D scanning with continuous logging
- **Physics Analysis**: FD-PBD (Frequency-Domain Photothermal Beam Deflection) thermal property extraction

### Supported Instruments

- **Lock-in Amplifier**: Stanford Research Systems SR865A (GPIB/USB)
- **Digital Multimeter**: BK Precision 5493C (GPIB/USB)
- **Motorized Stage**: Thorlabs BBD302 2-channel brushless motor controller (.NET SDK)

## Tech Stack

| Category            | Technology       |
| ------------------- | ---------------- |
| **Framework**       | FastAPI          |
| **Language**        | Python 3.10+     |
| **Validation**      | Pydantic         |
| **Instrument I/O**  | PyVISA           |
| **.NET Bridge**     | pythonnet        |
| **Scientific**      | NumPy, SciPy, Matplotlib |
| **Code Quality**    | Ruff (format + lint), mypy (type checking) |
| **Git Hooks**       | Husky, lint-staged (configured in root) |

## Getting Started

### Prerequisites

- **Python 3.10 or higher**
- **Hardware Instruments**:
  - SR865A Lock-in Amplifier (serial number: USB-based, PID 3769)
  - BK Precision 5493C Multimeter (serial number: W114239033)
  - Thorlabs BBD302 Stage Controller (serial number: 103387864)
- **Thorlabs Kinesis Software**: Required for BBD302 .NET DLLs
  - Install from [Thorlabs Kinesis](https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=Motion_Control)
  - DLLs expected at: `C:\Program Files\Thorlabs\Kinesis\`
- **NI-VISA or Keysight IO Libraries**: For GPIB/USB instrument communication

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
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **OpenAPI Spec**: http://localhost:8000/openapi.json

## Architecture

### Project Structure

```
backend/
├── main.py                          # FastAPI app, WebSocket endpoints, lifespan
├── app/
│   ├── core/
│   │   ├── lockin.py                # SR865A lock-in amplifier driver
│   │   ├── multimeter.py            # BK Precision 5493C multimeter driver
│   │   ├── stage.py                 # Thorlabs BBD302 stage controller
│   │   ├── shared_state.py          # Thread-safe data cache
│   │   ├── fdpbd_analysis.py        # FD-PBD fitting pipeline
│   │   ├── anisotropic_analysis.py  # Anisotropic thermal analysis
│   │   └── fdpbd/
│   │       ├── thermal_model.py     # Multilayer heat transfer solver
│   │       ├── fitting.py           # Nonlinear least-squares fitting
│   │       ├── integration.py       # Romberg numerical integration
│   │       └── data_processing.py   # Signal processing utilities
│   │
│   ├── routers/
│   │   └── endpoints.py             # REST API endpoints
│   │
│   ├── models/
│   │   ├── state.py                 # Global state (instrument instances, typed)
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
│  REST API Endpoints │              │  WebSocket Endpoints     │
│  (endpoints.py)     │              │  (/ws/lockin,            │
│                     │              │   /ws/multimeter,        │
│  - /move            │              │   /ws/stage)             │
│  - /start           │              │                          │
│  - /move_and_log    │              │  Streams at ~200Hz       │
│  - /fdpbd/analyze   │              └──────────┬───────────────┘
└──────────┬──────────┘                         │
           │                                    │
           ▼                                    ▼
    ┌────────────────────────────────────────────────────┐
    │           Global State (global_state.py)           │
    │  - stage: ThorlabsBBD302                           │
    │  - lockin: SR865A                                  │
    │  - multimeter: BKPrecision5493C                    │
    └──────────┬─────────────────────────────────────────┘
               │
               ▼
    ┌────────────────────────────────────────────────────┐
    │        Shared State (shared_state.py)              │
    │  Thread-safe cache for latest values:              │
    │  - latest_lockin_values                            │
    │  - latest_multimeter_value                         │
    │  - latest_stage_values                             │
    │  - pause_lockin_reading (Event)                    │
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
- **Features**:
  - Reads X, Y (in-phase, quadrature) components and reference frequency
  - Configurable sensitivity (1V to 1nV full-scale)
  - Configurable time constant (1µs to 300ks integration time)
- **Auto-detection**: Searches for USB PID "3769"

#### Multimeter (`multimeter.py`)

- **Device**: BK Precision 5493C
- **Communication**: PyVISA (GPIB/USB)
- **Features**:
  - DC voltage measurement (default)
  - Configurable NPLC (0.02 to 100 power line cycles)
    - Lower NPLC = faster, noisier (0.02 NPLC ≈ 0.33ms @ 60Hz)
    - Higher NPLC = slower, cleaner (100 NPLC ≈ 1.67s @ 60Hz)
  - Front/rear terminal selection
- **Auto-detection**: Searches for serial "W114239033"

#### Motorized Stage (`stage.py`)

- **Device**: Thorlabs BBD302 (2-channel brushless motor controller)
- **Communication**: .NET DLLs via pythonnet
- **Features**:
  - 2-axis (X, Y) positioning with 1µm resolution
  - Automatic homing on initialization (finds limit switches)
  - Bidirectional zigzag scanning for 2D data acquisition
- **Initialization Sequence**:
  1. Build device list from Thorlabs SDK
  2. Connect to controller
  3. For each channel: StartPolling(250ms) → EnableDevice → LoadMotorConfiguration → Home(60s timeout)
- **Auto-detection**: Searches for serial "103387864"

### 2. WebSocket Streaming

Three WebSocket endpoints provide real-time data streams:

- **`/ws/lockin`**: Lock-in X, Y, frequency at ~200Hz (5ms interval)
- **`/ws/multimeter`**: Multimeter voltage at ~200Hz
- **`/ws/stage`**: Stage X, Y position at ~200Hz

**Connection Management**:

- Only one client allowed per instrument (prevents bandwidth conflicts)
- Previous connection automatically closed when new client connects
- Data cached in `shared_state` for synchronous access during scans

**GPIB Conflict Prevention**:

- Lock-in reading paused during stage scans using `shared_state.pause_lockin_reading` Event flag
- Prevents simultaneous GPIB queries which can cause communication errors
- Cached values in `shared_state` used during pause

### 3. Data Acquisition Modes

#### Legacy Grid Scan (`move_in_rectangle`)

- Unidirectional scanning with fixed pause at each point
- Endpoint: `POST /start`
- Closes WebSocket connections after completion
- **Use case**: Simple grid measurements with precise timing

#### Bidirectional Continuous Scan (`move_and_log`)

- **Algorithm**:
  1. Increase stage polling to 1ms for high-resolution position tracking
  2. For each X step:
     - Scan Y upward (start_y → target_y) or downward (current_y → start_y)
     - Log instrument data continuously during Y movement (not pausing)
     - Capture: first point + continuous samples + end point
     - Reverse Y direction for next X (bidirectional = 50% faster)
  3. Post-process: filter out-of-bounds and duplicate samples
- Endpoint: `POST /move_and_log`
- **Advantages**:
  - ~50% faster than unidirectional (no Y-axis return moves)
  - Higher spatial resolution (continuous sampling during motion)
  - Better for time-sensitive experiments
- **Output**: Timestamped CSV in `data/` directory

**Data Synchronization**:

- Stage movement runs in separate thread
- Main thread polls position and logs data at specified `sample_rate`
- Instrument values read from `shared_state` cache (populated by WebSocket streams)
- Thread-safe access via `shared_state.value_lock`

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

1. Load experimental data (frequency, in-phase, out-of-phase signals)
2. Subtract baseline (DC offset correction)
3. Nonlinear least-squares fit to extract:
   - Thermal conductivity (λ)
   - Thermo-optic coefficient (dn/dT)
4. Compute confidence intervals (95%)
5. Generate fit quality plots

**Endpoint**: `POST /fdpbd/analyze`

**Input**:

- CSV file with columns: `freq`, `in`, `out`
- Material parameters (Poisson ratio, layer properties, beam radii)

**Output**:

- Fitted parameters with uncertainties
- Plots: in-phase fit, out-of-phase fit, combined fit

## Development Workflow

### Code Quality Tools

Pre-commit hooks (configured in root `.lintstagedrc.json`):

- **Ruff format**: Code formatter (88 char line length)
- **Ruff check**: Linter + import sorter (pycodestyle + pyflakes + isort)
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
   import pyvisa

   class NewInstrument:
       """Driver for XYZ Instrument."""
       def __init__(self, resource_name=None):
           # Auto-detect, connect, initialize
           pass

       def read_values(self):
           # Return dict of measurements
           pass
   ```

2. **Add to global state** in `app/models/state.py`:

   ```python
   class GlobalState:
       new_instrument: Optional[NewInstrument] = None
   ```

3. **Initialize in lifespan** (`main.py`):

   ```python
   @asynccontextmanager
   async def lifespan(app: FastAPI):
       global_state.new_instrument = NewInstrument()
       yield
       # Cleanup if needed
   ```

4. **Create WebSocket endpoint** (if needed):

   ```python
   @app.websocket("/ws/new_instrument")
   async def websocket_new_instrument(websocket: WebSocket):
       # Follow pattern from /ws/lockin
       pass
   ```

5. **Add REST endpoints** in `app/routers/endpoints.py`

### Adding New Analysis Methods

1. Create analysis function in `app/core/`
2. Define Pydantic models in `app/models/`
3. Add endpoint in `app/routers/endpoints.py` with proper type annotations and None guards

## API Reference

### Stage Control

- **`POST /move`**: Move to absolute (X, Y) position in mm
- **`POST /start`**: Unidirectional grid scan (legacy)
- **`POST /move_and_log`**: Bidirectional continuous scan
- **`POST /home`**: Home specified channel

### Lock-in Control

- **`POST /lockin/sensitivity`**: Set sensitivity (code 0-27)
- **`POST /lockin/time_constant`**: Set time constant (code 0-23)
- **`GET /lockin/settings`**: Get current settings

### Multimeter Control

- **`POST /multimeter/aperture`**: Set NPLC (0.02, 0.2, 1, 10, 100)
- **`POST /multimeter/terminal`**: Set terminal ('fron', 'rear')
- **`GET /multimeter/settings`**: Get current settings

### Analysis

- **`POST /fdpbd/analyze`**: FD-PBD thermal property extraction
- **`POST /anisotropic_fdpbd/analyze`**: Anisotropic FD-PBD analysis

### WebSocket Streams

- **`/ws/lockin`**: X, Y, frequency at ~200Hz
- **`/ws/multimeter`**: Voltage at ~200Hz
- **`/ws/stage`**: X, Y position at ~200Hz

## Troubleshooting

### Instrument Connection Issues

**Lock-in or Multimeter not found**:

- Verify USB connection
- Install NI-VISA or Keysight IO Libraries
- Check device serial number in driver code
- Test with PyVISA:
  ```python
  import pyvisa
  rm = pyvisa.ResourceManager()
  print(rm.list_resources())  # Should show instrument
  ```

**Stage not found**:

- Verify USB connection
- Install Thorlabs Kinesis software
- Check DLL paths in `stage.py` (default: `C:\Program Files\Thorlabs\Kinesis\`)
- Verify serial number: `103387864`

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

### Data Acquisition Issues

**WebSocket disconnects during scan**:

- This is intentional for `/start` endpoint (legacy mode)
- Use `/move_and_log` if you need continuous streaming

**Stage position jumps or jitters**:

- Check for mechanical obstructions
- Verify homing completed successfully on startup
- Increase polling interval if CPU overloaded

**Lock-in reads zero during scan**:

- Check `shared_state.pause_lockin_reading` flag
- Should only pause during old grid scan mode
- Bidirectional scan uses cached values instead

**GPIB timeout errors**:

- Reduce WebSocket streaming rate (increase `await asyncio.sleep(0.005)`)
- Use GPIB analyzer to check for bus conflicts
- Ensure only one client per instrument (WebSocket limit)

### Analysis Errors

**FD-PBD fit does not converge**:

- Check baseline correction (in-phase/out-of-phase offsets)
- Verify frequency range matches thermal response
- Adjust initial guess `x_guess` and bounds `lb`, `ub`
- Increase `dec_digits` in Romberg integration (accuracy vs. speed trade-off)

**Unphysical results (negative thermal conductivity)**:

- Review beam radii `r_pump`, `r_probe` (must match experiment)
- Check layer thickness `h_down` (substrate usually semi-infinite)
- Verify material parameters (Poisson ratio, volumetric heat capacity)

## Contributing

1. Create feature branch from `main`
2. Make changes with descriptive commits
3. Pre-commit hooks will run automatically (Black + Ruff)
4. Push and create pull request

## License

Internal research tool for Cahill Research Group.
