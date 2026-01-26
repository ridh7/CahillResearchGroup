import { forwardRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Settings } from '../app/page';

type SettingsPanelProps = {
  settings: Settings;
  setSettings: React.Dispatch<React.SetStateAction<Settings>>;
  defaultSettings: Settings;
  handleSetParams: (settings: Settings) => void;
  setIsSettingsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  top: number;
};

const SettingsPanel = forwardRef<HTMLDivElement, SettingsPanelProps>(
  ({ settings, setSettings, defaultSettings, handleSetParams, setIsSettingsOpen, top }, ref) => {
    const [activeTab, setActiveTab] = useState<'channel1' | 'channel2'>('channel1');

    return (
      <motion.div
        ref={ref}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 20 }}
        transition={{ duration: 0.2 }}
        className="fixed z-50 w-96 rounded-lg border border-gray-700 bg-gray-800 p-6 shadow-xl"
        style={{ top, right: '1rem' }}
      >
        <div className="mb-4 flex justify-between">
          <h2 className="text-xl font-semibold text-white">Settings</h2>
          <button
            onClick={() => setIsSettingsOpen(false)}
            className="text-gray-400 hover:text-white"
          >
            ✕
          </button>
        </div>

        <div className="mb-4 flex">
          <button
            className={`flex-1 py-2 ${
              activeTab === 'channel1' ? 'bg-teal-600' : 'bg-gray-700'
            } rounded-l text-white`}
            onClick={() => setActiveTab('channel1')}
          >
            Channel 1
          </button>
          <button
            className={`flex-1 py-2 ${
              activeTab === 'channel2' ? 'bg-teal-600' : 'bg-gray-700'
            } rounded-r text-white`}
            onClick={() => setActiveTab('channel2')}
          >
            Channel 2
          </button>
        </div>

        <div className="space-y-4">
          {Object.entries(settings[activeTab]).map(([key, value]) => (
            <div key={key}>
              <label className="mb-1 block text-sm text-white">
                {key.charAt(0).toUpperCase() + key.slice(1).replace(/([A-Z])/g, ' $1')}
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
                className="w-full rounded border border-gray-600 bg-gray-700 p-2 text-white focus:border-teal-500 focus:outline-none"
              />
            </div>
          ))}
        </div>

        <div className="mt-6 flex space-x-4">
          <button
            onClick={() => setSettings(defaultSettings)}
            className="flex-1 rounded bg-gray-700 py-2 text-white transition-colors hover:bg-gray-600"
          >
            Reset
          </button>
          <button
            onClick={() => {
              handleSetParams(settings);
              setIsSettingsOpen(false);
            }}
            className="flex-1 rounded bg-teal-600 py-2 text-white transition-colors hover:bg-teal-700"
          >
            Save
          </button>
        </div>
      </motion.div>
    );
  }
);

SettingsPanel.displayName = 'SettingsPanel';

export default SettingsPanel;
