import RealTimeGraphs from './RealTimeGraphs';
import { LockinData, MultimeterData } from '../app/page';

type GraphsPanelProps = {
  lockinData: LockinData;
  multimeterData: MultimeterData;
  lockinConnected: boolean;
  multimeterConnected: boolean;
  resetLockin: boolean;
  resetMultimeter: boolean;
  onResetComplete: () => void;
  lockinStartTime: number | null;
  multimeterStartTime: number | null;
};

export default function GraphsPanel({
  lockinData,
  multimeterData,
  lockinConnected,
  multimeterConnected,
  resetLockin,
  resetMultimeter,
  onResetComplete,
  lockinStartTime,
  multimeterStartTime,
}: GraphsPanelProps) {
  return (
    <div className="w-1/2 rounded-lg bg-gray-800 p-4 shadow-lg">
      <h2 className="mb-4 text-lg font-semibold text-white">Real-Time Data Plots</h2>
      <RealTimeGraphs
        lockinData={lockinData}
        multimeterData={multimeterData}
        lockinConnected={lockinConnected}
        multimeterConnected={multimeterConnected}
        resetLockin={resetLockin}
        resetMultimeter={resetMultimeter}
        onResetComplete={onResetComplete}
        lockinStartTime={lockinStartTime}
        multimeterStartTime={multimeterStartTime}
      />
    </div>
  );
}
