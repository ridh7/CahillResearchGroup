import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface DataPoint {
  time: number; // Relative time in seconds
  value: number;
}

interface GraphProps {
  lockinData: {
    X: number;
    Y: number;
  };
  multimeterData: {
    value: number;
  };
  lockinConnected: boolean;
  multimeterConnected: boolean;
  resetLockin: boolean;
  resetMultimeter: boolean;
  onResetComplete: () => void;
  lockinStartTime: number | null;
  multimeterStartTime: number | null;
}

export default function RealTimeGraphs({
  lockinData,
  multimeterData,
  lockinConnected,
  multimeterConnected,
  resetLockin,
  resetMultimeter,
  onResetComplete,
  lockinStartTime,
  multimeterStartTime,
}: GraphProps) {
  const [xData, setXData] = useState<DataPoint[]>([]);
  const [yData, setYData] = useState<DataPoint[]>([]);
  const [multimeterValues, setMultimeterValues] = useState<DataPoint[]>([]);

  useEffect(() => {
    if (resetLockin) {
      setXData([]);
      setYData([]);
      onResetComplete();
    }
  }, [resetLockin, onResetComplete]);

  useEffect(() => {
    if (resetMultimeter) {
      setMultimeterValues([]);
      onResetComplete();
    }
  }, [resetMultimeter, onResetComplete]);

  useEffect(() => {
    if (lockinConnected && lockinStartTime !== null) {
      const time = (Date.now() - lockinStartTime) / 1000; // Convert to seconds
      setXData((prev) => [...prev, { time, value: lockinData.X }].slice(-100));
      setYData((prev) => [...prev, { time, value: lockinData.Y }].slice(-100));
    }
  }, [lockinData, lockinConnected]);

  useEffect(() => {
    if (multimeterConnected && multimeterStartTime !== null) {
      const time = (Date.now() - multimeterStartTime) / 1000; // Convert to seconds
      setMultimeterValues((prev) =>
        [...prev, { time, value: multimeterData.value }].slice(-100)
      );
    }
  }, [multimeterData, multimeterConnected]);

  const formatTime = (time: number) => `${time.toFixed(1)}s`; // Simple seconds format

  return (
    <div className="space-y-6">
      {/* Lock-in Amplifier X vs. Time */}
      <div className="bg-black p-4 rounded-lg shadow-lg">
        <h3 className="text-white text-lg font-semibold mb-2">
          Lock-in Amplifier X vs. Time
        </h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={xData}>
            <CartesianGrid stroke="#444" strokeDasharray="3 3" />
            <XAxis
              dataKey="time"
              tickFormatter={formatTime}
              stroke="#fff"
              label={{
                value: "Time (s)",
                position: "insideBottom",
                offset: -5,
                fill: "#fff",
              }}
            />
            <YAxis
              stroke="#fff"
              label={{
                value: "X",
                angle: -90,
                position: "insideLeft",
                fill: "#fff",
              }}
            />
            <Tooltip
              labelFormatter={formatTime}
              contentStyle={{ backgroundColor: "#333", border: "none" }}
              labelStyle={{ color: "#fff" }}
            />
            <Legend wrapperStyle={{ color: "#fff" }} />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#3b82f6" // Blue
              name="X"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Lock-in Amplifier Y vs. Time */}
      <div className="bg-black p-4 rounded-lg shadow-lg">
        <h3 className="text-white text-lg font-semibold mb-2">
          Lock-in Amplifier Y vs. Time
        </h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={yData}>
            <CartesianGrid stroke="#444" strokeDasharray="3 3" />
            <XAxis
              dataKey="time"
              tickFormatter={formatTime}
              stroke="#fff"
              label={{
                value: "Time (s)",
                position: "insideBottom",
                offset: -5,
                fill: "#fff",
              }}
            />
            <YAxis
              stroke="#fff"
              label={{
                value: "Y",
                angle: -90,
                position: "insideLeft",
                fill: "#fff",
              }}
            />
            <Tooltip
              labelFormatter={formatTime}
              contentStyle={{ backgroundColor: "#333", border: "none" }}
              labelStyle={{ color: "#fff" }}
            />
            <Legend wrapperStyle={{ color: "#fff" }} />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#f97316" // Orange
              name="Y"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Multimeter Voltage vs. Time */}
      <div className="bg-black p-4 rounded-lg shadow-lg">
        <h3 className="text-white text-lg font-semibold mb-2">
          Multimeter Voltage vs. Time
        </h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={multimeterValues}>
            <CartesianGrid stroke="#444" strokeDasharray="3 3" />
            <XAxis
              dataKey="time"
              tickFormatter={formatTime}
              stroke="#fff"
              label={{
                value: "Time (s)",
                position: "insideBottom",
                offset: -5,
                fill: "#fff",
              }}
            />
            <YAxis
              stroke="#fff"
              label={{
                value: "Voltage (V)",
                angle: -90,
                position: "insideLeft",
                fill: "#fff",
              }}
            />
            <Tooltip
              labelFormatter={formatTime}
              contentStyle={{ backgroundColor: "#333", border: "none" }}
              labelStyle={{ color: "#fff" }}
            />
            <Legend wrapperStyle={{ color: "#fff" }} />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#22c55e" // Green
              name="Voltage"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
