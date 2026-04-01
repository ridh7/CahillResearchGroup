'use client';

import { useMemo, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import type Plotly from 'plotly.js';
import { ScanDataPoint, FormData } from '../app/page';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface LiveScanPanelProps {
  scanData: ScanDataPoint[];
  formData: FormData;
  isProcessing: boolean;
}

/**
 * Bin a raw position into the nearest grid index.
 * Grid: start, start+step, start+2*step, ... up to end.
 */
function binIndex(pos: number, start: number, step: number): number {
  return Math.round((pos - start) / step);
}

/**
 * Build a grid axis: [start, start+step, start+2*step, ... end]
 */
function buildAxis(start: number, end: number, step: number): number[] {
  const dir = end >= start ? 1 : -1;
  const n = Math.round(Math.abs(end - start) / step);
  const axis: number[] = [];
  for (let i = 0; i <= n; i++) {
    axis.push(Math.round((start + i * step * dir) * 1e6) / 1e6);
  }
  return axis;
}

type BinAccum = { sum: number; count: number };

function parseTimestamp(ts: string): number {
  return new Date(ts).getTime();
}

const EXPORT_FORMATS = ['svg', 'png', 'jpeg', 'webp'] as const;
type ExportFormat = (typeof EXPORT_FORMATS)[number];

export default function LiveScanPanel({ scanData, formData, isProcessing }: LiveScanPanelProps) {
  const plotRef = useRef<HTMLDivElement>(null);
  const [exportFormat, setExportFormat] = useState<ExportFormat>('svg');

  const handleExport = () => {
    const plotDiv = plotRef.current?.querySelector('.js-plotly-plot') as HTMLElement | null;
    if (!plotDiv) return;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const PlotlyRuntime = (window as any).Plotly as typeof Plotly;
    if (!PlotlyRuntime) return;
    const { width, height } = plotDiv.getBoundingClientRect();
    PlotlyRuntime.downloadImage(plotDiv, {
      format: exportFormat,
      filename: `scan_heatmaps_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}`,
      width: Math.round(width),
      height: Math.round(height),
    });
  };
  const { currentRate, avgRate, elapsedSec } = useMemo(() => {
    const n = scanData.length;
    if (n < 2) return { currentRate: 0, avgRate: 0, elapsedSec: 0 };

    const tFirst = parseTimestamp(scanData[0].timestamp);
    const tLast = parseTimestamp(scanData[n - 1].timestamp);
    const totalSec = (tLast - tFirst) / 1000;
    const avg = totalSec > 0 ? (n - 1) / totalSec : 0;

    const window = Math.min(10, n - 1);
    const tWindow = parseTimestamp(scanData[n - 1 - window].timestamp);
    const windowSec = (tLast - tWindow) / 1000;
    const current = windowSec > 0 ? window / windowSec : 0;

    return { currentRate: current, avgRate: avg, elapsedSec: totalSec };
  }, [scanData]);

  // Parse coordinates
  const x1 = parseFloat(formData.x1) || 0;
  const x2 = parseFloat(formData.x2) || 0;
  const y1 = parseFloat(formData.y1) || 0;
  const y2 = parseFloat(formData.y2) || 0;

  // Compute step sizes — use step size fields directly, or derive from steps + range
  let xStep = parseFloat(formData.xStepSize) || 0;
  let yStep = parseFloat(formData.yStepSize) || 0;
  if (formData.movementMode === 'steps') {
    const xSteps = parseInt(formData.xSteps) || 0;
    const ySteps = parseInt(formData.ySteps) || 0;
    if (xSteps > 0 && xStep === 0) xStep = Math.abs(x2 - x1) / xSteps;
    if (ySteps > 0 && yStep === 0) yStep = Math.abs(y2 - y1) / ySteps;
  }

  // Signed steps — negative when scanning high→low, so binIndex works in both directions
  const xStepSigned = x2 >= x1 ? xStep : -xStep;
  const yStepSigned = y2 >= y1 ? yStep : -yStep;

  // Pre-compute grid axes
  const gridX = useMemo(() => (xStep > 0 ? buildAxis(x1, x2, xStep) : []), [x1, x2, xStep]);
  const gridY = useMemo(() => (yStep > 0 ? buildAxis(y1, y2, yStep) : []), [y1, y2, yStep]);

  // Build binned heatmap grids — average multiple readings per cell
  const heatmapTraces = useMemo(() => {
    if (scanData.length === 0 || gridX.length === 0 || gridY.length === 0) return [];

    const validPoints = scanData.filter(
      (p) =>
        p.positionX !== null &&
        p.positionY !== null &&
        !isNaN(p.X) &&
        !isNaN(p.Y) &&
        !isNaN(p.voltage)
    );
    if (validPoints.length === 0) return [];

    // Initialize accumulator grids: { sum, count } per cell
    const makeBinGrid = () => gridY.map(() => gridX.map((): BinAccum => ({ sum: 0, count: 0 })));
    const voltageBins = makeBinGrid();
    const xVBins = makeBinGrid();
    const yVBins = makeBinGrid();
    const ratioBins = makeBinGrid();
    const rBins = makeBinGrid();

    const xStart = gridX[0];
    const yStart = gridY[0];

    validPoints.forEach((p) => {
      const xi = binIndex(p.positionX as number, xStart, xStepSigned);
      const yi = binIndex(p.positionY as number, yStart, yStepSigned);
      if (xi >= 0 && xi < gridX.length && yi >= 0 && yi < gridY.length) {
        voltageBins[yi][xi].sum += p.voltage;
        voltageBins[yi][xi].count += 1;
        xVBins[yi][xi].sum += p.X;
        xVBins[yi][xi].count += 1;
        yVBins[yi][xi].sum += p.Y;
        yVBins[yi][xi].count += 1;
        if (p.Y !== 0 && isFinite(p.X / p.Y)) {
          ratioBins[yi][xi].sum += p.X / p.Y;
          ratioBins[yi][xi].count += 1;
        }
        const r = Math.sqrt(p.X * p.X + p.Y * p.Y);
        rBins[yi][xi].sum += r;
        rBins[yi][xi].count += 1;
      }
    });

    // Compute per-cell means first
    const toMeanGrid = (bins: BinAccum[][]): (number | null)[][] =>
      bins.map((row) => row.map((cell) => (cell.count > 0 ? cell.sum / cell.count : null)));

    const voltageMeans = toMeanGrid(voltageBins);
    const xVMeans = toMeanGrid(xVBins);
    const yVMeans = toMeanGrid(yVBins);
    const ratioMeans = toMeanGrid(ratioBins);
    const rMeans = toMeanGrid(rBins);

    // Compute global SD across all non-null cell means
    const globalSD = (means: (number | null)[][]): number => {
      const vals: number[] = [];
      means.forEach((row) =>
        row.forEach((v) => {
          if (v !== null) vals.push(v);
        })
      );
      if (vals.length < 2) return 0;
      const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
      const variance = vals.reduce((a, b) => a + (b - avg) ** 2, 0) / (vals.length - 1);
      return Math.sqrt(variance);
    };

    const voltageSD = globalSD(voltageMeans);
    const xVSD = globalSD(xVMeans);
    const yVSD = globalSD(yVMeans);
    const ratioSD = globalSD(ratioMeans);
    const rSD = globalSD(rMeans);

    // Compute global mean of all cell means
    const globalMean = (means: (number | null)[][]): number => {
      const vals: number[] = [];
      means.forEach((row) =>
        row.forEach((v) => {
          if (v !== null) vals.push(v);
        })
      );
      if (vals.length === 0) return 0;
      return vals.reduce((a, b) => a + b, 0) / vals.length;
    };

    const voltageMean = globalMean(voltageMeans);
    const xVMean = globalMean(xVMeans);
    const yVMean = globalMean(yVMeans);
    const ratioMean = globalMean(ratioMeans);
    const rMean = globalMean(rMeans);

    const makeTrace = (
      means: (number | null)[][],
      sd: number,
      mean: number,
      title: string,
      xaxis: string,
      yaxis: string,
      colorbarX: number,
      colorbarY: number,
      reverse?: boolean
    ): Plotly.Data => ({
      z: means,
      x: gridX,
      y: gridY,
      type: 'heatmap',
      colorscale: 'Greys',
      reversescale: reverse,
      zsmooth: false,
      showscale: true,
      connectgaps: false,
      zmin: mean - 2 * sd,
      zmax: mean + 2 * sd,
      hovertemplate: `X: %{x}<br>Y: %{y}<br>${title}: %{z:.4e}<extra></extra>`,
      xaxis,
      yaxis,
      colorbar: { title, x: colorbarX, y: colorbarY, len: 0.25, thickness: 15 },
    });

    // Row 1: X(V), Y(V) | Row 2: R, X/Y | Row 3: Voltage (centered)
    return [
      makeTrace(xVMeans, xVSD, xVMean, 'X(V)', 'x1', 'y1', 0.43, 0.87),
      makeTrace(yVMeans, yVSD, yVMean, 'Y(V)', 'x2', 'y2', 1.0, 0.87),
      makeTrace(rMeans, rSD, rMean, 'R (V)', 'x3', 'y3', 0.43, 0.53),
      makeTrace(ratioMeans, ratioSD, ratioMean, 'X/Y', 'x4', 'y4', 1.0, 0.53, true),
      makeTrace(voltageMeans, voltageSD, voltageMean, 'Voltage (V)', 'x5', 'y5', 0.72, 0.17),
    ];
  }, [scanData, gridX, gridY, xStepSigned, yStepSigned]);

  // Running strip chart: last N data points indexed by sample number (commented out)
  // const STRIP_WINDOW = 200;

  // Row 1: X(V), Y(V) | Row 2: R, X/Y | Row 3: Voltage (centered)
  const heatmapLayout: Partial<Plotly.Layout> = {
    title: isProcessing ? 'Live Scan' : 'Scan Complete',
    // Row 1: X(V), Y(V)
    xaxis: { domain: [0.05, 0.38], anchor: 'y' as const, showgrid: true, gridcolor: 'white' },
    yaxis: { domain: [0.73, 1], anchor: 'x' as const, showgrid: true, gridcolor: 'white' },
    xaxis2: { domain: [0.62, 0.95], anchor: 'y2', showgrid: true, gridcolor: 'white' },
    yaxis2: { domain: [0.73, 1], anchor: 'x2', showgrid: true, gridcolor: 'white' },
    // Row 2: R, X/Y
    xaxis3: { domain: [0.05, 0.38], anchor: 'y3', showgrid: true, gridcolor: 'white' },
    yaxis3: { domain: [0.39, 0.66], anchor: 'x3', showgrid: true, gridcolor: 'white' },
    xaxis4: { domain: [0.62, 0.95], anchor: 'y4', showgrid: true, gridcolor: 'white' },
    yaxis4: { domain: [0.39, 0.66], anchor: 'x4', showgrid: true, gridcolor: 'white' },
    // Row 3: Voltage (centered)
    xaxis5: { domain: [0.335, 0.665], anchor: 'y5', showgrid: true, gridcolor: 'white' },
    yaxis5: { domain: [0, 0.27], anchor: 'x5', showgrid: true, gridcolor: 'white' },
    margin: { t: 50, r: 75, b: 50, l: 75 },
    plot_bgcolor: 'black',
    paper_bgcolor: 'gray',
    annotations: [
      {
        text: 'X in-phase (V)',
        xref: 'paper',
        yref: 'paper',
        x: 0.215,
        y: 1.0,
        showarrow: false,
        font: { size: 13, color: 'white' },
        xanchor: 'center',
        yanchor: 'bottom',
      },
      {
        text: 'Y out-of-phase (V)',
        xref: 'paper',
        yref: 'paper',
        x: 0.785,
        y: 1.0,
        showarrow: false,
        font: { size: 13, color: 'white' },
        xanchor: 'center',
        yanchor: 'bottom',
      },
      {
        text: 'R = √(X² + Y²)',
        xref: 'paper',
        yref: 'paper',
        x: 0.215,
        y: 0.66,
        showarrow: false,
        font: { size: 13, color: 'white' },
        xanchor: 'center',
        yanchor: 'bottom',
      },
      {
        text: 'X/Y Ratio',
        xref: 'paper',
        yref: 'paper',
        x: 0.785,
        y: 0.66,
        showarrow: false,
        font: { size: 13, color: 'white' },
        xanchor: 'center',
        yanchor: 'bottom',
      },
      {
        text: 'Voltage (V)',
        xref: 'paper',
        yref: 'paper',
        x: 0.5,
        y: 0.28,
        showarrow: false,
        font: { size: 13, color: 'white' },
        xanchor: 'center',
        yanchor: 'bottom',
      },
    ],
  };

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-lg bg-gray-800 p-4">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">
          {isProcessing ? 'Live Scan' : 'Scan Results'}
        </h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-400">
            {scanData.length} points
            {isProcessing && currentRate > 0 && ` | ${currentRate.toFixed(1)} pts/sec`}
            {avgRate > 0 && ` | avg: ${avgRate.toFixed(1)} pts/sec`}
            {elapsedSec > 0 && ` | ${elapsedSec.toFixed(1)}s`}
          </span>
          {heatmapTraces.length > 0 && (
            <div className="flex items-center gap-1">
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
                className="rounded bg-gray-700 px-2 py-1 text-xs text-white"
              >
                {EXPORT_FORMATS.map((fmt) => (
                  <option key={fmt} value={fmt}>
                    {fmt.toUpperCase()}
                  </option>
                ))}
              </select>
              <button
                onClick={handleExport}
                className="rounded bg-teal-600 px-2 py-1 text-xs text-white hover:bg-teal-500"
              >
                Export
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Heatmaps — fixed height container to prevent layout shift */}
      <div ref={plotRef} style={{ height: 800, minHeight: 800 }}>
        {heatmapTraces.length > 0 ? (
          <Plot
            data={heatmapTraces}
            layout={{ ...heatmapLayout, height: 800, autosize: true }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%', height: '100%' }}
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <p className="text-gray-400">{isProcessing ? 'Waiting for scan data...' : 'No data'}</p>
          </div>
        )}
      </div>

      {/* Running strip chart — commented out for now */}
      {/*
      <div className="mt-4 rounded bg-gray-900 p-2" style={{ height: 190, minHeight: 190 }}>
        <div className="mb-1 flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-300">
            Live Signal Monitor (last {STRIP_WINDOW})
          </h3>
          <div className="flex gap-3 text-xs">
            <span className="text-teal-400">X(V)</span>
            <span className="text-orange-400">Y(V)</span>
            <span className="text-violet-400">Voltage</span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={155}>
          <LineChart data={stripData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="sample"
              tick={{ fill: '#9CA3AF', fontSize: 10 }}
              label={{ value: 'Sample #', fill: '#9CA3AF', fontSize: 10, dy: 10 }}
            />
            <YAxis
              yAxisId="lockin"
              tick={{ fill: '#9CA3AF', fontSize: 10 }}
              width={70}
              tickFormatter={(v: number) => v.toExponential(1)}
              label={{ value: 'X / Y (V)', fill: '#9CA3AF', fontSize: 10, angle: -90, dx: -25 }}
            />
            <YAxis
              yAxisId="voltage"
              orientation="right"
              tick={{ fill: '#9CA3AF', fontSize: 10 }}
              width={70}
              tickFormatter={(v: number) => v.toFixed(4)}
              label={{ value: 'Voltage (V)', fill: '#9CA3AF', fontSize: 10, angle: 90, dx: 25 }}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#1F2937', border: 'none', fontSize: 11 }}
              labelStyle={{ color: '#9CA3AF' }}
              formatter={(value: number, name: string) => [
                name === 'voltage' ? value.toFixed(6) : value.toExponential(4),
                name === 'xV' ? 'X(V)' : name === 'yV' ? 'Y(V)' : 'Voltage',
              ]}
              labelFormatter={(label: number) => `Sample ${label}`}
            />
            <Line yAxisId="lockin" type="monotone" dataKey="xV" stroke="#14b8a6" dot={false} strokeWidth={1.5} isAnimationActive={false} />
            <Line yAxisId="lockin" type="monotone" dataKey="yV" stroke="#f97316" dot={false} strokeWidth={1.5} isAnimationActive={false} />
            <Line yAxisId="voltage" type="monotone" dataKey="voltage" stroke="#a78bfa" dot={false} strokeWidth={1.5} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      */}
    </div>
  );
}
