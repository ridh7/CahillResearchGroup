"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

type FormData = {
  x1: string;
  x2: string;
  y1: string;
  y2: string;
  xSteps: string;
  ySteps: string;
  xStepSize: string;
  yStepSize: string;
};

type ChannelSettings = {
  homingVelocity: string;
  maxVelocity: string;
  acceleration: string;
};

type Settings = {
  channel1: ChannelSettings;
  channel2: ChannelSettings;
};

function useClickOutside(
  ref: React.RefObject<HTMLElement | null>,
  handler: () => void
) {
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        handler();
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [ref, handler]);
}

export default function CalculatePage() {
  const [formData, setFormData] = useState<FormData>({
    x1: "",
    y1: "",
    x2: "",
    y2: "",
    xSteps: "",
    ySteps: "",
    xStepSize: "",
    yStepSize: "",
  });
  const [lockinData, setLockinData] = useState({
    X: 0,
    Y: 0,
    R: 0,
    theta: 0,
    frequency: 0,
    phase: 0,
  });
  const [status, setStatus] = useState<string>("");
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"channel1" | "channel2">(
    "channel1"
  );

  const [settings, setSettings] = useState<Settings>({
    channel1: { homingVelocity: "", maxVelocity: "", acceleration: "" },
    channel2: { homingVelocity: "", maxVelocity: "", acceleration: "" },
  });
  const settingsButtonRef = useRef<HTMLButtonElement | null>(null);
  const settingsMenuRef = useRef<HTMLDivElement | null>(null);

  useClickOutside(settingsMenuRef, () => {
    if (isSettingsOpen) setIsSettingsOpen(false);
  });

  const defaultSettings: Settings = {
    channel1: {
      homingVelocity: "10",
      maxVelocity: "100",
      acceleration: "1000",
    },
    channel2: {
      homingVelocity: "10",
      maxVelocity: "100",
      acceleration: "1000",
    },
  };

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/lockin");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLockinData(data);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed");
    };

    return () => {
      ws.close();
    };
  }, []);

  const handleSubmit = async () => {
    try {
      setStatus("Processing...");
      const response = await fetch("http://localhost:8000/start", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          x1: parseFloat(formData.x1),
          x2: parseFloat(formData.x2),
          y1: parseFloat(formData.y1),
          y2: parseFloat(formData.y2),
          x_steps: parseInt(formData.xSteps),
          y_steps: parseInt(formData.ySteps),
          x_step_size: parseFloat(formData.xStepSize),
          y_step_size: parseFloat(formData.yStepSize),
        }),
      });
      const data = await response.json();
      setStatus(data.message);
    } catch (error) {
      console.error("Error:", error);
      setStatus("Error occurred");
    }
  };

  const handleHome = async (channel_direction: string) => {
    try {
      setStatus("Processing...");
      const response = await fetch("http://localhost:8000/home", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          channel_direction: channel_direction,
        }),
      });
      const data = await response.json();
      setStatus(data.message);
    } catch (error) {
      console.error("Error:", error);
      setStatus("Error occurred");
    }
  };

  const handleGetParams = async () => {
    try {
      const response = await fetch(
        "http://localhost:8000/get_movement_params",
        {
          method: "GET",
        }
      );
      const data = await response.json();
      setSettings({
        channel1: {
          homingVelocity: data.homing_velocity_x,
          maxVelocity: data.max_velocity_x,
          acceleration: data.acceleration_x,
        },
        channel2: {
          homingVelocity: data.homing_velocity_y,
          maxVelocity: data.max_velocity_y,
          acceleration: data.acceleration_y,
        },
      });
    } catch (error) {
      console.error("Error:", error);
      setStatus("Error occurred");
    }
  };

  const handleSetParams = async (new_settings: Settings) => {
    try {
      const response = await fetch(
        "http://localhost:8000/set_movement_params",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            channel1: {
              homing_velocity: parseFloat(new_settings.channel1.homingVelocity),
              max_velocity: parseFloat(new_settings.channel1.maxVelocity),
              acceleration: parseFloat(new_settings.channel1.acceleration),
            },
            channel2: {
              homing_velocity: parseFloat(new_settings.channel2.homingVelocity),
              max_velocity: parseFloat(new_settings.channel2.maxVelocity),
              acceleration: parseFloat(new_settings.channel2.acceleration),
            },
          }),
        }
      );
      const data = await response.json();
      if (data.status === "success") {
        console.log("success");
      }
    } catch (error) {
      console.error("Error:", error);
      setStatus("Error occurred");
    }
  };

  const getCurrentPosition = async () => {
    try {
      const response = await fetch(
        "http://localhost:8000/get_current_position",
        {
          method: "GET",
        }
      );
      const data = await response.json();
      setStatus("(" + data.x + ", " + data.y + ")");
    } catch (error) {
      console.error("Error: ", error);
      setStatus("Error occurred");
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <div className="absolute top-4 left-4 bg-gray-900 p-4 rounded-lg shadow-xl border border-gray-800">
        <h2 className="text-white text-lg font-semibold mb-2">
          Lock-in Amplifier
        </h2>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="text-gray-400">X:</div>
          <div className="text-white">{lockinData.X.toFixed(6)}</div>
          <div className="text-gray-400">Y:</div>
          <div className="text-white">{lockinData.Y.toFixed(6)}</div>
          <div className="text-gray-400">R:</div>
          <div className="text-white">{lockinData.R.toFixed(6)}</div>
          <div className="text-gray-400">θ:</div>
          <div className="text-white">{lockinData.theta.toFixed(6)}°</div>
          <div className="text-gray-400">Frequency:</div>
          <div className="text-white">{lockinData.frequency.toFixed(2)} Hz</div>
          <div className="text-gray-400">Phase:</div>
          <div className="text-white">{lockinData.phase.toFixed(2)}°</div>
        </div>
      </div>

      <button
        ref={settingsButtonRef}
        onClick={() => {
          handleGetParams();
          setIsSettingsOpen(!isSettingsOpen);
        }}
        className="absolute top-4 right-4 bg-gray-800 p-2 rounded-full hover:bg-gray-700 transition-colors"
      >
        <svg
          className="w-6 h-6 text-white"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
      </button>

      {/* Settings Popup */}
      <AnimatePresence>
        {isSettingsOpen && (
          <motion.div
            ref={settingsMenuRef}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.1 }}
            className="fixed z-50 origin-top-right"
            style={{
              top: settingsButtonRef.current
                ? settingsButtonRef.current.offsetTop +
                  settingsButtonRef.current.offsetHeight +
                  8
                : 0,
              right: "1rem",
            }}
          >
            <div className="bg-gray-900 p-6 rounded-lg w-96 shadow-xl border border-gray-800">
              <div className="flex justify-between mb-4">
                <h2 className="text-white text-xl font-semibold">Settings</h2>
                <button
                  onClick={() => setIsSettingsOpen(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              {/* Tabs */}
              <div className="flex mb-4">
                <button
                  className={`flex-1 py-2 ${
                    activeTab === "channel1" ? "bg-blue-600" : "bg-gray-800"
                  } text-white rounded-l`}
                  onClick={() => setActiveTab("channel1")}
                >
                  Channel 1
                </button>
                <button
                  className={`flex-1 py-2 ${
                    activeTab === "channel2" ? "bg-blue-600" : "bg-gray-800"
                  } text-white rounded-r`}
                  onClick={() => setActiveTab("channel2")}
                >
                  Channel 2
                </button>
              </div>

              {/* Settings Fields */}
              <div className="space-y-4">
                {Object.entries(settings[activeTab]).map(([key, value]) => (
                  <div key={key}>
                    <label className="text-white text-sm mb-1 block">
                      {key.charAt(0).toUpperCase() +
                        key.slice(1).replace(/([A-Z])/g, " $1")}
                    </label>
                    <input
                      type="number"
                      value={value}
                      onChange={(e) =>
                        setSettings({
                          ...settings,
                          [activeTab]: {
                            ...settings[activeTab],
                            [key]: e.target.value,
                          },
                        })
                      }
                      className="w-full p-2 rounded bg-gray-800 text-white border border-gray-700 focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                ))}
              </div>

              {/* Buttons */}
              <div className="flex space-x-4 mt-6">
                <button
                  onClick={() => setSettings(defaultSettings)}
                  className="flex-1 bg-gray-700 text-white py-2 rounded hover:bg-gray-600 transition-colors"
                >
                  Reset to Default
                </button>
                <button
                  onClick={() => {
                    handleSetParams(settings);
                    setIsSettingsOpen(false);
                  }}
                  className="flex-1 bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition-colors"
                >
                  Save
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="bg-gray-900 p-8 rounded-lg shadow-xl w-96">
        <div className="space-y-4">
          {(Object.keys(formData) as Array<keyof FormData>).map((key) => (
            <div key={key}>
              <input
                type="number"
                placeholder={key}
                className="w-full p-2 rounded bg-gray-800 text-white border border-gray-700 focus:border-blue-500 focus:outline-none"
                value={formData[key]}
                onChange={(e) =>
                  setFormData({ ...formData, [key]: e.target.value })
                }
              />
            </div>
          ))}
          <button
            onClick={handleSubmit}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition-colors"
          >
            Start
          </button>
          <button
            onClick={() => handleHome("x")}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition-colors"
          >
            Home X
          </button>
          <button
            onClick={() => handleHome("y")}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition-colors"
          >
            Home Y
          </button>
          <button
            onClick={() => handleHome("")}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition-colors"
          >
            Home X & Y
          </button>
          <button
            onClick={getCurrentPosition}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition-colors"
          >
            Get Current Position
          </button>
          {status && (
            <div className="mt-4 text-center text-white">{status}</div>
          )}
        </div>
      </div>
    </div>
  );
}
