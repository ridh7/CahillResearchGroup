import { useState } from "react";
import { FormData } from "../app/page";

type DeviceControlsProps = {
  formData: FormData;
  setFormData: React.Dispatch<React.SetStateAction<FormData>>;
  handleSubmit: () => void;
  handleHome: (direction: string) => void;
  getCurrentPosition: () => void;
  status: string;
};

export default function DeviceControls({
  formData,
  setFormData,
  handleSubmit,
  handleHome,
  getCurrentPosition,
  status,
}: DeviceControlsProps) {
  const [activeTab, setActiveTab] = useState<"stage" | "lockin" | "multimeter">(
    "stage"
  );

  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow-lg flex-1">
      <div className="flex mb-4">
        <button
          className={`flex-1 py-2 ${
            activeTab === "stage" ? "bg-teal-600" : "bg-gray-700"
          } text-white rounded-l`}
          onClick={() => setActiveTab("stage")}
        >
          Stage
        </button>
        <button
          className={`flex-1 py-2 ${
            activeTab === "lockin" ? "bg-teal-600" : "bg-gray-700"
          } text-white`}
          onClick={() => setActiveTab("lockin")}
        >
          Lock-in
        </button>
        <button
          className={`flex-1 py-2 ${
            activeTab === "multimeter" ? "bg-teal-600" : "bg-gray-700"
          } text-white rounded-r`}
          onClick={() => setActiveTab("multimeter")}
        >
          Multimeter
        </button>
      </div>

      {activeTab === "stage" && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-2">
            {[
              "x1",
              "y1",
              "x2",
              "y2",
              "xSteps",
              "ySteps",
              "xStepSize",
              "yStepSize",
            ].map((key) => (
              <input
                key={key}
                type="number"
                placeholder={key}
                className="p-2 rounded bg-gray-700 text-white border border-gray-600 focus:border-teal-500 focus:outline-none"
                value={formData[key as keyof FormData]}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    [key as keyof FormData]: e.target.value,
                  })
                }
              />
            ))}
          </div>
          <div className="flex space-x-2">
            <button
              onClick={handleSubmit}
              className="flex-1 bg-teal-600 text-white py-2 rounded hover:bg-teal-700 transition-colors"
            >
              Start
            </button>
            <button
              onClick={() => handleHome("x")}
              className="flex-1 bg-teal-600 text-white py-2 rounded hover:bg-teal-700 transition-colors"
            >
              Home X
            </button>
            <button
              onClick={() => handleHome("y")}
              className="flex-1 bg-teal-600 text-white py-2 rounded hover:bg-teal-700 transition-colors"
            >
              Home Y
            </button>
            <button
              onClick={() => handleHome("")}
              className="flex-1 bg-teal-600 text-white py-2 rounded hover:bg-teal-700 transition-colors"
            >
              Home XY
            </button>
          </div>
          <button
            onClick={getCurrentPosition}
            className="w-full bg-teal-600 text-white py-2 rounded hover:bg-teal-700 transition-colors"
          >
            Get Position
          </button>
          {status && (
            <div className="text-center text-white mt-2">{status}</div>
          )}
        </div>
      )}
      {activeTab === "lockin" && (
        <p className="text-gray-400">Controlled via Output Panel</p>
      )}
      {activeTab === "multimeter" && (
        <p className="text-gray-400">Controlled via Output Panel</p>
      )}
    </div>
  );
}
