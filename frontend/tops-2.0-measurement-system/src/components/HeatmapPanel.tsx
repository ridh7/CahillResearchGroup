// src/components/HeatmapPanel.tsx
"use client"; // Keep for client-side rendering
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
  const [showHeatmap, setShowHeatmap] = useState<boolean>(false);
  const [heatmapData, setHeatmapData] = useState<Plotly.Data | null>(null);

  const handleCsvUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      Papa.parse<CsvRow>(file, {
        header: true,
        skipEmptyLines: true,
        complete: (result) => {
          const data = result.data;
          setCsvData(data);
          setShowHeatmap(false);
          setStatus("CSV uploaded successfully");
        },
        error: (error: Error) => {
          console.error("CSV parsing error:", error);
          setStatus("Error uploading CSV");
        },
      });
    }
  };

  const generateHeatmap = () => {
    if (csvData.length === 0) {
      setStatus("No CSV data uploaded");
      return;
    }

    // Extract and round PositionX and PositionY, keep Voltage(V) unrounded
    const xValues = csvData.map(
      (row) => Math.round(parseFloat(row.PositionX) * 100) / 100 // Round to 2 decimals
    );
    const yValues = csvData.map(
      (row) => Math.round(parseFloat(row.PositionY) * 100) / 100 // Round to 2 decimals
    );
    const zValues = csvData.map((row) => parseFloat(row["Voltage(V)"])); // No rounding

    // Filter out invalid data points
    const filteredData = xValues
      .map((x, i) => ({
        x,
        y: yValues[i],
        z: zValues[i],
      }))
      .filter((d) => !isNaN(d.x) && !isNaN(d.y) && !isNaN(d.z));

    // Get unique X and Y values for grid
    const uniqueX = [...new Set(filteredData.map((d) => d.x))].sort(
      (a, b) => a - b
    );
    const uniqueY = [...new Set(filteredData.map((d) => d.y))].sort(
      (a, b) => a - b
    );

    // Create 2D array for z-values
    const zGrid: number[][] = uniqueY.map(() => Array(uniqueX.length).fill(0));
    filteredData.forEach((point) => {
      const xIndex = uniqueX.indexOf(point.x);
      const yIndex = uniqueY.indexOf(point.y);
      zGrid[yIndex][xIndex] = point.z; // Use raw z value
    });

    // Scale z-values for better visualization (optional, adjust as needed)
    const displayZGrid = zGrid.map((row) => row.map((z) => z * 1e6)); // Convert to µV

    // Set heatmap data for Plotly
    const newHeatmapData: Plotly.Data = {
      z: displayZGrid,
      x: uniqueX,
      y: uniqueY,
      type: "heatmap",
      colorscale: "Viridis",
      zsmooth: false, // Disable smoothing for sharp cell edges
      showscale: true, // Show colorbar for reference
      hovertemplate: "X: %{x}<br>Y: %{y}<br>Voltage: %{z} µV<extra></extra>",
    };
    setHeatmapData(newHeatmapData);
    setShowHeatmap(true);
    setStatus("Heatmap generated");
  };

  return (
    <div className="bg-gray-800 p-4 rounded-lg flex flex-col h-full">
      <h2 className="text-white text-lg font-semibold mb-2">Heatmap</h2>
      <div className="flex space-x-4 mb-4">
        <input
          type="file"
          accept=".csv"
          onChange={handleCsvUpload}
          className="text-white"
        />
        <button
          onClick={generateHeatmap}
          className="bg-teal-500 text-white px-4 py-2 rounded hover:bg-teal-600"
        >
          Generate Heatmap
        </button>
      </div>
      {showHeatmap && heatmapData && (
        <Plot
          data={[heatmapData]}
          layout={{
            width: 400,
            height: 400,
            title: "Voltage Heatmap (µV)",
            xaxis: {
              title: "Position X",
              showgrid: true, // Show grid lines
              gridcolor: "white", // White grid lines for contrast
              gridwidth: 1,
            },
            yaxis: {
              title: "Position Y",
              showgrid: true, // Show grid lines
              gridcolor: "white", // White grid lines for contrast
              gridwidth: 1,
            },
            margin: { t: 50, r: 20, b: 50, l: 50 },
            plot_bgcolor: "black", // Dark background for contrast
            paper_bgcolor: "black",
          }}
          config={{ responsive: true }}
        />
      )}
    </div>
  );
}
