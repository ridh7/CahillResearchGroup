import { forwardRef, useState } from "react";
import { motion } from "framer-motion";
import { Settings } from "../app/page";

type SettingsPanelProps = {
  settings: Settings;
  setSettings: React.Dispatch<React.SetStateAction<Settings>>;
  defaultSettings: Settings;
  handleSetParams: (settings: Settings) => void;
  setIsSettingsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  top: number;
};

const SettingsPanel = forwardRef<HTMLDivElement, SettingsPanelProps>(
  (
    {
      settings,
      setSettings,
      defaultSettings,
      handleSetParams,
      setIsSettingsOpen,
      top,
    },
    ref
  ) => {
    const [activeTab, setActiveTab] = useState<"channel1" | "channel2">(
      "channel1"
    );

    return (
      <motion.div
        ref={ref}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 20 }}
        transition={{ duration: 0.2 }}
        className="fixed z-50 bg-gray-800 p-6 rounded-lg w-96 shadow-xl border border-gray-700"
        style={{ top, right: "1rem" }}
      >
        <div className="flex justify-between mb-4">
          <h2 className="text-white text-xl font-semibold">Settings</h2>
          <button
            onClick={() => setIsSettingsOpen(false)}
            className="text-gray-400 hover:text-white"
          >
            ✕
          </button>
        </div>

        <div className="flex mb-4">
          <button
            className={`flex-1 py-2 ${
              activeTab === "channel1" ? "bg-teal-600" : "bg-gray-700"
            } text-white rounded-l`}
            onClick={() => setActiveTab("channel1")}
          >
            Channel 1
          </button>
          <button
            className={`flex-1 py-2 ${
              activeTab === "channel2" ? "bg-teal-600" : "bg-gray-700"
            } text-white rounded-r`}
            onClick={() => setActiveTab("channel2")}
          >
            Channel 2
          </button>
        </div>

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
                className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600 focus:border-teal-500 focus:outline-none"
              />
            </div>
          ))}
        </div>

        <div className="flex space-x-4 mt-6">
          <button
            onClick={() => setSettings(defaultSettings)}
            className="flex-1 bg-gray-700 text-white py-2 rounded hover:bg-gray-600 transition-colors"
          >
            Reset
          </button>
          <button
            onClick={() => {
              handleSetParams(settings);
              setIsSettingsOpen(false);
            }}
            className="flex-1 bg-teal-600 text-white py-2 rounded hover:bg-teal-700 transition-colors"
          >
            Save
          </button>
        </div>
      </motion.div>
    );
  }
);

SettingsPanel.displayName = "SettingsPanel";

export default SettingsPanel;
