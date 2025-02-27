import { useState, useMemo } from "react";
import { FormData } from "../app/page";

type DeviceControlsProps = {
  formData: FormData;
  setFormData: React.Dispatch<React.SetStateAction<FormData>>;
  handleSubmit: () => void;
  handleHome: (direction: string) => void;
  status: string;
};

const initialFormData = {
  sampleId: "",
  sampleName: "",
  probeLaserPower: "",
  pumpLaserPower: "",
  aluminumThickness: "",
  comments: "",
  x1: "",
  x2: "",
  y1: "",
  y2: "",
  xSteps: "",
  ySteps: "",
  xStepSize: "",
  yStepSize: "",
  movementMode: "steps",
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

  const handleReset = () => {
    setFormData(initialFormData);
  };

  const isFormValid = useMemo(() => {
    const x1Valid =
      formData.x1 !== "" &&
      Number(formData.x1) >= 0 &&
      Number(formData.x1) <= 110;
    const x2Valid =
      formData.x2 !== "" &&
      Number(formData.x2) >= 0 &&
      Number(formData.x2) <= 110;
    const y1Valid =
      formData.y1 !== "" &&
      Number(formData.y1) >= 0 &&
      Number(formData.y1) <= 75;
    const y2Valid =
      formData.y2 !== "" &&
      Number(formData.y2) >= 0 &&
      Number(formData.y2) <= 75;

    if (formData.movementMode === "steps") {
      const xStepsValid =
        formData.xSteps !== "" &&
        Number(formData.xSteps) > 0 &&
        Number.isInteger(Number(formData.xSteps));
      const yStepsValid =
        formData.ySteps !== "" &&
        Number(formData.ySteps) > 0 &&
        Number.isInteger(Number(formData.ySteps));
      return (
        x1Valid && x2Valid && y1Valid && y2Valid && xStepsValid && yStepsValid
      );
    } else {
      const xStepSizeValid =
        formData.xStepSize !== "" && Number(formData.xStepSize) > 0;
      const yStepSizeValid =
        formData.yStepSize !== "" && Number(formData.yStepSize) > 0;
      return (
        x1Valid &&
        x2Valid &&
        y1Valid &&
        y2Valid &&
        xStepSizeValid &&
        yStepSizeValid
      );
    }
  }, [formData]);

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
          <div className="flex justify-center space-x-6 mb-4">
            <label className="flex items-center text-white">
              <input
                type="radio"
                name="movementMode"
                value="steps"
                checked={formData.movementMode === "steps"}
                onChange={() => {
                  setFormData({
                    ...formData,
                    xStepSize: "",
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
                checked={formData.movementMode === "stepSize"}
                onChange={() => {
                  setFormData({
                    ...formData,
                    xSteps: "",
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
            {["x1", "y1", "x2", "y2"].map((key) => (
              <input
                key={key}
                type="number"
                placeholder={`${key} (${
                  key === "x1" || key === "x2" ? "0-110" : "0-75"
                })`}
                className={`p-2 rounded bg-gray-700 text-white border ${
                  formData[key as keyof FormData] === "" ||
                  ((key === "x1" || key === "x2") &&
                    (Number(formData[key as keyof FormData]) < 0 ||
                      Number(formData[key as keyof FormData]) > 110)) ||
                  ((key === "y1" || key === "y2") &&
                    (Number(formData[key as keyof FormData]) < 0 ||
                      Number(formData[key as keyof FormData]) > 75))
                    ? "border-red-500"
                    : "border-gray-600 focus:border-teal-500"
                } focus:outline-none`}
                value={formData[key as keyof FormData]}
                onChange={(e) => {
                  const value = e.target.value;
                  if (
                    ((key === "x1" || key === "x2") &&
                      (value === "" ||
                        (Number(value) >= 0 && Number(value) <= 110))) ||
                    ((key === "y1" || key === "y2") &&
                      (value === "" ||
                        (Number(value) >= 0 && Number(value) <= 75)))
                  ) {
                    setFormData({
                      ...formData,
                      [key as keyof FormData]: value,
                    });
                  }
                }}
              />
            ))}
            {formData.movementMode === "steps" ? (
              <>
                <input
                  type="number"
                  placeholder="xSteps (int >0)"
                  className={`p-2 rounded bg-gray-700 text-white border ${
                    formData.xSteps === "" ||
                    Number(formData.xSteps) <= 0 ||
                    !Number.isInteger(Number(formData.xSteps))
                      ? "border-red-500"
                      : "border-gray-600 focus:border-teal-500"
                  } focus:outline-none`}
                  value={formData.xSteps}
                  onChange={(e) => {
                    const value = e.target.value;
                    // Only allow integers or empty string
                    if (
                      value === "" ||
                      (Number.isInteger(Number(value)) && Number(value) > 0)
                    ) {
                      setFormData({ ...formData, xSteps: value });
                    }
                  }}
                />
                <input
                  type="number"
                  placeholder="ySteps (int >0)"
                  className={`p-2 rounded bg-gray-700 text-white border ${
                    formData.ySteps === "" ||
                    Number(formData.ySteps) <= 0 ||
                    !Number.isInteger(Number(formData.ySteps))
                      ? "border-red-500"
                      : "border-gray-600 focus:border-teal-500"
                  } focus:outline-none`}
                  value={formData.ySteps}
                  onChange={(e) => {
                    const value = e.target.value;
                    if (
                      value === "" ||
                      (Number.isInteger(Number(value)) && Number(value) > 0)
                    ) {
                      setFormData({ ...formData, ySteps: value });
                    }
                  }}
                />
              </>
            ) : (
              <>
                <input
                  type="number"
                  placeholder="xStepSize (>0)"
                  className={`p-2 rounded bg-gray-700 text-white border ${
                    formData.xStepSize === "" || Number(formData.xStepSize) <= 0
                      ? "border-red-500"
                      : "border-gray-600 focus:border-teal-500"
                  } focus:outline-none`}
                  value={formData.xStepSize}
                  onChange={(e) =>
                    setFormData({ ...formData, xStepSize: e.target.value })
                  }
                />
                <input
                  type="number"
                  placeholder="yStepSize (>0)"
                  className={`p-2 rounded bg-gray-700 text-white border ${
                    formData.yStepSize === "" || Number(formData.yStepSize) <= 0
                      ? "border-red-500"
                      : "border-gray-600 focus:border-teal-500"
                  } focus:outline-none`}
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
              disabled={!isFormValid}
              className={`flex-1 py-2 rounded text-white transition-colors ${
                isFormValid
                  ? "bg-teal-600 hover:bg-teal-700"
                  : "bg-gray-600 cursor-not-allowed"
              }`}
            >
              Start
            </button>
            <button
              onClick={() => handleHome("")}
              className="flex-1 bg-teal-600 text-white py-2 rounded hover:bg-teal-700 transition-colors"
            >
              Home XY
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
          </div>
          <button
            onClick={handleReset}
            className="w-full bg-red-600 text-white py-2 rounded hover:bg-red-700 transition-colors"
          >
            Reset Values
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
