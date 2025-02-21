import { LockinData, MultimeterData } from "../app/page";

type OutputPanelProps = {
  lockinData: LockinData;
  multimeterData: MultimeterData;
  lockinConnected: boolean;
  multimeterConnected: boolean;
  connectLockin: () => void;
  disconnectLockin: () => void;
  connectMultimeter: () => void;
  disconnectMultimeter: () => void;
};

export default function OutputPanel({
  lockinData,
  multimeterData,
  lockinConnected,
  multimeterConnected,
  connectLockin,
  disconnectLockin,
  connectMultimeter,
  disconnectMultimeter,
}: OutputPanelProps) {
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
              disabled={lockinConnected}
              className={`p-1 ${
                lockinConnected
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
              disabled={!lockinConnected}
              className={`p-1 ${
                !lockinConnected
                  ? "text-gray-500"
                  : "text-red-500 hover:text-red-400"
              }`}
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 4.5c-3.03 0-5.5 2.47-5.5 5.5s2.47 5.5 5.5 5.5 5.5-2.47 5.5-5.5-2.47-5.5-5.5-5.5zm-1 8.5v-6h2v6h-2z" />
              </svg>
            </button>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <span className="text-gray-400">X:</span>
          <span className="text-white">{lockinData.X.toFixed(6)}</span>
          <span className="text-gray-400">Y:</span>
          <span className="text-white">{lockinData.Y.toFixed(6)}</span>
          <span className="text-gray-400">R:</span>
          <span className="text-white">{lockinData.R.toFixed(6)}</span>
          <span className="text-gray-400">θ:</span>
          <span className="text-white">{lockinData.theta.toFixed(6)}°</span>
          <span className="text-gray-400">Freq:</span>
          <span className="text-white">
            {lockinData.frequency.toFixed(2)} Hz
          </span>
          <span className="text-gray-400">Phase:</span>
          <span className="text-white">{lockinData.phase.toFixed(2)}°</span>
        </div>
      </div>

      {/* Multimeter */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-white text-lg font-semibold">Multimeter</h2>
          <div className="flex gap-2">
            <button
              onClick={connectMultimeter}
              disabled={multimeterConnected}
              className={`p-1 ${
                multimeterConnected
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
              disabled={!multimeterConnected}
              className={`p-1 ${
                !multimeterConnected
                  ? "text-gray-500"
                  : "text-red-500 hover:text-red-400"
              }`}
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 4.5c-3.03 0-5.5 2.47-5.5 5.5s2.47 5.5 5.5 5.5 5.5-2.47 5.5-5.5-2.47-5.5-5.5-5.5zm-1 8.5v-6h2v6h-2z" />
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
    </div>
  );
}
