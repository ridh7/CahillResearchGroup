"use client";

import React, { useEffect, useRef } from "react";
import { LockinData, MultimeterData, StageData } from "../app/page";

type HeatMapsPanelProps = {
  lockinData: LockinData;
  multimeterData: MultimeterData;
  stageData: StageData;
};

// Define grid resolution and cell size (in pixels)
const gridX = 111; // cells for x (0 to 110)
const gridY = 76; // cells for y (0 to 75)
const cellSize = 5; // each cell is 5x5 pixels

const HeatMapsPanel: React.FC<HeatMapsPanelProps> = ({
  lockinData,
  multimeterData,
  stageData,
}) => {
  // Canvas references for the four heat maps:
  const canvasXRef = useRef<HTMLCanvasElement>(null);
  const canvasYRef = useRef<HTMLCanvasElement>(null);
  const canvasRatioRef = useRef<HTMLCanvasElement>(null);
  const canvasMultiRef = useRef<HTMLCanvasElement>(null);

  // Use refs to hold the heat map grid data (2D arrays)
  // Each will be an array of gridY rows and gridX columns.
  const heatMapXRef = useRef<(number | null)[][]>([]);
  const heatMapYRef = useRef<(number | null)[][]>([]);
  const heatMapRatioRef = useRef<(number | null)[][]>([]);
  const heatMapMultiRef = useRef<(number | null)[][]>([]);

  // Initialize the heat map arrays once on mount:
  useEffect(() => {
    if (heatMapXRef.current.length === 0) {
      heatMapXRef.current = Array.from({ length: gridY }, () =>
        Array(gridX).fill(null)
      );
      heatMapYRef.current = Array.from({ length: gridY }, () =>
        Array(gridX).fill(null)
      );
      heatMapRatioRef.current = Array.from({ length: gridY }, () =>
        Array(gridX).fill(null)
      );
      heatMapMultiRef.current = Array.from({ length: gridY }, () =>
        Array(gridX).fill(null)
      );
    }
  }, []);

  // Whenever stageData, lockinData or multimeterData update, update the appropriate cell and redraw
  useEffect(() => {
    // Compute grid indices from stage data.
    // We assume stageData.x and stageData.y are in the proper range.
    const xIndex = Math.floor(stageData.x);
    const yIndex = Math.floor(stageData.y);
    if (xIndex < 0 || xIndex >= gridX || yIndex < 0 || yIndex >= gridY) {
      return;
    }

    // Update the heat map data for each measure:
    heatMapXRef.current[yIndex][xIndex] = lockinData.X;
    heatMapYRef.current[yIndex][xIndex] = lockinData.Y;
    heatMapRatioRef.current[yIndex][xIndex] =
      lockinData.Y !== 0 ? lockinData.X / lockinData.Y : 0;
    heatMapMultiRef.current[yIndex][xIndex] = multimeterData.value;

    // Redraw all canvases
    drawCanvas(canvasXRef.current, heatMapXRef.current);
    drawCanvas(canvasYRef.current, heatMapYRef.current);
    drawCanvas(canvasRatioRef.current, heatMapRatioRef.current);
    drawCanvas(canvasMultiRef.current, heatMapMultiRef.current);
  }, [stageData, lockinData, multimeterData]);

  // A simple draw function: loop through each cell and draw a rectangle.
  // Here we use a very simple grayscale mapping.
  const drawCanvas = (
    canvas: HTMLCanvasElement | null,
    data: (number | null)[][]
  ) => {
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    // Clear the canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // Loop over each cell in the grid
    for (let y = 0; y < gridY; y++) {
      for (let x = 0; x < gridX; x++) {
        const value = data[y][x];
        if (value != null) {
          // Normalize the value to a range between 0 and 1.
          // (Here we assume the measurement range roughly spans 0-10,
          // but you can adjust the max value as needed.)
          const norm = Math.max(0, Math.min(1, value / 10));
          // Map normalized value to a grayscale color.
          // Higher measurement = darker cell.
          const intensity = Math.floor(255 * (1 - norm));
          ctx.fillStyle = `rgb(${intensity}, ${intensity}, ${intensity})`;
          ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
        }
      }
    }
  };

  return (
    <div className="grid grid-cols-2 gap-4">
      <div>
        <h3 className="text-white text-center">Lockin X (V)</h3>
        <canvas
          ref={canvasXRef}
          width={gridX * cellSize}
          height={gridY * cellSize}
          className="border border-gray-600"
        />
      </div>
      <div>
        <h3 className="text-white text-center">Lockin Y (V)</h3>
        <canvas
          ref={canvasYRef}
          width={gridX * cellSize}
          height={gridY * cellSize}
          className="border border-gray-600"
        />
      </div>
      <div>
        <h3 className="text-white text-center">Lockin X/Y Ratio</h3>
        <canvas
          ref={canvasRatioRef}
          width={gridX * cellSize}
          height={gridY * cellSize}
          className="border border-gray-600"
        />
      </div>
      <div>
        <h3 className="text-white text-center">Multimeter Voltage (V)</h3>
        <canvas
          ref={canvasMultiRef}
          width={gridX * cellSize}
          height={gridY * cellSize}
          className="border border-gray-600"
        />
      </div>
    </div>
  );
};

export default HeatMapsPanel;
