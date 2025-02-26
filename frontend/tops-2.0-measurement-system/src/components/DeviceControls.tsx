import { useState } from "react";
import { FormData } from "../app/page";

type DeviceControlsProps = {
  formData: FormData;
  setFormData: React.Dispatch<React.SetStateAction<FormData>>;
  handleSubmit: () => void;
  handleHome: (direction: string) => void;
  status: string;
};

export default function DeviceControls({
  formData,
  setFormData,
  handleSubmit,
  handleHome,
  status,
}: DeviceControlsProps) {
  const [activeTab, setActiveTab] = useState<"stage" | "lockin" | "multimeter">(
    "stage"
  );
  const [movementMode, setMovementMode] = useState<"steps" | "stepSize">(
    "steps"
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
          {/* Radio Buttons for Movement Mode */}
          <div className="flex justify-center space-x-6 mb-4">
            <label className="flex items-center text-white">
              <input
                type="radio"
                name="movementMode"
                value="steps"
                checked={movementMode === "steps"}
                onChange={() => {
                  setMovementMode("steps");
                  setFormData({
                    ...formData,
                    xStepSize: "", // Reset Step Size fields
                    yStepSize: "",
                    movementMode: "steps",
                  });
                }}
                className="mr-2 text-teal-600 focus:ring-teal-500"
              />
              Steps
            </label>
            <label className="flex items-center text-white">
              <input
                type="radio"
                name="movementMode"
                value="stepSize"
                checked={movementMode === "stepSize"}
                onChange={() => {
                  setMovementMode("stepSize");
                  setFormData({
                    ...formData,
                    xSteps: "", // Reset Steps fields
                    ySteps: "",
                    movementMode: "stepSize",
                  });
                }}
                className="mr-2 text-teal-600 focus:ring-teal-500"
              />
              Step Size
            </label>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {/* Always show x1, y1, x2, y2 */}
            {["x1", "y1", "x2", "y2"].map((key) => (
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
            {/* Conditionally show xSteps/ySteps or xStepSize/yStepSize */}
            {movementMode === "steps" ? (
              <>
                <input
                  type="number"
                  placeholder="xSteps"
                  className="p-2 rounded bg-gray-700 text-white border border-gray-600 focus:border-teal-500 focus:outline-none"
                  value={formData.xSteps}
                  onChange={(e) =>
                    setFormData({ ...formData, xSteps: e.target.value })
                  }
                />
                <input
                  type="number"
                  placeholder="ySteps"
                  className="p-2 rounded bg-gray-700 text-white border border-gray-600 focus:border-teal-500 focus:outline-none"
                  value={formData.ySteps}
                  onChange={(e) =>
                    setFormData({ ...formData, ySteps: e.target.value })
                  }
                />
              </>
            ) : (
              <>
                <input
                  type="number"
                  placeholder="xStepSize"
                  className="p-2 rounded bg-gray-700 text-white border border-gray-600 focus:border-teal-500 focus:outline-none"
                  value={formData.xStepSize}
                  onChange={(e) =>
                    setFormData({ ...formData, xStepSize: e.target.value })
                  }
                />
                <input
                  type="number"
                  placeholder="yStepSize"
                  className="p-2 rounded bg-gray-700 text-white border border-gray-600 focus:border-teal-500 focus:outline-none"
                  value={formData.yStepSize}
                  onChange={(e) =>
                    setFormData({ ...formData, yStepSize: e.target.value })
                  }
                />
              </>
            )}
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
