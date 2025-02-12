"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

type FormData = {
  x1: string;
  x2: string;
  y1: string;
  y2: string;
  steps: string;
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
    steps: "",
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
      homingVelocity: "100",
      maxVelocity: "1000",
      acceleration: "500",
    },
    channel2: {
      homingVelocity: "100",
      maxVelocity: "1000",
      acceleration: "500",
    },
  };

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
          steps: parseInt(formData.steps),
        }),
      });
      const data = await response.json();
      setStatus(data.message);
    } catch (error) {
      console.error("Error:", error);
      setStatus("Error occurred");
    }
  };

  const handleHomeX = async () => {
    try {
      setStatus("Processing...");
      const response = await fetch("http://localhost:8000/home_x", {
        method: "GET",
      });
      const data = await response.json();
      setStatus(data.message);
    } catch (error) {
      console.error("Error:", error);
      setStatus("Error occurred");
    }
  };

  const handleHomeY = async () => {
    try {
      setStatus("Processing...");
      const response = await fetch("http://localhost:8000/home_y", {
        method: "GET",
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
      setStatus("Processing...");
      const response = await fetch(
        "http://localhost:8000/get_movement_params_x",
        {
          method: "GET",
        }
      );
      const data = await response.json();
      setStatus(data.message);
      setSettings({
        channel1: {
          homingVelocity: data.message,
          maxVelocity: "1",
          acceleration: "2",
        },
        channel2: {
          homingVelocity: "3",
          maxVelocity: "4",
          acceleration: "5",
        },
      });
    } catch (error) {
      console.error("Error:", error);
      setStatus("Error occurred");
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center">
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
                    // Add your save logic here
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
            onClick={handleHomeX}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition-colors"
          >
            Home X
          </button>
          <button
            onClick={handleHomeY}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition-colors"
          >
            Home Y
          </button>
          <button
            onClick={handleGetParams}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition-colors"
          >
            Get Homing Velocity X
          </button>
          {status && (
            <div className="mt-4 text-center text-white">{status}</div>
          )}
        </div>
      </div>
    </div>
  );
}
