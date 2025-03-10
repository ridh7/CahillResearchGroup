"use client";

import { useState, useRef, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import MetadataPanel from "../components/MetadataPanel";
import DeviceControls from "../components/DeviceControls";
import GraphsPanel from "../components/GraphsPanel";
import OutputPanel from "../components/OutputPanel";
import SettingsPanel from "../components/SettingsPanel";

export type FormData = {
  sampleId: string;
  sampleName: string;
  probeLaserPower: string;
  pumpLaserPower: string;
  aluminumThickness: string;
  comments: string;
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
};

export type LockinData = {
  X: number;
  Y: number;
  R: number;
  unit: string;
  theta: number;
  frequency: number;
  phase: number;
};

export type MultimeterData = {
  value: number;
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
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [ref, handler]);
}

export default function CalculatePage() {
  const [formData, setFormData] = useState<FormData>({
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
    delay: "",
  });

  const [lockinData, setLockinData] = useState<LockinData>({
    X: 0,
    Y: 0,
    R: 0,
    unit: "",
    theta: 0,
    frequency: 0,
    phase: 0,
  });
  const [multimeterData, setMultimeterData] = useState<MultimeterData>({
    value: 0,
  });
  const [stageData, setStageData] = useState<StageData>({
    x: 0,
    y: 0,
  });
  const [lockinConnected, setLockinConnected] = useState(false);
  const [multimeterConnected, setMultimeterConnected] = useState(false);
  const [stageConnected, setStageConnected] = useState(false);
  const [resetLockinTrigger, setResetLockinTrigger] = useState(false);
  const [resetMultimeterTrigger, setResetMultimeterTrigger] = useState(false);
  const [lockinStartTime, setLockinStartTime] = useState<number | null>(null);
  const [multimeterStartTime, setMultimeterStartTime] = useState<number | null>(
    null
  );
  const [lockinWs, setLockinWs] = useState<WebSocket | null>(null);
  const [multimeterWs, setMultimeterWs] = useState<WebSocket | null>(null);
  const [stageWs, setStageWs] = useState<WebSocket | null>(null);
  const [status, setStatus] = useState<string>("");
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [settings, setSettings] = useState<Settings>({
    channel1: { homingVelocity: "", maxVelocity: "", acceleration: "" },
    channel2: { homingVelocity: "", maxVelocity: "", acceleration: "" },
  });
  const [isProcessing, setIsProcessing] = useState(false);

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

  const connectLockin = () => {
    return new Promise<void>((resolve, reject) => {
      if (lockinWs) {
        switch (lockinWs.readyState) {
          case WebSocket.OPEN:
            console.log("Lockin WebSocket already open, reusing it");
            setLockinConnected(true);
            setLockinStartTime(Date.now());
            resolve();
            return;
          case WebSocket.CLOSING:
          case WebSocket.CLOSED:
            console.log("Cleaning up stale Locking WebSocket");
            lockinWs.close();
            setLockinWs(null);
            break;
          case WebSocket.CONNECTING:
            console.log("Lockin WebSocket already connecting, waiting...");
            lockinWs.onopen = () => {
              setLockinConnected(true);
              setLockinStartTime(Date.now());
              resolve();
            };
            lockinWs.onerror = () => {
              reject(new Error("Locking connection failed"));
            };
            return;
        }
      }

      console.log("Creating new Lockin WebSocket");
      const ws = new WebSocket("ws://localhost:8000/ws/lockin");

      ws.onopen = () => {
        console.log("Lockin WebSocket connected");
        setLockinConnected(true);
        setLockinStartTime(Date.now());
        resolve();
      };

      ws.onmessage = (event) => {
        setLockinData(JSON.parse(event.data));
      };

      ws.onerror = () => {
        console.error("Lockin WebSocket error");
        setLockinConnected(false);
        setLockinWs(null);
        reject(new Error("Lockin WebSocket encountered an error"));
      };

      ws.onclose = () => {
        console.log("Lockin WebSocket closed");
        setLockinConnected(false);
        setLockinWs(null);
      };

      setLockinWs(ws);
    });
  };

  const disconnectLockin = () => {
    return new Promise<void>((resolve) => {
      console.log(
        "Disconnecting lockin, current state: ",
        lockinWs?.readyState
      );
      if (!lockinWs || lockinWs.readyState === WebSocket.CLOSED) {
        console.log("Locking already closed");
        setLockinWs(null);
        setLockinConnected(false);
        setLockinStartTime(null);
        resolve();
        return;
      }
      if (lockinWs.readyState === WebSocket.CLOSING) {
        console.log("Locking already closing");
        lockinWs.onclose = () => {
          console.log("Lockin closed");
          setLockinWs(null);
          setLockinConnected(false);
          setLockinStartTime(null);
          resolve();
        };
        return;
      }
      lockinWs.onclose = () => {
        console.log("Lockin closed");
        setLockinWs(null);
        setLockinConnected(false);
        setLockinStartTime(null);
        resolve();
      };
      lockinWs?.close();
    });
  };

  const resetLockin = () => {
    setLockinData({
      X: 0,
      Y: 0,
      R: 0,
      unit: "",
      theta: 0,
      frequency: 0,
      phase: 0,
    });
    setResetLockinTrigger(true);
    if (lockinConnected) {
      setLockinStartTime(Date.now());
    } else {
      setLockinStartTime(null);
    }
  };

  const connectMultimeter = () => {
    return new Promise<void>((resolve, reject) => {
      if (multimeterWs) {
        switch (multimeterWs.readyState) {
          case WebSocket.OPEN:
            console.log("Multimeter WebSocket already open, reusing it");
            setMultimeterConnected(true);
            setMultimeterStartTime(Date.now());
            resolve();
            return;
          case WebSocket.CLOSING:
          case WebSocket.CLOSED:
            console.log("Cleaning up stale Multimeter WebSocket");
            multimeterWs.close();
            setMultimeterWs(null);
            break;
          case WebSocket.CONNECTING:
            console.log("Multimeter WebSocket already connecting, waiting...");
            multimeterWs.onopen = () => {
              setMultimeterConnected(true);
              setMultimeterStartTime(Date.now());
              resolve();
            };
            multimeterWs.onerror = () => {
              reject(new Error("Multimeter connection failed"));
            };
            return;
        }
      }

      console.log("Creating new Multimeter WebSocket");
      const ws = new WebSocket("ws://localhost:8000/ws/multimeter");

      ws.onopen = () => {
        console.log("Multimeter WebSocket connected");
        setMultimeterConnected(true);
        setMultimeterStartTime(Date.now());
        resolve();
      };

      ws.onmessage = (event) => {
        setMultimeterData(JSON.parse(event.data));
      };

      ws.onerror = () => {
        console.error("Multimeter WebSocket error");
        setMultimeterConnected(false);
        setMultimeterWs(null);
        reject(new Error("Multimeter WebSocket encountered an error"));
      };

      ws.onclose = () => {
        console.log("Multimeter WebSocket closed");
        setMultimeterConnected(false);
        setMultimeterWs(null);
      };

      setMultimeterWs(ws);
    });
  };

  const disconnectMultimeter = () => {
    return new Promise<void>((resolve) => {
      console.log(
        "Disconnecting multimeter, current state: ",
        multimeterWs?.readyState
      );
      if (!multimeterWs || multimeterWs.readyState === WebSocket.CLOSED) {
        console.log("Multimeter already closed");
        setMultimeterWs(null);
        setMultimeterConnected(false);
        setMultimeterStartTime(null);
        resolve();
        return;
      }
      if (multimeterWs.readyState === WebSocket.CLOSING) {
        console.log("Multimeter already closing");
        multimeterWs.onclose = () => {
          console.log("Multimeter closed");
          setMultimeterWs(null);
          setMultimeterConnected(false);
          setMultimeterStartTime(null);
          resolve();
        };
        return;
      }
      multimeterWs.onclose = () => {
        console.log("Multimeter closed");
        setMultimeterWs(null);
        setMultimeterConnected(false);
        setMultimeterStartTime(null);
        resolve();
      };
      multimeterWs?.close();
    });
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
    return new Promise<void>((resolve, reject) => {
      if (stageWs) {
        switch (stageWs.readyState) {
          case WebSocket.OPEN:
            console.log("Stage WebSocket already open, reusing it");
            setStageConnected(true);
            resolve();
            return;
          case WebSocket.CLOSING:
          case WebSocket.CLOSED:
            console.log("Cleaning up stale Stage WebSocket");
            stageWs.close();
            setStageWs(null);
            break;
          case WebSocket.CONNECTING:
            console.log("Stage WebSocket already connecting, waiting...");
            stageWs.onopen = () => {
              setStageConnected(true);
              resolve();
            };
            stageWs.onerror = () => {
              reject(new Error("Stage connection failed"));
            };
            return;
        }
      }

      console.log("Creating new Stage WebSocket");
      const ws = new WebSocket("ws://localhost:8000/ws/stage");

      ws.onopen = () => {
        console.log("Stage WebSocket connected");
        setStageConnected(true);
        resolve();
      };

      ws.onmessage = (event) => {
        setStageData(JSON.parse(event.data));
      };

      ws.onerror = () => {
        console.error("Stage WebSocket error");
        setStageConnected(false);
        setStageWs(null);
        reject(new Error("Stage WebSocket encountered an error"));
      };

      ws.onclose = () => {
        console.log("Stage WebSocket closed");
        setStageConnected(false);
        setStageWs(null);
      };

      setStageWs(ws);
    });
  };

  const disconnectStage = () => {
    return new Promise<void>((resolve) => {
      console.log("Disconnecting stage, current state: ", stageWs?.readyState);
      if (!stageWs || stageWs.readyState === WebSocket.CLOSED) {
        setStageWs(null);
        setStageConnected(false);
        resolve();
        return;
      }
      if (stageWs.readyState === WebSocket.CLOSING) {
        console.log("Stage already closing");
        stageWs.onclose = () => {
          console.log("Stage closed");
          setStageWs(null);
          setStageConnected(false);
          resolve();
        };
        return;
      }
      stageWs.onclose = () => {
        console.log("Stage closed");
        setStageWs(null);
        setStageConnected(false);
        resolve();
      };
      stageWs?.close();
    });
  };

  const resetStage = () => {
    setStageData({
      x: 0,
      y: 0,
    });
  };

  const waitForCondition = (
    condition: () => boolean,
    timeoutMs: number
  ): Promise<void> => {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      const check = () => {
        if (condition()) {
          resolve();
        } else if (Date.now() - startTime > timeoutMs) {
          reject(new Error("Timeout waiting for condition"));
        } else {
          setTimeout(check, 100);
        }
      };
      check();
    });
  };

  const handleSubmit = async () => {
    try {
      setStatus("Connecting devices...");
      if (!lockinConnected) await connectLockin();
      if (!multimeterConnected) await connectMultimeter();
      if (!stageConnected) await connectStage();
      await Promise.all([
        !lockinConnected
          ? waitForCondition(() => lockinConnected, 5000)
          : Promise.resolve(),
        !multimeterConnected
          ? waitForCondition(() => multimeterConnected, 5000)
          : Promise.resolve(),
        !stageConnected
          ? waitForCondition(() => stageConnected, 5000)
          : Promise.resolve(),
      ]).catch((error) => {
        throw new Error("Failed to connect all devices: " + error.message);
      });

      resetLockin();
      resetMultimeter();
      resetStage();

      setIsProcessing(true);
      setStatus("Processing...");

      const response = await fetch("http://localhost:8000/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
        }),
      });
      const data = await response.json();
      setStatus(data.message);

      setIsProcessing(false);
      await Promise.all([
        disconnectLockin(),
        disconnectMultimeter(),
        disconnectStage(),
      ]);
    } catch (error) {
      console.error("Error:", error);
      setIsProcessing(false);
      await Promise.all([
        disconnectLockin(),
        disconnectMultimeter(),
        disconnectStage(),
      ]);
      setStatus("Error occurred");
    }
  };

  const handleHome = async (channel_direction: string) => {
    try {
      setStatus("Processing...");
      const response = await fetch("http://localhost:8000/home", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel_direction }),
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
      const response = await fetch("http://localhost:8000/get_movement_params");
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

  const handleSetParams = async (newSettings: Settings) => {
    try {
      const response = await fetch(
        "http://localhost:8000/set_movement_params",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
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
        }
      );
      const data = await response.json();
      if (data.status === "success") console.log("success");
    } catch (error) {
      console.error("Error:", error);
      setStatus("Error occurred");
    }
  };

  const handleResetComplete = () => {
    setResetLockinTrigger(false);
    setResetMultimeterTrigger(false);
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      {/* Top Bar */}
      <header className="bg-gray-800 p-4 flex justify-between items-center">
        <h1 className="text-white text-xl font-semibold">
          Experiment Dashboard
        </h1>
        <button
          ref={settingsButtonRef}
          onClick={() => {
            handleGetParams();
            setIsSettingsOpen(true);
          }}
          className="text-white hover:text-teal-400"
        >
          <svg
            className="w-6 h-6"
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
      </header>

      {/* Main Layout */}
      <div className="flex flex-1 p-4 space-x-4">
        {/* Left Panel */}
        <div className="w-1/3 flex flex-col space-y-4">
          <MetadataPanel formData={formData} setFormData={setFormData} />
          <DeviceControls
            formData={formData}
            setFormData={setFormData}
            handleSubmit={handleSubmit}
            handleHome={handleHome}
            status={status}
          />
        </div>

        {/* Center Panel */}
        <GraphsPanel
          lockinData={lockinData}
          multimeterData={multimeterData}
          lockinConnected={lockinConnected}
          multimeterConnected={multimeterConnected}
          resetLockin={resetLockinTrigger}
          resetMultimeter={resetMultimeterTrigger}
          onResetComplete={handleResetComplete}
          lockinStartTime={lockinStartTime}
          multimeterStartTime={multimeterStartTime}
        />

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
                ? settingsButtonRef.current.offsetTop +
                  settingsButtonRef.current.offsetHeight +
                  8
                : 0
            }
          />
        )}
      </AnimatePresence>

      {/* Status Bar */}
      <footer className="bg-gray-800 p-2 text-white text-sm flex justify-between">
        <div>
          Stage: Connected | Lock-in:{" "}
          {lockinConnected ? "Connected" : "Disconnected"} | Multimeter:{" "}
          {multimeterConnected ? "Connected" : "Disconnected"}
        </div>
        <div>{new Date().toLocaleString()}</div>
      </footer>
    </div>
  );
}
