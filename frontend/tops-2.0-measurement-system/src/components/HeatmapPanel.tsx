"use client";
import { useState } from "react";
import dynamic from "next/dynamic";
import Papa from "papaparse";

// Dynamically import Plot with SSR disabled
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

// Define the expected CSV row structure
interface CsvRow {
  Timestamp: string;
  PositionX: string;
  PositionY: string;
  "X(V)": string;
  "Y(V)": string;
  "Frequency(Hz)": string;
  "Voltage(V)": string;
}

// Define props for the component
interface HeatmapPanelProps {
  setStatus: (status: string) => void;
}

export default function HeatmapPanel({ setStatus }: HeatmapPanelProps) {
  const [csvData, setCsvData] = useState<CsvRow[]>([]);
  const [showHeatmaps, setShowHeatmaps] = useState<boolean>(false);
  const [heatmapData, setHeatmapData] = useState<Plotly.Data[]>([]);

  const handleCsvUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      Papa.parse<CsvRow>(file, {
        header: true,
        skipEmptyLines: true,
        complete: (result) => {
          const data = result.data;
          setCsvData(data);
          setShowHeatmaps(false);
          setStatus("CSV uploaded successfully");
        },
        error: (error: Error) => {
          console.error("CSV parsing error:", error);
          setStatus("Error uploading CSV");
        },
      });
    }
  };

  const generateHeatmaps = () => {
    if (csvData.length === 0) {
      setStatus("No CSV data uploaded");
      return;
    }

    // Extract and round PositionX and PositionY
    const xValues = csvData.map(
      (row) => Math.round(parseFloat(row.PositionX) * 10) / 10
    );
    const yValues = csvData.map(
      (row) => Math.round(parseFloat(row.PositionY) * 10) / 10
    );
    // Extract z-values for each heatmap
    const voltageValues = csvData.map((row) => parseFloat(row["Voltage(V)"]));
    const xVoltageValues = csvData.map((row) => parseFloat(row["X(V)"]));
    const yVoltageValues = csvData.map((row) => parseFloat(row["Y(V)"]));
    const ratioValues = csvData.map(
      (row) => parseFloat(row["X(V)"]) / parseFloat(row["Y(V)"])
    );

    // Filter out invalid data points
    const filteredData = xValues
      .map((x, i) => ({
        x,
        y: yValues[i],
        voltage: voltageValues[i],
        xVoltage: xVoltageValues[i],
        yVoltage: yVoltageValues[i],
        ratio: ratioValues[i],
      }))
      .filter(
        (d) =>
          !isNaN(d.x) &&
          !isNaN(d.y) &&
          !isNaN(d.voltage) &&
          !isNaN(d.xVoltage) &&
          !isNaN(d.yVoltage) &&
          !isNaN(d.ratio) &&
          isFinite(d.ratio)
      );

    if (filteredData.length === 0) {
      setStatus("No valid data points found");
      return;
    }

    // Get unique X and Y values for grid
    const uniqueX = [...new Set(filteredData.map((d) => d.x))].sort(
      (a, b) => a - b
    );
    const uniqueY = [...new Set(filteredData.map((d) => d.y))].sort(
      (a, b) => a - b
    );

    // Create 2D grids for each z-value type
    const voltageGrid: number[][] = uniqueY.map(() =>
      Array(uniqueX.length).fill(0)
    );
    const xVoltageGrid: number[][] = uniqueY.map(() =>
      Array(uniqueX.length).fill(0)
    );
    const yVoltageGrid: number[][] = uniqueY.map(() =>
      Array(uniqueX.length).fill(0)
    );
    const ratioGrid: number[][] = uniqueY.map(() =>
      Array(uniqueX.length).fill(0)
    );

    filteredData.forEach((point) => {
      const xIndex = uniqueX.indexOf(point.x);
      const yIndex = uniqueY.indexOf(point.y);
      voltageGrid[yIndex][xIndex] = point.voltage;
      xVoltageGrid[yIndex][xIndex] = point.xVoltage;
      yVoltageGrid[yIndex][xIndex] = point.yVoltage;
      ratioGrid[yIndex][xIndex] = point.ratio;
    });

    // Define heatmap data for each plot
    const heatmapVoltage: Plotly.Data = {
      z: voltageGrid,
      x: uniqueX,
      y: uniqueY,
      type: "heatmap",
      colorscale: "Greys",
      zsmooth: false,
      showscale: true,
      hovertemplate: "X: %{x}<br>Y: %{y}<br>Voltage: %{z} V<extra></extra>",
      xaxis: "x1",
      yaxis: "y1",
      colorbar: {
        title: "Voltage (µV)",
        x: 0.4,
        y: 0.8,
        len: 0.4,
        thickness: 20,
      },
    };

    const heatmapXVoltage: Plotly.Data = {
      z: xVoltageGrid,
      x: uniqueX,
      y: uniqueY,
      type: "heatmap",
      colorscale: "Greys",
      zsmooth: false,
      showscale: true,
      hovertemplate: "X: %{x}<br>Y: %{y}<br>X(V): %{z} V<extra></extra>",
      xaxis: "x2",
      yaxis: "y2",
      colorbar: {
        title: "X(V) (V)",
        x: 1.0,
        y: 0.8,
        len: 0.4,
        thickness: 20,
      },
    };

    const heatmapYVoltage: Plotly.Data = {
      z: yVoltageGrid,
      x: uniqueX,
      y: uniqueY,
      type: "heatmap",
      colorscale: "Greys",
      reversescale: true,
      zsmooth: false,
      showscale: true,
      hovertemplate: "X: %{y}<br>Y: %{y}<br>Y(V): %{z} V<extra></extra>",
      xaxis: "x3",
      yaxis: "y3",
      colorbar: {
        title: "Y(V) (V)",
        x: 0.4,
        y: 0.2,
        len: 0.4,
        thickness: 20,
      },
    };

    const heatmapRatio: Plotly.Data = {
      z: ratioGrid,
      x: uniqueX,
      y: uniqueY,
      type: "heatmap",
      colorscale: "Greys",
      reversescale: true,
      zsmooth: false,
      showscale: true,
      hovertemplate: "X: %{x}<br>Y: %{y}<br>X/Y Ratio: %{z}<extra></extra>",
      xaxis: "x4",
      yaxis: "y4",
      colorbar: {
        title: "X/Y Ratio",
        x: 1.0,
        y: 0.2,
        len: 0.4,
        thickness: 20,
      },
    };

    setHeatmapData([
      heatmapVoltage,
      heatmapXVoltage,
      heatmapYVoltage,
      heatmapRatio,
    ]);
    setShowHeatmaps(true);
    setStatus("Heatmaps generated");
  };

  return (
    <div className="bg-gray-800 p-4 rounded-lg flex flex-col h-full overflow-hidden">
      <h2 className="text-white text-lg font-semibold mb-2">Heatmaps</h2>
      <div className="flex space-x-4 mb-4">
        <input
          type="file"
          accept=".csv"
          onChange={handleCsvUpload}
          className="text-white"
        />
        <button
          onClick={generateHeatmaps}
          className="bg-teal-500 text-white px-4 py-2 rounded hover:bg-teal-600"
        >
          Generate Heatmaps
        </button>
      </div>
      {showHeatmaps && heatmapData.length > 0 && (
        <Plot
          data={heatmapData}
          layout={{
            title: "Voltage Heatmaps",
            grid: { rows: 2, columns: 2, pattern: "independent" },
            xaxis: {
              title: {
                text: "Position X",
                font: {
                  color: "black",
                },
                standoff: 5,
              },
              showgrid: true,
              gridcolor: "white",
              gridwidth: 1,
              domain: [0, 0.4],
            },
            yaxis: {
              title: {
                text: "Position Y",
                font: {
                  color: "black",
                },
              },
              showgrid: true,
              gridcolor: "white",
              gridwidth: 1,
              domain: [0.6, 1],
            },
            xaxis2: {
              title: {
                text: "Position X",
                font: {
                  color: "black",
                },
                standoff: 5,
              },
              showgrid: true,
              gridcolor: "white",
              gridwidth: 1,
              domain: [0.6, 1],
            },
            yaxis2: {
              title: {
                text: "Position Y",
                font: {
                  color: "black",
                },
              },
              showgrid: true,
              gridcolor: "white",
              gridwidth: 1,
              domain: [0.6, 1],
            },
            xaxis3: {
              title: {
                text: "Position X",
                font: {
                  color: "black",
                },
                standoff: 5,
              },
              showgrid: true,
              gridcolor: "white",
              gridwidth: 1,
              domain: [0, 0.4],
            },
            yaxis3: {
              title: {
                text: "Position Y",
                font: {
                  color: "black",
                },
              },
              showgrid: true,
              gridcolor: "white",
              gridwidth: 1,
              domain: [0, 0.4],
            },
            xaxis4: {
              title: {
                text: "Position X",
                font: {
                  color: "black",
                },
                standoff: 5,
              },
              showgrid: true,
              gridcolor: "white",
              gridwidth: 1,
              domain: [0.6, 1],
            },
            yaxis4: {
              title: {
                text: "Position Y",
                font: {
                  color: "black",
                },
              },
              showgrid: true,
              gridcolor: "black",
              gridwidth: 1,
              domain: [0, 0.4],
            },
            margin: { t: 50, r: 75, b: 50, l: 75 },
            plot_bgcolor: "black",
            paper_bgcolor: "gray",
            annotations: [
              
              {
                text: "Voltage (V)",
                xref: "paper",
                yref: "paper",
                x: 0.2, 
                y: 1.0,
                showarrow: false,
                font: { size: 14, color: "white" },
                xanchor: "center",
                yanchor: "bottom",
              },
              
              {
                text: "X in-phase (V)",
                xref: "paper",
                yref: "paper",
                x: 0.8, 
                y: 1.0, 
                showarrow: false,
                font: { size: 14, color: "white" },
                xanchor: "center",
                yanchor: "bottom",
              },
              
              {
                text: "Y out-of-phase (V)",
                xref: "paper",
                yref: "paper",
                x: 0.2, 
                y: 0.4, 
                showarrow: false,
                font: { size: 14, color: "white" },
                xanchor: "center",
                yanchor: "bottom",
              },
              
              {
                text: "X/Y Ratio",
                xref: "paper",
                yref: "paper",
                x: 0.8, 
                y: 0.4, 
                showarrow: false,
                font: { size: 14, color: "white" },
                xanchor: "center",
                yanchor: "bottom",
              },
            ],
          }}
          config={{ responsive: true, displayModeBar: false }}
        />
      )}
    </div>
  );
}
