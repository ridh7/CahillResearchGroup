'use client';

import { useState, useRef, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import MetadataPanel from '../components/MetadataPanel';
import DeviceControls from '../components/DeviceControls';
import OutputPanel from '../components/OutputPanel';
import SettingsPanel from '../components/SettingsPanel';
import LiveScanPanel from '../components/LiveScanPanel';
import Link from 'next/link';
import { API_BASE } from '../lib/api';

export type FormData = {
  sampleId: string;
  comments: string;
  saveDir: string;
  x1: string;
  x2: string;
  y1: string;
  y2: string;
  xSteps: string;
  ySteps: string;
  xStepSize: string;
  yStepSize: string;
  movementMode: string;
  delay: string;
  motionType: string;
  scanPattern: string;
  recordRetrace: boolean;
  fastAxis: string;
};

export type ScanDataPoint = {
  timestamp: string;
  positionX: number | null;
  positionY: number | null;
  X: number;
  Y: number;
  frequency: number;
  voltage: number;
};

export type LockinData = {
  X: number;
  Y: number;
  frequency: number;
  sensitivity?: number;
  timeConstant?: number;
};

export type MultimeterData = {
  value: number;
  aperture?: number;
  terminal?: string;
};
export type StageData = {
  x: number;
  y: number;
};

export type ChannelSettings = {
  homingVelocity: string;
  maxVelocity: string;
  acceleration: string;
};

export type Settings = {
  channel1: ChannelSettings;
  channel2: ChannelSettings;
};

function useClickOutside(ref: React.RefObject<HTMLElement | null>, handler: () => void) {
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        handler();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [ref, handler]);
}

export default function CalculatePage() {
  const [formData, setFormData] = useState<FormData>({
    sampleId: '',
    comments: '',
    saveDir: '',
    x1: '',
    x2: '',
    y1: '',
    y2: '',
    xSteps: '',
    ySteps: '',
    xStepSize: '',
    yStepSize: '',
    movementMode: 'steps',
    delay: '',
    motionType: 'step_and_measure',
    scanPattern: 'bidirectional',
    recordRetrace: false,
    fastAxis: 'y',
  });

  const [lockinData, setLockinData] = useState<LockinData>({
    X: 0,
    Y: 0,
    frequency: 0,
  });
  const [lockinSettings, setLockinSettings] = useState({
    sensitivity: 0,
    timeConstant: 0,
    frequency: 0,
    filterSlope: 0,
  });
  const [multimeterData, setMultimeterData] = useState<MultimeterData>({
    value: 0,
  });
  const [multimeterSettings, setMultimeterSettings] = useState({
    aperture: 0, // Default NPLC
    terminal: '', // Default terminal
  });
  const [stageData, setStageData] = useState<StageData>({
    x: 0,
    y: 0,
  });
  const [lockinConnected, setLockinConnected] = useState(false);
  const [multimeterConnected, setMultimeterConnected] = useState(false);
  const [stageConnected, setStageConnected] = useState(false);
  const [, setResetLockinTrigger] = useState(false);
  const [, setResetMultimeterTrigger] = useState(false);
  const [, setLockinStartTime] = useState<number | null>(null);
  const [, setMultimeterStartTime] = useState<number | null>(null);
  const [lockinEs, setLockinEs] = useState<EventSource | null>(null);
  const [multimeterEs, setMultimeterEs] = useState<EventSource | null>(null);
  const [stageEs, setStageEs] = useState<EventSource | null>(null);
  const [status, setStatus] = useState<string>('');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [settings, setSettings] = useState<Settings>({
    channel1: { homingVelocity: '', maxVelocity: '', acceleration: '' },
    channel2: { homingVelocity: '', maxVelocity: '', acceleration: '' },
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [scanData, setScanData] = useState<ScanDataPoint[]>([]);
  const [defaultSaveDir, setDefaultSaveDir] = useState('');
  const [scanFormData, setScanFormData] = useState<FormData | null>(null);
  const scanDataEsRef = useRef<EventSource | null>(null);
  const prevIsProcessingRef = useRef(false);

  // Pre-fill x1, y1 with current stage position on mount
  useEffect(() => {
    fetch(`${API_BASE}/default-save-dir`)
      .then((res) => res.json())
      .then((data) => setDefaultSaveDir(data.directory))
      .catch(() => {});
  }, []);

  // Close device streams when scan completes (isProcessing: true → false)
  useEffect(() => {
    if (prevIsProcessingRef.current && !isProcessing) {
      disconnectLockin();
      disconnectMultimeter();
      disconnectStage();
    }
    prevIsProcessingRef.current = isProcessing;
  });

  const settingsButtonRef = useRef<HTMLButtonElement | null>(null);
  const settingsMenuRef = useRef<HTMLDivElement | null>(null);

  useClickOutside(settingsMenuRef, () => {
    if (isSettingsOpen) setIsSettingsOpen(false);
  });

  const defaultSettings: Settings = {
    channel1: {
      homingVelocity: '10',
      maxVelocity: '100',
      acceleration: '1000',
    },
    channel2: {
      homingVelocity: '10',
      maxVelocity: '100',
      acceleration: '1000',
    },
  };

  const connectLockin = () => {
    if (lockinEs) lockinEs.close();
    const es = new EventSource(`${API_BASE}/sse/lockin`);
    es.onopen = () => {
      setLockinConnected(true);
      setLockinStartTime(Date.now());
    };
    es.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.error) {
        es.close();
        setLockinConnected(false);
        setLockinEs(null);
        return;
      }
      setLockinData(data);
    };
    es.onerror = () => {
      es.close();
      setLockinConnected(false);
      setLockinEs(null);
    };
    setLockinEs(es);
  };
  const fetchLockinSettings = async () => {
    try {
      const response = await fetch(`${API_BASE}/lockin/settings`);
      const data = await response.json();
      if (data.status === 'success') {
        setLockinSettings({
          sensitivity: data.sensitivity,
          timeConstant: data.time_constant,
          frequency: data.frequency,
          filterSlope: data.filter_slope,
        });
      } else {
        console.error('Failed to fetch lock-in settings:', data.message);
        setStatus('Error fetching lock-in settings');
      }
    } catch (error) {
      console.error('Error fetching lock-in settings:', error);
      setStatus('Error fetching lock-in settings');
    }
  };

  const disconnectLockin = () => {
    if (lockinEs) lockinEs.close();
    setLockinEs(null);
    setLockinConnected(false);
    setLockinStartTime(null);
  };

  const resetLockin = () => {
    setLockinData({
      X: 0,
      Y: 0,
      frequency: 0,
    });
    setResetLockinTrigger(true);
    if (lockinConnected) {
      setLockinStartTime(Date.now());
    } else {
      setLockinStartTime(null);
    }
  };

  const connectMultimeter = () => {
    if (multimeterEs) multimeterEs.close();
    const es = new EventSource(`${API_BASE}/sse/multimeter`);
    es.onopen = () => {
      setMultimeterConnected(true);
      setMultimeterStartTime(Date.now());
    };
    es.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.error) {
        es.close();
        setMultimeterConnected(false);
        setMultimeterEs(null);
        return;
      }
      setMultimeterData(data);
    };
    es.onerror = () => {
      es.close();
      setMultimeterConnected(false);
      setMultimeterEs(null);
    };
    setMultimeterEs(es);
  };

  const disconnectMultimeter = () => {
    if (multimeterEs) multimeterEs.close();
    setMultimeterEs(null);
    setMultimeterConnected(false);
    setMultimeterStartTime(null);
  };

  const resetMultimeter = () => {
    setMultimeterData({
      value: 0,
    });
    setResetMultimeterTrigger(true);
    if (multimeterConnected) {
      setMultimeterStartTime(Date.now());
    } else {
      setMultimeterStartTime(null);
    }
  };

  const connectStage = () => {
    if (stageEs) stageEs.close();
    const es = new EventSource(`${API_BASE}/sse/stage`);
    es.onopen = () => {
      setStageConnected(true);
    };
    es.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.error) {
        es.close();
        setStageConnected(false);
        setStageEs(null);
        return;
      }
      setStageData(data);
    };
    es.onerror = () => {
      es.close();
      setStageConnected(false);
      setStageEs(null);
    };
    setStageEs(es);
  };

  const disconnectStage = () => {
    if (stageEs) stageEs.close();
    setStageEs(null);
    setStageConnected(false);
  };

  const resetStage = () => {
    setStageData({
      x: 0,
      y: 0,
    });
  };

  const handleBrowseSaveDir = async () => {
    const currentDir = formData.saveDir || defaultSaveDir;
    const res = await fetch(
      `${API_BASE}/choose-save-dir?initialdir=${encodeURIComponent(currentDir)}`
    );
    const { directory } = await res.json();
    if (directory) {
      setFormData((prev) => ({ ...prev, saveDir: directory }));
    }
  };

  const handleSubmit = async () => {
    try {
      setStatus('Connecting devices...');
      if (!lockinConnected) await connectLockin();
      if (!multimeterConnected) await connectMultimeter();
      if (!stageConnected) await connectStage();

      setIsProcessing(true);
      setScanData([]);
      setScanFormData({ ...formData });
      setStatus('Scanning...');

      // Connect scan data SSE before starting scan
      const scanEs = new EventSource(`${API_BASE}/sse/scan_data`);
      scanEs.onmessage = (event) => {
        const point = JSON.parse(event.data);
        if (point.type === 'scan_complete') {
          scanEs.close();
          setIsProcessing(false);
          setStatus('Scan completed');
        } else {
          setScanData((prev) => [...prev, point]);
        }
      };
      scanEs.onerror = () => {
        scanEs.close();
      };
      scanDataEsRef.current = scanEs;

      const response = await fetch(`${API_BASE}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          x1: parseFloat(formData.x1),
          x2: parseFloat(formData.x2),
          y1: parseFloat(formData.y1),
          y2: parseFloat(formData.y2),
          x_steps: parseInt(formData.xSteps) || null,
          y_steps: parseInt(formData.ySteps) || null,
          x_step_size: parseFloat(formData.xStepSize) || null,
          y_step_size: parseFloat(formData.yStepSize) || null,
          movement_mode: formData.movementMode,
          delay: parseFloat(formData.delay) || null,
          motion_type: formData.motionType,
          scan_pattern: formData.scanPattern,
          record_retrace: formData.recordRetrace,
          fast_axis: formData.fastAxis,
          sample_id: formData.sampleId,
          comments: formData.comments,
          save_dir: formData.saveDir,
        }),
      });
      const data = await response.json();
      if (data.status === 'error') {
        setStatus(data.message);
        setIsProcessing(false);
        if (scanDataEsRef.current) {
          scanDataEsRef.current.close();
        }
      }
    } catch (error) {
      console.error('Error:', error);
      setIsProcessing(false);
      setStatus('Error occurred');
      if (scanDataEsRef.current) {
        scanDataEsRef.current.close();
      }
    }
  };

  const handleStop = async () => {
    try {
      setStatus('Stopping...');
      await fetch(`${API_BASE}/stop`, { method: 'POST' });
      setIsProcessing(false);
      if (scanDataEsRef.current) {
        scanDataEsRef.current.close();
      }
      setStatus('Motion stopped');
    } catch (error) {
      console.error('Error stopping:', error);
      setStatus('Error stopping motion');
    }
  };

  const handleHome = async (channel_direction: string) => {
    try {
      setStatus('Processing...');
      const response = await fetch(`${API_BASE}/home`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel_direction }),
      });
      const data = await response.json();
      setStatus(data.message);
    } catch (error) {
      console.error('Error:', error);
      setStatus('Error occurred');
    }
  };

  const handleGetParams = async () => {
    try {
      const response = await fetch(`${API_BASE}/get_movement_params`);
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
      console.error('Error:', error);
      setStatus('Error occurred');
    }
  };

  const handleSetParams = async (newSettings: Settings) => {
    try {
      const response = await fetch(`${API_BASE}/set_movement_params`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel1: {
            homing_velocity: parseFloat(newSettings.channel1.homingVelocity),
            max_velocity: parseFloat(newSettings.channel1.maxVelocity),
            acceleration: parseFloat(newSettings.channel1.acceleration),
          },
          channel2: {
            homing_velocity: parseFloat(newSettings.channel2.homingVelocity),
            max_velocity: parseFloat(newSettings.channel2.maxVelocity),
            acceleration: parseFloat(newSettings.channel2.acceleration),
          },
        }),
      });
      const data = await response.json();
      if (data.status === 'success') console.log('success');
    } catch (error) {
      console.error('Error:', error);
      setStatus('Error occurred');
    }
  };

  const changeLockinSensitivity = async (increment: boolean) => {
    try {
      const response = await fetch(`${API_BASE}/lockin/sensitivity`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ increment }),
      });
      const data = await response.json();
      console.log(data);
      if (data.status === 'success') {
        setLockinSettings((prev) => ({
          ...prev,
          sensitivity: data.sensitivity,
        }));
      }
    } catch (error) {
      console.error('Error changing sensitivity:', error);
      setStatus('Error changing sensitivity');
    }
  };

  const changeLockinTimeConstant = async (increment: boolean) => {
    try {
      const response = await fetch(`${API_BASE}/lockin/time_constant`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ increment }),
      });
      const data = await response.json();
      console.log(data);
      if (data.status === 'success') {
        setLockinSettings((prev) => ({
          ...prev,
          timeConstant: data.time_constant,
        }));
      }
    } catch (error) {
      console.error('Error changing time constant:', error);
      setStatus('Error changing time constant');
    }
  };

  const changeLockinFrequency = async (frequency: number) => {
    try {
      const response = await fetch(`${API_BASE}/lockin/frequency`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ frequency }),
      });
      const data = await response.json();
      if (data.status === 'success') {
        setLockinSettings((prev) => ({ ...prev, frequency: data.frequency }));
      }
    } catch (error) {
      console.error('Error setting frequency:', error);
      setStatus('Error setting frequency');
    }
  };

  const changeLockinFilterSlope = async (code: number) => {
    try {
      const response = await fetch(`${API_BASE}/lockin/filter_slope`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });
      const data = await response.json();
      if (data.status === 'success') {
        setLockinSettings((prev) => ({ ...prev, filterSlope: data.filter_slope }));
      }
    } catch (error) {
      console.error('Error setting filter slope:', error);
      setStatus('Error setting filter slope');
    }
  };

  const fetchMultimeterSettings = async () => {
    try {
      const response = await fetch(`${API_BASE}/multimeter/settings`);
      const data = await response.json();
      console.log(data);
      if (data.status === 'success') {
        setMultimeterSettings({
          aperture: data.aperture,
          terminal: data.terminal,
        });
      } else {
        console.error('Failed to fetch multimeter settings:', data.message);
        setStatus('Error fetching multimeter settings');
      }
    } catch (error) {
      console.error('Error fetching multimeter settings:', error);
      setStatus('Error fetching multimeter settings');
    }
  };

  const changeMultimeterAperture = async (nplc: number) => {
    try {
      const response = await fetch(`${API_BASE}/multimeter/aperture`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nplc }),
      });
      const data = await response.json();
      if (data.status === 'success') {
        setMultimeterSettings((prev) => ({
          ...prev,
          aperture: data.aperture,
        }));
      } else {
        console.error('Failed to set aperture:', data.message);
        setStatus('Error setting aperture');
      }
    } catch (error) {
      console.error('Error setting aperture:', error);
      setStatus('Error setting aperture');
    }
  };

  const changeMultimeterTerminal = async (terminal: string) => {
    try {
      const response = await fetch(`${API_BASE}/multimeter/terminal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ terminal }),
      });
      const data = await response.json();
      if (data.status === 'success') {
        setMultimeterSettings((prev) => ({
          ...prev,
          terminal: data.terminal,
        }));
      } else {
        console.error('Failed to set terminal:', data.message);
        setStatus('Error setting terminal');
      }
    } catch (error) {
      console.error('Error setting terminal:', error);
      setStatus('Error setting terminal');
    }
  };

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-gray-900">
      {/* Top Bar */}
      <header className="flex items-center justify-between bg-gray-800 p-4">
        <h1 className="text-xl font-semibold text-white">Experiment Dashboard</h1>
        <div className="flex space-x-4">
          <Link href="/fdpbd" className="text-white hover:text-teal-400">
            Analysis
          </Link>
          <button
            ref={settingsButtonRef}
            onClick={() => {
              handleGetParams();
              setIsSettingsOpen(true);
            }}
            className="text-white hover:text-teal-400"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex flex-1 space-x-4 p-4">
        {/* Left Panel */}
        <div className="flex w-1/3 flex-col space-y-4">
          <MetadataPanel
            formData={formData}
            setFormData={setFormData}
            onBrowseSaveDir={handleBrowseSaveDir}
            defaultSaveDir={defaultSaveDir}
          />
          <DeviceControls
            formData={formData}
            setFormData={setFormData}
            handleSubmit={handleSubmit}
            handleStop={handleStop}
            handleHome={handleHome}
            status={status}
            isProcessing={isProcessing}
            lockinSettings={lockinSettings}
            changeLockinSensitivity={changeLockinSensitivity}
            changeLockinTimeConstant={changeLockinTimeConstant}
            changeLockinFrequency={changeLockinFrequency}
            changeLockinFilterSlope={changeLockinFilterSlope}
            fetchLockinSettings={fetchLockinSettings}
            lockinConnected={lockinConnected}
            multimeterSettings={multimeterSettings}
            fetchMultimeterSettings={fetchMultimeterSettings}
            changeMultimeterAperture={changeMultimeterAperture}
            changeMultimeterTerminal={changeMultimeterTerminal}
            multimeterConnected={multimeterConnected}
          />
        </div>

        {/* Center Panel */}
        <div className="flex w-1/2 flex-col space-y-4">
          <LiveScanPanel
            scanData={scanData}
            formData={scanFormData ?? formData}
            isProcessing={isProcessing}
          />
        </div>

        {/* Right Panel */}
        <OutputPanel
          lockinData={lockinData}
          multimeterData={multimeterData}
          stageData={stageData}
          lockinConnected={lockinConnected}
          multimeterConnected={multimeterConnected}
          stageConnected={stageConnected}
          connectLockin={connectLockin}
          disconnectLockin={disconnectLockin}
          connectMultimeter={connectMultimeter}
          disconnectMultimeter={disconnectMultimeter}
          connectStage={connectStage}
          disconnectStage={disconnectStage}
          resetLockin={resetLockin}
          resetMultimeter={resetMultimeter}
          resetStage={resetStage}
          isProcessing={isProcessing}
        />
      </div>

      {/* Settings Panel */}
      <AnimatePresence>
        {isSettingsOpen && (
          <SettingsPanel
            ref={settingsMenuRef}
            settings={settings}
            setSettings={setSettings}
            defaultSettings={defaultSettings}
            handleSetParams={handleSetParams}
            setIsSettingsOpen={setIsSettingsOpen}
            top={
              settingsButtonRef.current
                ? settingsButtonRef.current.offsetTop + settingsButtonRef.current.offsetHeight + 8
                : 0
            }
          />
        )}
      </AnimatePresence>
    </div>
  );
}
