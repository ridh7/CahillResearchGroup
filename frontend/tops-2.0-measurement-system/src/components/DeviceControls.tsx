import { useState, useMemo } from 'react';
import { FormData, Settings } from '../app/page';

type DeviceControlsProps = {
  formData: FormData;
  setFormData: React.Dispatch<React.SetStateAction<FormData>>;
  handleSubmit: () => void;
  handleStop: () => void;
  handleHome: (direction: string) => void;
  status: string;
  isProcessing: boolean;
  lockinSettings: {
    sensitivity: number;
    timeConstant: number;
    frequency: number;
    filterSlope: number;
  };
  changeLockinSensitivity: (increment: boolean) => void;
  changeLockinTimeConstant: (increment: boolean) => void;
  changeLockinFrequency: (frequency: number) => void;
  changeLockinFilterSlope: (code: number) => void;
  fetchLockinSettings: () => void;
  lockinConnected: boolean;
  multimeterSettings: { aperture: number; terminal: string };
  fetchMultimeterSettings: () => Promise<void>;
  changeMultimeterAperture: (nplc: number) => void;
  changeMultimeterTerminal: (terminal: string) => void;
  multimeterConnected: boolean;
  settings: Settings;
};

const initialFormData: FormData = {
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
  delay: '1',
  motionType: 'step_and_measure',
  scanPattern: 'bidirectional',
  recordRetrace: false,
  fastAxis: 'y',
};

export default function DeviceControls({
  formData,
  setFormData,
  handleSubmit,
  handleStop,
  handleHome,
  status,
  isProcessing,
  lockinSettings,
  changeLockinSensitivity,
  changeLockinTimeConstant,
  changeLockinFrequency,
  changeLockinFilterSlope,
  fetchLockinSettings,
  multimeterSettings,
  changeMultimeterAperture,
  changeMultimeterTerminal,
  fetchMultimeterSettings,
  settings,
}: DeviceControlsProps) {
  const [activeTab, setActiveTab] = useState<'stage' | 'lockin' | 'multimeter'>('stage');
  const [freqInput, setFreqInput] = useState('');
  const [moveX, setMoveX] = useState('');
  const [moveY, setMoveY] = useState('');
  const [isMoving, setIsMoving] = useState(false);

  const fetchCurrentPosition = async (field: 'x1' | 'y1' | 'x2' | 'y2') => {
    try {
      const res = await fetch('http://localhost:8000/get_current_position');
      const data = await res.json();
      if (data.status === 'success') {
        const value =
          field === 'x1' || field === 'x2'
            ? parseFloat(data.x).toFixed(4)
            : parseFloat(data.y).toFixed(4);
        setFormData((prev) => ({ ...prev, [field]: value }));
      }
    } catch (e) {
      console.error('Failed to fetch position:', e);
    }
  };

  const handleMoveTo = async () => {
    const x = parseFloat(moveX);
    const y = parseFloat(moveY);
    if (isNaN(x) || isNaN(y) || x < 0 || x > 110 || y < 0 || y > 75) return;
    setIsMoving(true);
    try {
      await fetch('http://localhost:8000/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x, y }),
      });
    } catch (error) {
      console.error('Move error:', error);
    } finally {
      setIsMoving(false);
    }
  };

  const isMoveValid =
    moveX !== '' &&
    moveY !== '' &&
    !isNaN(Number(moveX)) &&
    !isNaN(Number(moveY)) &&
    Number(moveX) >= 0 &&
    Number(moveX) <= 110 &&
    Number(moveY) >= 0 &&
    Number(moveY) <= 75;

  const handleReset = () => {
    setFormData(initialFormData);
  };

  const isFormValid = useMemo(() => {
    const x1Valid = formData.x1 !== '' && Number(formData.x1) >= 0 && Number(formData.x1) <= 110;
    const x2Valid = formData.x2 !== '' && Number(formData.x2) >= 0 && Number(formData.x2) <= 110;
    const y1Valid = formData.y1 !== '' && Number(formData.y1) >= 0 && Number(formData.y1) <= 75;
    const y2Valid = formData.y2 !== '' && Number(formData.y2) >= 0 && Number(formData.y2) <= 75;
    const coordsValid = x1Valid && x2Valid && y1Valid && y2Valid;

    if (formData.motionType === 'continuous') {
      if (formData.movementMode === 'steps') {
        const xStepsValid =
          formData.xSteps !== '' &&
          Number(formData.xSteps) > 0 &&
          Number.isInteger(Number(formData.xSteps));
        const yStepsValid =
          formData.ySteps !== '' &&
          Number(formData.ySteps) > 0 &&
          Number.isInteger(Number(formData.ySteps));
        return coordsValid && xStepsValid && yStepsValid;
      }
      const xStepValid = formData.xStepSize !== '' && Number(formData.xStepSize) > 0;
      const yStepValid = formData.yStepSize !== '' && Number(formData.yStepSize) > 0;
      return coordsValid && xStepValid && yStepValid;
    }

    // Step-and-measure mode: delay is required
    const delayValid =
      formData.delay !== '' && Number(formData.delay) >= 0 && !isNaN(Number(formData.delay));

    if (formData.movementMode === 'steps') {
      const xStepsValid =
        formData.xSteps !== '' &&
        Number(formData.xSteps) > 0 &&
        Number.isInteger(Number(formData.xSteps));
      const yStepsValid =
        formData.ySteps !== '' &&
        Number(formData.ySteps) > 0 &&
        Number.isInteger(Number(formData.ySteps));
      return coordsValid && xStepsValid && yStepsValid && delayValid;
    } else {
      const xStepSizeValid = formData.xStepSize !== '' && Number(formData.xStepSize) > 0;
      const yStepSizeValid = formData.yStepSize !== '' && Number(formData.yStepSize) > 0;
      return coordsValid && xStepSizeValid && yStepSizeValid && delayValid;
    }
  }, [formData]);

  const estimatedTime = useMemo(() => {
    if (!isFormValid) return null;

    const x1 = parseFloat(formData.x1);
    const x2 = parseFloat(formData.x2);
    const y1 = parseFloat(formData.y1);
    const y2 = parseFloat(formData.y2);
    const xDist = Math.abs(x2 - x1);
    const yDist = Math.abs(y2 - y1);

    // Determine fast/slow axis distances
    const fastDist = formData.fastAxis === 'x' ? xDist : yDist;
    const slowDist = formData.fastAxis === 'x' ? yDist : xDist;

    // Get velocity/acceleration for each axis (channel1=X, channel2=Y)
    const fastSettings = formData.fastAxis === 'x' ? settings.channel1 : settings.channel2;
    const slowSettings = formData.fastAxis === 'x' ? settings.channel2 : settings.channel1;
    const fastVel = parseFloat(fastSettings.maxVelocity);
    const fastAcc = parseFloat(fastSettings.acceleration);
    const slowVel = parseFloat(slowSettings.maxVelocity);
    const slowAcc = parseFloat(slowSettings.acceleration);

    if (!fastVel || !fastAcc || !slowVel || !slowAcc) return null;

    // Trapezoidal motion time: time to travel distance d with max velocity v and acceleration a
    const motionTime = (d: number, v: number, a: number) => {
      if (d <= 0) return 0;
      const tAccel = v / a;
      const dAccel = v * tAccel; // distance during accel+decel phases
      if (d < dAccel) {
        // Never reaches max velocity: t = 2 * sqrt(d/a)
        return 2 * Math.sqrt(d / a);
      }
      // Reaches max velocity: accel + cruise + decel
      return d / v + v / a;
    };

    // Compute number of slow axis steps
    let numSlowSteps: number;
    let slowStepSize: number;
    if (formData.movementMode === 'steps') {
      const fastSteps =
        formData.fastAxis === 'x' ? parseInt(formData.xSteps) : parseInt(formData.ySteps);
      const slowSteps =
        formData.fastAxis === 'x' ? parseInt(formData.ySteps) : parseInt(formData.xSteps);
      numSlowSteps = slowSteps;
      slowStepSize = numSlowSteps > 0 ? slowDist / numSlowSteps : 0;
      // fastSteps used only for step_and_measure
      void fastSteps;
    } else {
      const fastStepSz =
        formData.fastAxis === 'x' ? parseFloat(formData.xStepSize) : parseFloat(formData.yStepSize);
      slowStepSize =
        formData.fastAxis === 'x' ? parseFloat(formData.yStepSize) : parseFloat(formData.xStepSize);
      numSlowSteps = slowStepSize > 0 ? Math.ceil(slowDist / slowStepSize) : 0;
      void fastStepSz;
    }

    const numSweeps = numSlowSteps + 1;
    const sweepTime = motionTime(fastDist, fastVel, fastAcc);
    const slowStepTime = motionTime(slowStepSize, slowVel, slowAcc);

    let totalSeconds: number;

    if (formData.motionType === 'continuous') {
      // Continuous scan
      const retraceTime =
        formData.scanPattern === 'unidirectional'
          ? motionTime(fastDist, 100, 1000) // fast retrace: 100 mm/s, 1000 mm/s²
          : 0;
      // Each sweep: move fast axis + step slow axis (+ retrace if unidirectional)
      totalSeconds = numSweeps * sweepTime + numSlowSteps * (slowStepTime + retraceTime);
    } else {
      // Step & measure
      let numFastSteps: number;
      if (formData.movementMode === 'steps') {
        numFastSteps =
          formData.fastAxis === 'x' ? parseInt(formData.xSteps) : parseInt(formData.ySteps);
      } else {
        const fastStepSz =
          formData.fastAxis === 'x'
            ? parseFloat(formData.xStepSize)
            : parseFloat(formData.yStepSize);
        numFastSteps = fastStepSz > 0 ? Math.ceil(fastDist / fastStepSz) : 0;
      }
      const fastStepSzActual = numFastSteps > 0 ? fastDist / numFastSteps : 0;
      const totalPoints = (numFastSteps + 1) * (numSlowSteps + 1);
      const delay = parseFloat(formData.delay) || 0;
      const readTime = 0.15; // ~150ms per instrument read
      const stepMoveTime = motionTime(fastStepSzActual, fastVel, fastAcc);
      totalSeconds = totalPoints * (stepMoveTime + delay + readTime) + numSlowSteps * slowStepTime; // slow axis stepping between rows
    }

    if (!isFinite(totalSeconds) || totalSeconds <= 0) return null;

    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = Math.round(totalSeconds % 60);

    if (hours > 0) return `~${hours}h ${minutes}m ${seconds}s`;
    if (minutes > 0) return `~${minutes}m ${seconds}s`;
    return `~${seconds}s`;
  }, [formData, settings, isFormValid]);

  return (
    <div className="flex-1 rounded-lg bg-gray-800 p-4 shadow-lg">
      <div className="mb-4 flex">
        <button
          className={`flex-1 py-2 ${
            activeTab === 'stage' ? 'bg-teal-600' : 'bg-gray-700'
          } rounded-l text-white`}
          onClick={() => setActiveTab('stage')}
        >
          Stage
        </button>
        <button
          className={`flex-1 py-2 ${
            activeTab === 'lockin' ? 'bg-teal-600' : 'bg-gray-700'
          } text-white`}
          onClick={() => {
            setActiveTab('lockin');
            fetchLockinSettings();
          }}
        >
          Lock-in
        </button>
        <button
          className={`flex-1 py-2 ${
            activeTab === 'multimeter' ? 'bg-teal-600' : 'bg-gray-700'
          } rounded-r text-white`}
          onClick={() => {
            setActiveTab('multimeter');
            fetchMultimeterSettings();
          }}
        >
          Multimeter
        </button>
      </div>

      {activeTab === 'stage' && (
        <div className="space-y-3">
          {/* Move to Position */}
          <div className="grid grid-cols-4 gap-2">
            <input
              type="number"
              placeholder="x (0-110) (mm)"
              className={`rounded border bg-gray-700 p-2 text-sm text-white ${
                moveX !== '' && (Number(moveX) < 0 || Number(moveX) > 110)
                  ? 'border-red-500'
                  : 'border-gray-600 focus:border-teal-500'
              } focus:outline-none`}
              value={moveX}
              onChange={(e) => setMoveX(e.target.value)}
            />
            <input
              type="number"
              placeholder="y (0-75) (mm)"
              className={`rounded border bg-gray-700 p-2 text-sm text-white ${
                moveY !== '' && (Number(moveY) < 0 || Number(moveY) > 75)
                  ? 'border-red-500'
                  : 'border-gray-600 focus:border-teal-500'
              } focus:outline-none`}
              value={moveY}
              onChange={(e) => setMoveY(e.target.value)}
            />
            <button
              onClick={handleMoveTo}
              disabled={!isMoveValid || isMoving || isProcessing}
              className={`col-span-2 rounded py-2 text-sm text-white transition-colors ${
                isMoveValid && !isMoving && !isProcessing
                  ? 'bg-teal-600 hover:bg-teal-700'
                  : 'cursor-not-allowed bg-gray-600'
              }`}
            >
              {isMoving ? 'Moving...' : 'Move To'}
            </button>
          </div>

          {/* Motion Type Toggle */}
          <div className="flex justify-center space-x-4">
            <label className="flex items-center text-white">
              <input
                type="radio"
                name="motionType"
                value="step_and_measure"
                checked={formData.motionType === 'step_and_measure'}
                onChange={() => setFormData({ ...formData, motionType: 'step_and_measure' })}
                className="mr-2 text-teal-600 focus:ring-teal-500"
              />
              Step & Measure
            </label>
            <label className="flex items-center text-white">
              <input
                type="radio"
                name="motionType"
                value="continuous"
                checked={formData.motionType === 'continuous'}
                onChange={() => setFormData({ ...formData, motionType: 'continuous' })}
                className="mr-2 text-teal-600 focus:ring-teal-500"
              />
              Continuous
            </label>
          </div>

          {/* Movement Mode (steps vs stepSize) */}
          {
            <div className="flex justify-center space-x-6">
              <label className="flex items-center text-sm text-gray-300">
                <input
                  type="radio"
                  name="movementMode"
                  value="steps"
                  checked={formData.movementMode === 'steps'}
                  onChange={() =>
                    setFormData({
                      ...formData,
                      xStepSize: '',
                      yStepSize: '',
                      movementMode: 'steps',
                    })
                  }
                  className="mr-1.5 text-teal-600 focus:ring-teal-500"
                />
                Steps
              </label>
              <label className="flex items-center text-sm text-gray-300">
                <input
                  type="radio"
                  name="movementMode"
                  value="stepSize"
                  checked={formData.movementMode === 'stepSize'}
                  onChange={() =>
                    setFormData({
                      ...formData,
                      xSteps: '',
                      ySteps: '',
                      movementMode: 'stepSize',
                    })
                  }
                  className="mr-1.5 text-teal-600 focus:ring-teal-500"
                />
                Step Size
              </label>
            </div>
          }

          {/* Coordinate Inputs */}
          <div className="grid grid-cols-2 gap-2">
            {['x1', 'y1', 'x2', 'y2'].map((key) => {
              const isX = key === 'x1' || key === 'x2';
              const max = isX ? 110 : 75;
              const val = formData[key as keyof FormData] as string;
              const invalid = val === '' || Number(val) < 0 || Number(val) > max;
              return (
                <div key={key} className="flex items-stretch gap-1">
                  <input
                    type="number"
                    placeholder={`${key} (0-${max}) (mm)`}
                    className={`min-w-0 flex-1 rounded border bg-gray-700 p-2 text-white ${
                      invalid ? 'border-red-500' : 'border-gray-600 focus:border-teal-500'
                    } focus:outline-none`}
                    value={val}
                    onChange={(e) => {
                      const v = e.target.value;
                      if (v === '' || (Number(v) >= 0 && Number(v) <= max)) {
                        setFormData({ ...formData, [key]: v });
                      }
                    }}
                  />
                  <button
                    type="button"
                    title="Use current stage position"
                    disabled={isProcessing}
                    onClick={() => fetchCurrentPosition(key as 'x1' | 'y1' | 'x2' | 'y2')}
                    className="flex-shrink-0 rounded border border-gray-600 bg-gray-700 px-2 text-teal-400 hover:bg-gray-600 hover:text-teal-300 disabled:opacity-50"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <circle cx="12" cy="12" r="10" />
                      <circle cx="12" cy="12" r="2" />
                      <line x1="12" y1="2" x2="12" y2="6" />
                      <line x1="12" y1="18" x2="12" y2="22" />
                      <line x1="2" y1="12" x2="6" y2="12" />
                      <line x1="18" y1="12" x2="22" y2="12" />
                    </svg>
                  </button>
                </div>
              );
            })}
          </div>

          {/* Step Inputs — conditional on motion type and movement mode */}
          {formData.motionType === 'continuous' ? (
            formData.movementMode === 'steps' ? (
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  placeholder={`x steps ${formData.fastAxis === 'x' ? '(fast)' : '(slow)'} (int >0)`}
                  className={`rounded border bg-gray-700 p-2 text-white ${
                    formData.xSteps === '' ||
                    Number(formData.xSteps) <= 0 ||
                    !Number.isInteger(Number(formData.xSteps))
                      ? 'border-red-500'
                      : 'border-gray-600 focus:border-teal-500'
                  } focus:outline-none`}
                  value={formData.xSteps}
                  onChange={(e) => {
                    const value = e.target.value;
                    if (value === '' || (Number.isInteger(Number(value)) && Number(value) > 0)) {
                      setFormData({ ...formData, xSteps: value });
                    }
                  }}
                />
                <input
                  type="number"
                  placeholder={`y steps ${formData.fastAxis === 'y' ? '(fast)' : '(slow)'} (int >0)`}
                  className={`rounded border bg-gray-700 p-2 text-white ${
                    formData.ySteps === '' ||
                    Number(formData.ySteps) <= 0 ||
                    !Number.isInteger(Number(formData.ySteps))
                      ? 'border-red-500'
                      : 'border-gray-600 focus:border-teal-500'
                  } focus:outline-none`}
                  value={formData.ySteps}
                  onChange={(e) => {
                    const value = e.target.value;
                    if (value === '' || (Number.isInteger(Number(value)) && Number(value) > 0)) {
                      setFormData({ ...formData, ySteps: value });
                    }
                  }}
                />
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  placeholder={`x step size ${formData.fastAxis === 'x' ? '(fast)' : '(slow)'} (mm)`}
                  className={`rounded border bg-gray-700 p-2 text-white ${
                    formData.xStepSize === '' || Number(formData.xStepSize) <= 0
                      ? 'border-red-500'
                      : 'border-gray-600 focus:border-teal-500'
                  } focus:outline-none`}
                  value={formData.xStepSize}
                  onChange={(e) => setFormData({ ...formData, xStepSize: e.target.value })}
                />
                <input
                  type="number"
                  placeholder={`y step size ${formData.fastAxis === 'y' ? '(fast)' : '(slow)'} (mm)`}
                  className={`rounded border bg-gray-700 p-2 text-white ${
                    formData.yStepSize === '' || Number(formData.yStepSize) <= 0
                      ? 'border-red-500'
                      : 'border-gray-600 focus:border-teal-500'
                  } focus:outline-none`}
                  value={formData.yStepSize}
                  onChange={(e) => setFormData({ ...formData, yStepSize: e.target.value })}
                />
              </div>
            )
          ) : formData.movementMode === 'steps' ? (
            <div className="grid grid-cols-2 gap-2">
              <input
                type="number"
                placeholder={`x steps ${formData.fastAxis === 'x' ? '(fast)' : '(slow)'} (int >0)`}
                className={`rounded border bg-gray-700 p-2 text-white ${
                  formData.xSteps === '' ||
                  Number(formData.xSteps) <= 0 ||
                  !Number.isInteger(Number(formData.xSteps))
                    ? 'border-red-500'
                    : 'border-gray-600 focus:border-teal-500'
                } focus:outline-none`}
                value={formData.xSteps}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === '' || (Number.isInteger(Number(value)) && Number(value) > 0)) {
                    setFormData({ ...formData, xSteps: value });
                  }
                }}
              />
              <input
                type="number"
                placeholder={`y steps ${formData.fastAxis === 'y' ? '(fast)' : '(slow)'} (int >0)`}
                className={`rounded border bg-gray-700 p-2 text-white ${
                  formData.ySteps === '' ||
                  Number(formData.ySteps) <= 0 ||
                  !Number.isInteger(Number(formData.ySteps))
                    ? 'border-red-500'
                    : 'border-gray-600 focus:border-teal-500'
                } focus:outline-none`}
                value={formData.ySteps}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === '' || (Number.isInteger(Number(value)) && Number(value) > 0)) {
                    setFormData({ ...formData, ySteps: value });
                  }
                }}
              />
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-2">
              <input
                type="number"
                placeholder={`x step size ${formData.fastAxis === 'x' ? '(fast)' : '(slow)'} (mm)`}
                className={`rounded border bg-gray-700 p-2 text-white ${
                  formData.xStepSize === '' || Number(formData.xStepSize) <= 0
                    ? 'border-red-500'
                    : 'border-gray-600 focus:border-teal-500'
                } focus:outline-none`}
                value={formData.xStepSize}
                onChange={(e) => setFormData({ ...formData, xStepSize: e.target.value })}
              />
              <input
                type="number"
                placeholder={`y step size ${formData.fastAxis === 'y' ? '(fast)' : '(slow)'} (mm)`}
                className={`rounded border bg-gray-700 p-2 text-white ${
                  formData.yStepSize === '' || Number(formData.yStepSize) <= 0
                    ? 'border-red-500'
                    : 'border-gray-600 focus:border-teal-500'
                } focus:outline-none`}
                value={formData.yStepSize}
                onChange={(e) => setFormData({ ...formData, yStepSize: e.target.value })}
              />
            </div>
          )}

          {/* Fast Axis + Scan Pattern + Delay Row */}
          <div className="grid grid-cols-2 gap-2">
            {/* Fast Axis Dropdown */}
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-300">Fast axis:</label>
              <select
                value={formData.fastAxis}
                onChange={(e) => setFormData({ ...formData, fastAxis: e.target.value })}
                className="rounded border border-gray-600 bg-gray-700 p-1.5 text-sm text-white focus:border-teal-500 focus:outline-none"
              >
                <option value="x">X</option>
                <option value="y">Y</option>
              </select>
            </div>
            {/* Delay — visible only for step & measure, but always rendered to prevent layout shift */}
            <input
              placeholder="delay (>=0) (s)"
              className={`rounded border bg-gray-700 p-2 text-white ${
                formData.motionType !== 'step_and_measure'
                  ? 'invisible'
                  : formData.delay !== '' &&
                      (Number(formData.delay) < 0 || isNaN(Number(formData.delay)))
                    ? 'border-red-500'
                    : 'border-gray-600 focus:border-teal-500'
              } focus:outline-none`}
              value={formData.delay}
              disabled={formData.motionType !== 'step_and_measure'}
              onChange={(e) => {
                const value = e.target.value;
                if (value === '' || (Number(value) >= 0 && !isNaN(Number(value)))) {
                  setFormData({ ...formData, delay: value });
                }
              }}
            />
          </div>

          {/* Scan Pattern */}
          <div className="flex items-center justify-center space-x-4">
            <label className="flex items-center text-sm text-gray-300">
              <input
                type="radio"
                name="scanPattern"
                value="bidirectional"
                checked={formData.scanPattern === 'bidirectional'}
                onChange={() =>
                  setFormData({ ...formData, scanPattern: 'bidirectional', recordRetrace: false })
                }
                className="mr-1.5 text-teal-600 focus:ring-teal-500"
              />
              Bidirectional
            </label>
            <label className="flex items-center text-sm text-gray-300">
              <input
                type="radio"
                name="scanPattern"
                value="unidirectional"
                checked={formData.scanPattern === 'unidirectional'}
                onChange={() => setFormData({ ...formData, scanPattern: 'unidirectional' })}
                className="mr-1.5 text-teal-600 focus:ring-teal-500"
              />
              Unidirectional
            </label>
            {formData.scanPattern === 'unidirectional' && (
              <label className="flex items-center text-sm text-gray-300">
                <input
                  type="checkbox"
                  checked={formData.recordRetrace}
                  onChange={(e) => setFormData({ ...formData, recordRetrace: e.target.checked })}
                  className="mr-1.5 rounded text-teal-600 focus:ring-teal-500"
                />
                Record retrace
              </label>
            )}
          </div>

          {/* Estimated Time */}
          {estimatedTime && (
            <div className="mb-2 text-center text-sm text-gray-300">
              Estimated scan time:{' '}
              <span className="font-semibold text-teal-400">{estimatedTime}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex space-x-2">
            <button
              onClick={handleSubmit}
              disabled={!isFormValid || isProcessing}
              className={`flex-1 rounded py-2 text-white transition-colors ${
                isFormValid ? 'bg-teal-600 hover:bg-teal-700' : 'cursor-not-allowed bg-gray-600'
              }`}
            >
              Start
            </button>
            <button
              onClick={() => handleHome('')}
              className="flex-1 rounded bg-teal-600 py-2 text-white transition-colors hover:bg-teal-700"
            >
              Home XY
            </button>
            <button
              onClick={handleReset}
              className="flex-1 rounded bg-red-600 py-2 text-white transition-colors hover:bg-red-700"
            >
              Clear Values
            </button>
            <button
              onClick={handleStop}
              disabled={!isProcessing}
              className={`flex-1 rounded py-2 text-white transition-colors ${
                isProcessing ? 'bg-red-700 hover:bg-red-800' : 'cursor-not-allowed bg-gray-600'
              }`}
            >
              Stop
            </button>
          </div>
          {status && <div className="mt-2 text-center text-white">{status}</div>}
        </div>
      )}
      {activeTab === 'lockin' && (
        <div className="space-y-4">
          {/* Sensitivity Control */}
          <div className="flex items-center space-x-2">
            <label className="w-24 text-white">Sensitivity</label>
            <button
              onClick={() => changeLockinSensitivity(true)}
              disabled={lockinSettings.sensitivity === 27}
              className="rounded bg-gray-700 p-2 text-white hover:bg-gray-600 disabled:opacity-50"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                  0: '1 V',
                  1: '500 mV',
                  2: '200 mV',
                  3: '100 mV',
                  4: '50 mV',
                  5: '20 mV',
                  6: '10 mV',
                  7: '5 mV',
                  8: '2 mV',
                  9: '1 mV',
                  10: '500 µV',
                  11: '200 µV',
                  12: '100 µV',
                  13: '50 µV',
                  14: '20 µV',
                  15: '10 µV',
                  16: '5 µV',
                  17: '2 µV',
                  18: '1 µV',
                  19: '500 nV',
                  20: '200 nV',
                  21: '100 nV',
                  22: '50 nV',
                  23: '20 nV',
                  24: '10 nV',
                  25: '5 nV',
                  26: '2 nV',
                  27: '1 nV',
                }[lockinSettings.sensitivity] || 'Unknown'
              }
              readOnly
              className="w-24 rounded border border-gray-600 bg-gray-700 p-2 text-center text-white"
            />
            <button
              onClick={() => changeLockinSensitivity(false)}
              disabled={lockinSettings.sensitivity === 0}
              className="rounded bg-gray-700 p-2 text-white hover:bg-gray-600 disabled:opacity-50"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
            <label className="w-24 text-white">Time Constant</label>
            <button
              onClick={() => changeLockinTimeConstant(false)}
              disabled={lockinSettings.timeConstant === 0}
              className="rounded bg-gray-700 p-2 text-white hover:bg-gray-600 disabled:opacity-50"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                  0: '1 µs',
                  1: '3 µs',
                  2: '10 µs',
                  3: '30 µs',
                  4: '100 µs',
                  5: '300 µs',
                  6: '1 ms',
                  7: '3 ms',
                  8: '10 ms',
                  9: '30 ms',
                  10: '100 ms',
                  11: '300 ms',
                  12: '1 s',
                  13: '3 s',
                  14: '10 s',
                  15: '30 s',
                  16: '100 s',
                  17: '300 s',
                  18: '1 ks',
                  19: '3 ks',
                  20: '10 ks',
                  21: '30 ks',
                  22: '100 ks',
                  23: '300 ks',
                }[lockinSettings.timeConstant] || 'Unknown'
              }
              readOnly
              className="w-24 rounded border border-gray-600 bg-gray-700 p-2 text-center text-white"
            />
            <button
              onClick={() => changeLockinTimeConstant(true)}
              disabled={lockinSettings.timeConstant === 23} // Adjust to 30 if extending time constant map
              className="rounded bg-gray-700 p-2 text-white hover:bg-gray-600 disabled:opacity-50"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 14l-7-7-7 7"
                />
              </svg>
            </button>
          </div>

          {/* Frequency Control */}
          <div className="flex items-center space-x-2">
            <label className="w-24 text-white">Frequency</label>
            <input
              type="number"
              placeholder={lockinSettings.frequency.toString()}
              className="w-28 rounded border border-gray-600 bg-gray-700 p-2 text-center text-sm text-white focus:border-teal-500 focus:outline-none"
              value={freqInput}
              onChange={(e) => setFreqInput(e.target.value)}
            />
            <span className="text-sm text-gray-400">Hz</span>
            <button
              onClick={() => {
                const freq = parseFloat(freqInput);
                if (!isNaN(freq) && freq > 0) {
                  changeLockinFrequency(freq);
                  setFreqInput('');
                }
              }}
              disabled={freqInput === '' || isNaN(Number(freqInput)) || Number(freqInput) <= 0}
              className="rounded bg-teal-600 px-3 py-2 text-sm text-white hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Set
            </button>
          </div>

          {/* Filter Slope Control */}
          <div className="flex items-center space-x-2">
            <label className="w-24 text-white">Filter Slope</label>
            <div className="flex space-x-2">
              {[
                { code: 0, label: '6 dB/oct' },
                { code: 1, label: '12 dB/oct' },
                { code: 2, label: '18 dB/oct' },
                { code: 3, label: '24 dB/oct' },
              ].map((opt) => (
                <button
                  key={opt.code}
                  onClick={() => changeLockinFilterSlope(opt.code)}
                  className={`rounded px-2 py-1.5 text-xs text-white transition-colors ${
                    lockinSettings.filterSlope === opt.code
                      ? 'bg-teal-600'
                      : 'bg-gray-700 hover:bg-gray-600'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
      {activeTab === 'multimeter' && (
        <div className="space-y-4">
          {/* Aperture Control */}
          <div className="flex items-center space-x-2">
            <label className="w-24 text-white">Aperture (NPLC)</label>
            <button
              onClick={() => {
                const validNPLC = [0.02, 0.2, 1, 10, 100];
                const currentIndex = validNPLC.indexOf(multimeterSettings.aperture);
                if (currentIndex > 0) {
                  changeMultimeterAperture(validNPLC[currentIndex - 1]);
                }
              }}
              disabled={multimeterSettings.aperture === 0.02}
              className="rounded bg-gray-700 p-2 text-white hover:bg-gray-600 disabled:opacity-50"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
              className="w-24 rounded border border-gray-600 bg-gray-700 p-2 text-center text-white"
            />
            <button
              onClick={() => {
                const validNPLC = [0.02, 0.2, 1, 10, 100];
                const currentIndex = validNPLC.indexOf(multimeterSettings.aperture);
                if (currentIndex < validNPLC.length - 1) {
                  changeMultimeterAperture(validNPLC[currentIndex + 1]);
                }
              }}
              disabled={multimeterSettings.aperture === 100}
              className="rounded bg-gray-700 p-2 text-white hover:bg-gray-600 disabled:opacity-50"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
            <label className="w-24 text-white">Terminal</label>
            <div className="flex space-x-4">
              <label className="flex items-center text-white">
                <input
                  type="radio"
                  name="terminal"
                  value="front"
                  checked={multimeterSettings.terminal === 'fron'}
                  onChange={() => changeMultimeterTerminal('fron')}
                  className="mr-2 text-teal-600 focus:ring-teal-500"
                />
                Front
              </label>
              <label className="flex items-center text-white">
                <input
                  type="radio"
                  name="terminal"
                  value="rear"
                  checked={multimeterSettings.terminal === 'rear'}
                  onChange={() => changeMultimeterTerminal('rear')}
                  className="mr-2 text-teal-600 focus:ring-teal-500"
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
