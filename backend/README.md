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
- **Hardware Instruments**:
  - SR865A Lock-in Amplifier (serial number: USB-based, Product ID 3769)
  - BK Precision 5493C Multimeter (serial number: W114239033)
  - Thorlabs BBD302 Stage Controller (serial number: 103387864)
- **Thorlabs Kinesis Software**: Required for BBD302 .NET DLLs
  - Install from [Thorlabs Kinesis](https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=Motion_Control)
  - DLLs expected at: `C:\Program Files\Thorlabs\Kinesis\`
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
│  - /move_and_log    │              │                          │
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
- **Auto-detection**: Searches for USB Product ID "3769" in VISA resource string

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
- **Auto-detection**: Searches for serial number "W114239033" in VISA resource string

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
- **Auto-detection**: Searches for serial number "103387864"

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

Three WebSocket endpoints provide real-time data streams:

- **`/ws/lockin`**: Lock-in X, Y
- **`/ws/multimeter`**: Multimeter voltage
- **`/ws/stage`**: Stage X, Y position

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
- **Output**: Timestamped CSV (`Measurements_YYYYMMDD_HHMMSS.csv`) in the server's working directory

#### Bidirectional Continuous Scan (`move_and_log`)

- **Algorithm**:
  1. Increase stage polling to 1ms for high-resolution position tracking
  2. For each X step:
     - Scan Y upward (start_y → target_y) or downward (current_y → start_y)
     - Log instrument data continuously during Y movement (not pausing)
     - Capture: first point + continuous samples + end point
     - Reverse Y direction for next X
  3. Post-process: filter out-of-bounds and duplicate samples
- Endpoint: `POST /move_and_log`
- **Output**: Timestamped CSV (`Measurements_YYYYMMDD_HHMMSS.csv`) in the server's working directory

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
