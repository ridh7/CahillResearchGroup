import { useState } from "react";
import { LockinData, MultimeterData, StageData } from "../app/page";

type OutputPanelProps = {
  lockinData: LockinData;
  multimeterData: MultimeterData;
  stageData: StageData;
  lockinConnected: boolean;
  multimeterConnected: boolean;
  stageConnected: boolean;
  connectLockin: () => void;
  disconnectLockin: () => void;
  connectMultimeter: () => void;
  disconnectMultimeter: () => void;
  connectStage: () => void;
  disconnectStage: () => void;
  resetLockin: () => void;
  resetMultimeter: () => void;
  resetStage: () => void;
  isProcessing: boolean;
};

export default function OutputPanel({
  lockinData,
  multimeterData,
  stageData,
  lockinConnected,
  multimeterConnected,
  stageConnected,
  connectLockin,
  disconnectLockin,
  connectMultimeter,
  disconnectMultimeter,
  connectStage,
  disconnectStage,
  resetLockin,
  resetMultimeter,
  resetStage,
  isProcessing,
}: OutputPanelProps) {
  const [moveX, setMoveX] = useState("");
  const [moveY, setMoveY] = useState("");

  const handleMove = async () => {
    try {
      const response = await fetch("http://localhost:8000/move_and_log", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          x: parseFloat(moveX),
          y: parseFloat(moveY),
          x_step_size: 1,
          sample_rate: 0.01,
        }),
      });
      const data = await response.json();
      if (data.status === "success") {
        console.log("Move and logging successful:", data.message);
        setMoveX("");
        setMoveY("");
      } else {
        console.error("Move and loggin failed:", data.message);
      }
    } catch (error) {
      console.error("Error during move and loggin:", error);
    }
  };

  const isMoveValid =
    moveX !== "" &&
    moveY !== "" &&
    !isNaN(parseFloat(moveX)) &&
    !isNaN(parseFloat(moveY)) &&
    parseFloat(moveX) >= 0 &&
    parseFloat(moveX) <= 110 &&
    parseFloat(moveY) >= 0 &&
    parseFloat(moveY) <= 75;

  return (
    <div className="w-1/5 bg-gray-800 p-4 rounded-lg shadow-lg space-y-6">
      {/* Lock-in Amplifier */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-white text-lg font-semibold">
            Lock-in Amplifier
          </h2>
          <div className="flex gap-2">
            <button
              onClick={connectLockin}
              disabled={lockinConnected || isProcessing}
              className={`p-1 ${
                lockinConnected || isProcessing
                  ? "text-gray-500"
                  : "text-teal-500 hover:text-teal-400"
              }`}
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 4.5c-3.03 0-5.5 2.47-5.5 5.5s2.47 5.5 5.5 5.5 5.5-2.47 5.5-5.5-2.47-5.5-5.5-5.5zm-1 8.5v-6l4 3-4 3z" />
              </svg>
            </button>
            <button
              onClick={disconnectLockin}
              disabled={!lockinConnected || isProcessing}
              className={`p-1 ${
                !lockinConnected || isProcessing
                  ? "text-gray-500"
                  : "text-red-500 hover:text-red-400"
              }`}
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 4.5c-3.03 0-5.5 2.47-5.5 5.5s2.47 5.5 5.5 5.5 5.5-2.47 5.5-5.5-2.47-5.5-5.5-5.5zm-1 8.5v-6h2v6h-2z" />
              </svg>
            </button>
            <button
              onClick={resetLockin}
              className="p-1 text-yellow-500 hover:text-yellow-400"
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 4C6.686 4 4 6.686 4 10c0 3.314 2.686 6 6 6 2.608 0 4.827-1.664 5.65-4h-1.717C13.237 13.635 11.723 15 10 15c-2.757 0-5-2.243-5-5s2.243-5 5-5c1.408 0 2.685.586 3.593 1.526L12 8h4V4l-1.703 1.703C13.185 4.651 11.684 4 10 4z" />
              </svg>
            </button>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <span className="text-gray-400">X:</span>
          <span className="text-white">
            {lockinData.X} {lockinData.unit}
          </span>
          <span className="text-gray-400">Y:</span>
          <span className="text-white">
            {lockinData.Y} {lockinData.unit}
          </span>
          <span className="text-gray-400">Freq:</span>
          <span className="text-white">
            {lockinData.frequency.toFixed(2)} Hz
          </span>
        </div>
      </div>

      {/* Multimeter */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-white text-lg font-semibold">Multimeter</h2>
          <div className="flex gap-2">
            <button
              onClick={connectMultimeter}
              disabled={multimeterConnected || isProcessing}
              className={`p-1 ${
                multimeterConnected || isProcessing
                  ? "text-gray-500"
                  : "text-teal-500 hover:text-teal-400"
              }`}
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 4.5c-3.03 0-5.5 2.47-5.5 5.5s2.47 5.5 5.5 5.5 5.5-2.47 5.5-5.5-2.47-5.5-5.5-5.5zm-1 8.5v-6l4 3-4 3z" />
              </svg>
            </button>
            <button
              onClick={disconnectMultimeter}
              disabled={!multimeterConnected || isProcessing}
              className={`p-1 ${
                !multimeterConnected || isProcessing
                  ? "text-gray-500"
                  : "text-red-500 hover:text-red-400"
              }`}
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 4.5c-3.03 0-5.5 2.47-5.5 5.5s2.47 5.5 5.5 5.5 5.5-2.47 5.5-5.5-2.47-5.5-5.5-5.5zm-1 8.5v-6h2v6h-2z" />
              </svg>
            </button>
            <button
              onClick={resetMultimeter}
              className="p-1 text-yellow-500 hover:text-yellow-400"
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 4C6.686 4 4 6.686 4 10c0 3.314 2.686 6 6 6 2.608 0 4.827-1.664 5.65-4h-1.717C13.237 13.635 11.723 15 10 15c-2.757 0-5-2.243-5-5s2.243-5 5-5c1.408 0 2.685.586 3.593 1.526L12 8h4V4l-1.703 1.703C13.185 4.651 11.684 4 10 4z" />
              </svg>
            </button>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <span className="text-gray-400">Voltage:</span>
          <span className="text-white">
            {multimeterData.value.toFixed(6)} V
          </span>
        </div>
      </div>

      {/*Stage*/}
      <div>
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-white text-lg font-semibold">Stage</h2>
          <div className="flex gap-2">
            <button
              onClick={connectStage}
              disabled={stageConnected || isProcessing}
              className={`p-1 ${
                stageConnected || isProcessing
                  ? "text-gray-500"
                  : "text-teal-500 hover:text-teal-400"
              }`}
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 4.5c-3.03 0-5.5 2.47-5.5 5.5s2.47 5.5 5.5 5.5 5.5-2.47 5.5-5.5-2.47-5.5-5.5-5.5zm-1 8.5v-6l4 3-4 3z" />
              </svg>
            </button>
            <button
              onClick={disconnectStage}
              disabled={!stageConnected}
              className={`p-1 ${
                !stageConnected || isProcessing
                  ? "text-gray-500"
                  : "text-red-500 hover:text-red-400"
              }`}
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 4.5c-3.03 0-5.5 2.47-5.5 5.5s2.47 5.5 5.5 5.5 5.5-2.47 5.5-5.5-2.47-5.5-5.5-5.5zm-1 8.5v-6h2v6h-2z" />
              </svg>
            </button>
            <button
              onClick={resetStage}
              className="p-1 text-yellow-500 hover:text-yellow-400"
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 4C6.686 4 4 6.686 4 10c0 3.314 2.686 6 6 6 2.608 0 4.827-1.664 5.65-4h-1.717C13.237 13.635 11.723 15 10 15c-2.757 0-5-2.243-5-5s2.243-5 5-5c1.408 0 2.685.586 3.593 1.526L12 8h4V4l-1.703 1.703C13.185 4.651 11.684 4 10 4z" />
              </svg>
            </button>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <span className="text-gray-400">X:</span>
          <span className="text-white">{stageData.x} mm</span>
          <span className="text-gray-400">Y:</span>
          <span className="text-white">{stageData.y} mm</span>
        </div>
        <div className="grid grid-cols-1 gap-2 mt-4">
          <input
            type="number"
            placeholder="X (0-110) (mm)"
            className={`p-2 rounded bg-gray-700 text-white border ${
              moveX === "" || parseFloat(moveX) < 0 || parseFloat(moveX) > 110
                ? "border-red-500"
                : "border-gray-600 focus:border-teal-500"
            } focus:outline-none`}
            value={moveX}
            onChange={(e) => {
              const value = e.target.value;
              if (
                value === "" ||
                (parseFloat(value) >= 0 && parseFloat(value) <= 110)
              ) {
                setMoveX(value);
              }
            }}
          />
          <input
            type="number"
            placeholder="Y (0-75) (mm)"
            className={`p-2 rounded bg-gray-700 text-white border ${
              moveY === "" || parseFloat(moveY) < 0 || parseFloat(moveY) > 75
                ? "border-red-500"
                : "border-gray-600 focus:border-teal-500"
            } focus:outline-none`}
            value={moveY}
            onChange={(e) => {
              const value = e.target.value;
              if (
                value === "" ||
                (parseFloat(value) >= 0 && parseFloat(value) <= 75)
              ) {
                setMoveY(value);
              }
            }}
          />
        </div>
        <button
          onClick={handleMove}
          disabled={!isMoveValid}
          className={`w-full py-2 rounded text-white transition-colors mt-4 ${
            isMoveValid
              ? "bg-teal-600 hover:bg-teal-700"
              : "bg-gray-600 cursor-not-allowed"
          }`}
        >
          Move & Log
        </button>
      </div>
    </div>
  );
}
