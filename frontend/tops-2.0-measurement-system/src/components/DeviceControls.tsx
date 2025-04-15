import { useState, useMemo } from "react";
import { FormData } from "../app/page";

type DeviceControlsProps = {
  formData: FormData;
  setFormData: React.Dispatch<React.SetStateAction<FormData>>;
  handleSubmit: () => void;
  handleHome: (direction: string) => void;
  status: string;
  lockinSettings: { sensitivity: number; timeConstant: number };
  changeLockinSensitivity: (increment: boolean) => void;
  changeLockinTimeConstant: (increment: boolean) => void;
  fetchLockinSettings: () => void;
  lockinConnected: boolean;
  multimeterSettings: { aperture: number; terminal: string };
  fetchMultimeterSettings: () => Promise<void>;
  changeMultimeterAperture: (nplc: number) => void;
  changeMultimeterTerminal: (terminal: string) => void;
  multimeterConnected: boolean;
};

const initialFormData = {
  sampleId: "",
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
  delay: "",
};

export default function DeviceControls({
  formData,
  setFormData,
  handleSubmit,
  handleHome,
  status,
  lockinSettings,
  changeLockinSensitivity,
  changeLockinTimeConstant,
  fetchLockinSettings,
  lockinConnected,
  multimeterSettings,
  changeMultimeterAperture,
  changeMultimeterTerminal,
  fetchMultimeterSettings,
  multimeterConnected,
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
    // Add delay validation (allowing empty string or non-negative number)
    const delayValid =
      formData.delay === "" ||
      (Number(formData.delay) >= 0 && !isNaN(Number(formData.delay)));

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
        x1Valid &&
        x2Valid &&
        y1Valid &&
        y2Valid &&
        xStepsValid &&
        yStepsValid &&
        delayValid
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
        yStepSizeValid &&
        delayValid
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
          onClick={() => {
            setActiveTab("lockin");
            fetchLockinSettings();
          }}
        >
          Lock-in
        </button>
        <button
          className={`flex-1 py-2 ${
            activeTab === "multimeter" ? "bg-teal-600" : "bg-gray-700"
          } text-white rounded-r`}
          onClick={() => {
            setActiveTab("multimeter");
            fetchMultimeterSettings();
          }}
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
                }) (mm)`}
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
                  placeholder="xStepSize (>0) (mm)"
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
                  placeholder="yStepSize (>0) (mm)"
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
            <input
              placeholder="delay (>=0) (s)"
              className={`p-2 rounded bg-gray-700 text-white border ${
                formData.delay !== "" &&
                (Number(formData.delay) < 0 || isNaN(Number(formData.delay)))
                  ? "border-red-500"
                  : "border-gray-600 focus:border-teal-500"
              } focus:outline-none`}
              value={formData.delay}
              onChange={(e) => {
                const value = e.target.value;
                if (
                  value === "" ||
                  (Number(value) >= 0 && !isNaN(Number(value)))
                ) {
                  setFormData({ ...formData, delay: value });
                }
              }}
            />
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
        <div className="space-y-4">
          {/* Sensitivity Control */}
          <div className="flex items-center space-x-2">
            <label className="text-white w-24">Sensitivity</label>
            <button
              onClick={() => changeLockinSensitivity(true)}
              disabled={lockinSettings.sensitivity === 27 || lockinConnected}
              className="p-2 bg-gray-700 text-white rounded hover:bg-gray-600 disabled:opacity-50"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 10l7 7 7-7"
                />
              </svg>
            </button>
            <input
              type="text"
              value={
                {
                  0: "1 V",
                  1: "500 mV",
                  2: "200 mV",
                  3: "100 mV",
                  4: "50 mV",
                  5: "20 mV",
                  6: "10 mV",
                  7: "5 mV",
                  8: "2 mV",
                  9: "1 mV",
                  10: "500 µV",
                  11: "200 µV",
                  12: "100 µV",
                  13: "50 µV",
                  14: "20 µV",
                  15: "10 µV",
                  16: "5 µV",
                  17: "2 µV",
                  18: "1 µV",
                  19: "500 nV",
                  20: "200 nV",
                  21: "100 nV",
                  22: "50 nV",
                  23: "20 nV",
                  24: "10 nV",
                  25: "5 nV",
                  26: "2 nV",
                  27: "1 nV",
                }[lockinSettings.sensitivity] || "Unknown"
              }
              readOnly
              className="p-2 rounded bg-gray-700 text-white border border-gray-600 w-24 text-center"
            />
            <button
              onClick={() => changeLockinSensitivity(false)}
              disabled={lockinSettings.sensitivity === 0 || lockinConnected}
              className="p-2 bg-gray-700 text-white rounded hover:bg-gray-600 disabled:opacity-50"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 14l-7-7-7 7"
                />
              </svg>
            </button>
          </div>

          {/* Time Constant Control */}
          <div className="flex items-center space-x-2">
            <label className="text-white w-24">Time Constant</label>
            <button
              onClick={() => changeLockinTimeConstant(false)}
              disabled={lockinSettings.timeConstant === 0 || lockinConnected}
              className="p-2 bg-gray-700 text-white rounded hover:bg-gray-600 disabled:opacity-50"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 10l7 7 7-7"
                />
              </svg>
            </button>
            <input
              type="text"
              value={
                {
                  0: "1 µs",
                  1: "3 µs",
                  2: "10 µs",
                  3: "30 µs",
                  4: "100 µs",
                  5: "300 µs",
                  6: "1 ms",
                  7: "3 ms",
                  8: "10 ms",
                  9: "30 ms",
                  10: "100 ms",
                  11: "300 ms",
                  12: "1 s",
                  13: "3 s",
                  14: "10 s",
                  15: "30 s",
                  16: "100 s",
                  17: "300 s",
                  18: "1 ks",
                  19: "3 ks",
                  20: "10 ks",
                  21: "30 ks",
                  22: "100 ks",
                  23: "300 ks",
                }[lockinSettings.timeConstant] || "Unknown"
              }
              readOnly
              className="p-2 rounded bg-gray-700 text-white border border-gray-600 w-24 text-center"
            />
            <button
              onClick={() => changeLockinTimeConstant(true)}
              disabled={lockinSettings.timeConstant === 23 || lockinConnected} // Adjust to 30 if extending time constant map
              className="p-2 bg-gray-700 text-white rounded hover:bg-gray-600 disabled:opacity-50"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 14l-7-7-7 7"
                />
              </svg>
            </button>
          </div>
        </div>
      )}
      {activeTab === "multimeter" && (
        <div className="space-y-4">
          {/* Aperture Control */}
          <div className="flex items-center space-x-2">
            <label className="text-white w-24">Aperture (NPLC)</label>
            <button
              onClick={() => {
                const validNPLC = [0.02, 0.2, 1, 10, 100];
                const currentIndex = validNPLC.indexOf(
                  multimeterSettings.aperture
                );
                if (currentIndex > 0) {
                  changeMultimeterAperture(validNPLC[currentIndex - 1]);
                }
              }}
              disabled={
                multimeterSettings.aperture === 0.02 || multimeterConnected
              }
              className="p-2 bg-gray-700 text-white rounded hover:bg-gray-600 disabled:opacity-50"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 10l7 7 7-7"
                />
              </svg>
            </button>
            <input
              type="text"
              value={multimeterSettings.aperture.toString()}
              readOnly
              className="p-2 rounded bg-gray-700 text-white border border-gray-600 w-24 text-center"
            />
            <button
              onClick={() => {
                const validNPLC = [0.02, 0.2, 1, 10, 100];
                const currentIndex = validNPLC.indexOf(
                  multimeterSettings.aperture
                );
                if (currentIndex < validNPLC.length - 1) {
                  changeMultimeterAperture(validNPLC[currentIndex + 1]);
                }
              }}
              disabled={
                multimeterSettings.aperture === 100 || multimeterConnected
              }
              className="p-2 bg-gray-700 text-white rounded hover:bg-gray-600 disabled:opacity-50"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 14l-7-7-7 7"
                />
              </svg>
            </button>
          </div>

          {/* Terminal Control */}
          <div className="flex items-center space-x-2">
            <label className="text-white w-24">Terminal</label>
            <div className="flex space-x-4">
              <label className="flex items-center text-white">
                <input
                  type="radio"
                  name="terminal"
                  value="front"
                  checked={multimeterSettings.terminal === "fron"}
                  onChange={() => changeMultimeterTerminal("fron")}
                  className="mr-2 text-teal-600 focus:ring-teal-500"
                  disabled={multimeterConnected}
                />
                Front
              </label>
              <label className="flex items-center text-white">
                <input
                  type="radio"
                  name="terminal"
                  value="rear"
                  checked={multimeterSettings.terminal === "rear"}
                  onChange={() => changeMultimeterTerminal("rear")}
                  className="mr-2 text-teal-600 focus:ring-teal-500"
                  disabled={multimeterConnected}
                />
                Rear
              </label>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
