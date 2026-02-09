# TOPS 2.0 Frontend

A Next.js dashboard for controlling real-time laboratory experiments measuring thermal properties of materials using TOPS (Thermo-Optic Phase Spectroscopy).

## Overview

This application provides a web-based interface for researchers to:

- Control and monitor three hardware instruments simultaneously (Lock-in Amplifier, Multimeter, Motorized Stage)
- Perform automated 2D spatial scanning of material samples
- Visualize measurement data with 2D spatial heatmaps from CSV uploads
- Analyze experimental data using physics-based models (FDPBD - Frequency-Domain Pump-Probe Buried Delay)

## Tech Stack

| Category            | Technology    |
| ------------------- | ------------- |
| **Framework**       | Next.js       |
| **UI Library**      | React         |
| **Language**        | TypeScript    |
| **Styling**         | Tailwind CSS  |
| **Data Viz**        | Plotly.js     |
|                     | Recharts      |
| **Animation**       | Framer Motion |
| **Data Processing** | PapaParse     |
| **Code Quality**    | ESLint        |
|                     | Prettier      |
| **Git Hooks**       | Husky         |
|                     | lint-staged   |

## Getting Started

### Prerequisites

- Node.js 14+ installed
- Backend server running on `localhost:8000` (FastAPI)
- Hardware instruments connected (Lock-in Amplifier, Multimeter, Motorized Stage)

### Installation

```bash
# Navigate to the project directory
cd frontend/tops-2.0-measurement-system

# Install dependencies
npm install
```

### Development Server

```bash
# Start the development server with Turbopack
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Building for Production

```bash
# Create optimized production build
npm run build

# Start production server
npm start
```

## Architecture

### Project Structure

```
src/
├── app/
│   ├── layout.tsx              # Root layout with global styles
│   ├── page.tsx                # Main dashboard (experiment control)
│   ├── globals.css             # Tailwind directives and global styles
│   └── fdpbd/
│       └── page.tsx            # Analysis page (physics-based fitting)
│
├── components/
│   ├── MetadataPanel.tsx       # Sample ID and comments input
│   ├── DeviceControls.tsx      # Tabbed controls (Stage/Lock-in/Multimeter)
│   ├── OutputPanel.tsx         # Device status displays and manual controls
│   ├── RealTimeGraphs.tsx      # Live line charts (Recharts)
│   ├── GraphsPanel.tsx         # Wrapper for RealTimeGraphs
│   ├── HeatmapPanel.tsx        # 2D heatmap generation from CSV (Plotly)
│   └── SettingsPanel.tsx       # Animated modal for stage motor configuration
│
├── next.config.ts             # Next.js configuration
├── tailwind.config.ts         # Tailwind theme customization
└── tsconfig.json              # TypeScript compiler options
```

### Application Routes

| Route    | Purpose                                                                      |
| -------- | ---------------------------------------------------------------------------- |
| `/`      | **Experiment Dashboard** - Real-time instrument control and data acquisition |
| `/fdpbd` | **Analysis Page** - Upload data files and run FDPBD analysis                 |

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   EXPERIMENT DASHBOARD (/)                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User configures experiment parameters                      │
│         ↓                                                   │
│  POST /start → Backend initializes measurement              │
│         ↓                                                   │
│  WebSocket connections established (3 channels):            │
│  • ws://localhost:8000/ws/lockin    → LockinData            │
│  • ws://localhost:8000/ws/multimeter → MultimeterData       │
│  • ws://localhost:8000/ws/stage      → StageData            │
│         ↓                                                   │
│  POST /move_and_log → Stage moves, logs data point          │
│         ↓                                                   │
│  User uploads CSV for post-processing                       │
│  • PapaParse extracts data                                  │
│  • HeatmapPanel generates 2D grids                          │
│  • Plotly renders 4 heatmaps (Voltage, X, Y, Ratio)         │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              ANALYSIS PAGE (/fdpbd)                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User uploads .txt data file                                │
│         ↓                                                   │
│  Configure 40+ physics parameters (with presets)            │
│         ↓                                                   │
│  Select isotropy or anisotropy model                        │
│         ↓                                                   │
│  POST /fdpbd/analyze (or analyze_anisotropy)                │
│         ↓                                                   │
│  Backend runs physics simulation & model fitting            │
│         ↓                                                   │
│  Display results (thermal conductivity, frequencies)        │
│         ↓                                                   │
│  Plotly renders fitted vs experimental data graphs          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### MetadataPanel

Simple input form for sample identification and experiment comments. Data is included with measurement start requests.

### DeviceControls

Tabbed interface for configuring three instruments:

- **Stage Tab**: Scan bounds (X/Y min/max), step sizes, delay parameters
- **Lock-in Tab**: Sensitivity, time constant, frequency settings
- **Multimeter Tab**: Aperture time, measurement mode selection

Includes detailed tooltips explaining units and valid ranges.

### OutputPanel

Displays real-time status for each instrument:

- Connection indicators (green = connected, red = disconnected)
- Current readings from Lock-in (X, Y, Frequency) and Multimeter (Voltage)
- Connect/Disconnect buttons for each WebSocket channel
- Manual stage control (Move & Log button)

### HeatmapPanel

Generates 2D spatial heatmaps from uploaded CSV files:

- Algorithm: Converts 1D CSV data (X, Y, Z columns) to 2D grids
- Creates 4 simultaneous heatmaps: Voltage, X-Voltage, Y-Voltage, X/Y Ratio
- Uses Plotly for interactive visualization (zoom, pan, hover tooltips)
- Handles floating-point precision issues with coordinate rounding

### SettingsPanel

Animated modal (Framer Motion) for configuring stage motor parameters:

- Channel 1 & 2 settings: Homing velocity, max velocity, acceleration
- Persists settings to backend via POST /settings

## Development Workflow

### Available Scripts

| Command                | Description                             |
| ---------------------- | --------------------------------------- |
| `npm run dev`          | Start development server with Turbopack |
| `npm run build`        | Create production build                 |
| `npm start`            | Run production server                   |
| `npm run lint`         | Run ESLint on codebase                  |
| `npm run lint:fix`     | Run ESLint with auto-fix                |
| `npm run format`       | Format all files with Prettier          |
| `npm run format:check` | Check formatting without modifying      |

### Code Quality Automation

**Format on Save (VS Code)**:

- Files are automatically formatted with Prettier when you save (Ctrl+S)
- ESLint auto-fixes are applied on save
- Configured via `.vscode/settings.json`

**Pre-commit Hooks (Husky + lint-staged)**:

- Runs automatically on `git commit`
- Executes ESLint --fix and Prettier --write on staged files
- Blocks commit if unfixable errors exist
- Ensures code quality before it enters the repository

### Code Style Guidelines

- **Formatting**: Enforced by Prettier (single quotes, semicolons, 100 char width)
- **Linting**: ESLint with Next.js and TypeScript rules
- **Tailwind Class Order**: Automatically sorted by prettier-plugin-tailwindcss
- **Comments**: Minimal - only for complex logic (see inline comments in code)

## WebSocket Integration

### Connection Lifecycle

Each WebSocket follows a state machine to handle rapid connect/disconnect:

**States**:

- `CONNECTING` - Connection in progress (attach handlers, wait)
- `OPEN` - Connected (reuse existing connection)
- `CLOSING` - Disconnect initiated (wait for completion)
- `CLOSED` - Disconnected (cleanup and allow reconnect)

**Prevents**:

- Duplicate connections when user clicks rapidly
- Memory leaks from unclosed connections
- Race conditions during state transitions

### Environment Variables

Create a `.env.local` file (optional) to override defaults:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Troubleshooting

### WebSocket Connection Errors

**Issue**: "WebSocket failed to connect"

**Solutions**:

- Verify backend server is running on `localhost:8000`
- Check that instruments are powered on and connected
- Inspect browser console for detailed error messages

### CSV Upload Fails

**Issue**: "No valid data points found"

**Solutions**:

- Ensure CSV has columns: `PositionX`, `PositionY`, `Voltage(V)`, `X(V)`, `Y(V)`
- Check for NaN or Infinity values in data
- Verify numeric data (not text)

### Pre-commit Hook Blocks Commit

**Issue**: Husky blocks git commit with ESLint errors

**Solutions**:

- Run `npm run lint:fix` to auto-fix issues
- Manually fix remaining errors shown in output
- Use `git commit --no-verify` only in emergencies (not recommended)

## Additional Resources

See the [root README](../../README.md) for scientific concept references and hardware manuals, and the [backend README](../../backend/README.md) for detailed resources on lock-in amplifiers, NPLC, thermal conductivity measurement, and the mathematical methods used in the FD-PBD analysis.
