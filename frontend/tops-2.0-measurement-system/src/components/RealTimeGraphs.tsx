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
  timestamp: number;
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
}

export default function RealTimeGraphs({
  lockinData,
  multimeterData,
  lockinConnected,
  multimeterConnected,
}: GraphProps) {
  const [xData, setXData] = useState<DataPoint[]>([]);
  const [yData, setYData] = useState<DataPoint[]>([]);
  const [multimeterValues, setMultimeterValues] = useState<DataPoint[]>([]);

  useEffect(() => {
    if (lockinConnected) {
      const timestamp = Date.now();
      setXData((prev) =>
        [...prev, { timestamp, value: lockinData.X }].slice(-100)
      );
      setYData((prev) =>
        [...prev, { timestamp, value: lockinData.Y }].slice(-100)
      );
    }
  }, [lockinData, lockinConnected]);

  useEffect(() => {
    if (multimeterConnected) {
      const timestamp = Date.now();
      setMultimeterValues((prev) =>
        [...prev, { timestamp, value: multimeterData.value }].slice(-100)
      );
    }
  }, [multimeterData, multimeterConnected]);

  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="grid grid-cols-1 gap-4 mt-4">
      <div className="bg-gray-900 p-4 rounded-lg">
        <h3 className="text-white text-lg mb-2">Lock-in X Component</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={xData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" tickFormatter={formatTime} />
            <YAxis />
            <Tooltip labelFormatter={formatTime} />
            <Legend />
            <Line type="monotone" dataKey="value" stroke="#8884d8" name="X" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-gray-900 p-4 rounded-lg">
        <h3 className="text-white text-lg mb-2">Lock-in Y Component</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={yData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" tickFormatter={formatTime} />
            <YAxis />
            <Tooltip labelFormatter={formatTime} />
            <Legend />
            <Line type="monotone" dataKey="value" stroke="#82ca9d" name="Y" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-gray-900 p-4 rounded-lg">
        <h3 className="text-white text-lg mb-2">Multimeter Values</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={multimeterValues}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" tickFormatter={formatTime} />
            <YAxis />
            <Tooltip labelFormatter={formatTime} />
            <Legend />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#ffc658"
              name="Value"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
