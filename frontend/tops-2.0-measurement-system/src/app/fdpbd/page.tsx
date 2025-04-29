"use client";

import { useState } from "react";
import Plot from "react-plotly.js";

type FDPBDParams = {
  f_amp: string;
  delay_1: string;
  delay_2: string;
  lambda_down: string[];
  eta_down: string;
  c_down: string[];
  h_down: string[];
  niu: string;
  alpha_t: string;
  lambda_up: string;
  eta_up: string;
  c_up: string;
  h_up: string;
  r_rms: string;
  x_offset: string;
  incident_pump: string;
  incident_probe: string;
  n_al: string;
  k_al: string;
  lens_transmittance: string;
  detector_gain: string;
  phi: string;
};

type PlotData = {
  freq_fit: number[];
  v_corr_in_fit: number[];
  v_corr_out_fit: number[];
  v_corr_ratio_fit: number[];
  delta_in: number[];
  delta_out: number[];
  delta_ratio: number[];
};

type FDPBDResult = {
  lambda_measure: number;
  alpha_t_fitted: number;
  t_ss_heat: number;
  plot_data: PlotData;
};

export default function FDPBDPage() {
  const [params, setParams] = useState<FDPBDParams>({
    f_amp: "95000",
    delay_1: "0.0000089",
    delay_2: "-1.3e-11",
    lambda_down: ["149.0", "0.1", "9.7"],
    eta_down: "1.0,1.0,1.0",
    c_down: ["2440000", "100000", "2730000"],
    h_down: ["7e-8", "1e-9", "1e-6"],
    niu: "0.26",
    alpha_t: "0.00001885",
    lambda_up: "0.028",
    eta_up: "1.0",
    c_up: "1192.0",
    h_up: "0.001",
    r_rms: "0.00001120",
    x_offset: "0.0000126",
    incident_pump: "0.00106",
    incident_probe: "0.00085",
    n_al: "2.9",
    k_al: "8.2",
    lens_transmittance: "0.93",
    detector_gain: "74.0",
    phi: "0",
  });
  const fieldUnits: Record<string, string> = {
    f_amp: "Hz",
    delay_1: "s",
    delay_2: "s",
    lambda_down: "W/m-K",
    eta_down: "",
    c_down: "J/m³-K",
    h_down: "m",
    niu: "",
    alpha_t: "1/K",
    lambda_up: "W/m-K",
    eta_up: "",
    c_up: "J/m³-K",
    h_up: "m",
    r_rms: "m",
    x_offset: "m",
    incident_pump: "W",
    incident_probe: "W",
    n_al: "",
    k_al: "",
    lens_transmittance: "",
    detector_gain: "V/rad",
    phi: "degrees",
  };
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<FDPBDResult | null>(null);
  const [status, setStatus] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [lensOption, setLensOption] = useState<"5x" | "10x" | "20x" | "custom">(
    "5x"
  );
  const [transducerOption, setTransducerOption] = useState<"Al" | "custom">(
    "Al"
  );
  const [mediumOption, setMediumOption] = useState<"air" | "custom">("air");
  const [isotropyOption, setIsotropyOption] = useState<
    "isotropy" | "anisotropy"
  >("isotropy");
  const [laserOption, setLaserOption] = useState<
    "TOPS 1" | "TOPS 2" | "custom"
  >("TOPS 1");

  const isValidDecimal = (value: string | string[]) => {
    if (Array.isArray(value)) {
      return value.every((v) => v !== "" && !isNaN(parseFloat(v)));
    }
    if (value.includes(",")) {
      // For eta_down (comma-separated)
      return value
        .split(",")
        .every((v) => v.trim() !== "" && !isNaN(parseFloat(v.trim())));
    }
    return value !== "" && !isNaN(parseFloat(value));
  };

  const isFormValid = () => {
    const fields = [
      params.f_amp,
      params.delay_1,
      params.delay_2,
      params.lambda_down[0],
      params.lambda_down[1],
      params.lambda_down[2],
      params.eta_down,
      params.c_down[0],
      params.c_down[1],
      params.c_down[2],
      params.h_down[0],
      params.h_down[1],
      params.h_down[2],
      params.niu,
      params.alpha_t,
      params.lambda_up,
      ...(isotropyOption === "isotropy" ? [params.eta_up, params.h_up] : []),
      params.c_up,
      params.r_rms,
      params.x_offset,
      params.incident_pump,
      params.incident_probe,
      params.n_al,
      params.k_al,
      params.lens_transmittance,
      params.detector_gain,
      ...(isotropyOption === "anisotropy" ? [params.phi] : []),
    ];
    return fields.every((field) => isValidDecimal(field)) && file !== null;
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    field: keyof FDPBDParams,
    index?: number
  ) => {
    const value = e.target.value;
    setParams((prev) => {
      if (
        index !== undefined &&
        ["lambda_down", "c_down", "h_down"].includes(field)
      ) {
        const updatedArray = [...prev[field]];
        updatedArray[index] = value;
        return { ...prev, [field]: updatedArray };
      }
      return { ...prev, [field]: value };
    });

    if (
      [
        "r_rms",
        "x_offset",
        "lens_transmittance",
        "detector_gain",
        "phi",
      ].includes(field)
    ) {
      const lensValues = {
        "5x": {
          r_rms: "0.00001120",
          x_offset: "0.0000126",
          lens_transmittance: "0.93",
          detector_gain: "74.0",
          phi: "0",
        },
        "10x": {
          r_rms: "0.0000056",
          x_offset: "0.0000063",
          lens_transmittance: "0.85",
          detector_gain: "37.0",
          phi: "0",
        },
        "20x": {
          r_rms: "0.0000028",
          x_offset: "0.00000315",
          lens_transmittance: "0.80",
          detector_gain: "18.5",
          phi: "0",
        },
      };
      const updatedParams = { ...params, [field]: value };
      if (
        !Object.values(lensValues).some(
          (vals) =>
            vals.r_rms === updatedParams.r_rms &&
            vals.x_offset === updatedParams.x_offset &&
            vals.lens_transmittance === updatedParams.lens_transmittance &&
            vals.detector_gain === updatedParams.detector_gain &&
            vals.phi === updatedParams.phi
        )
      ) {
        setLensOption("custom");
      }
    }
    if (
      (["lambda_down", "c_down", "h_down"].includes(field) && index === 0) ||
      ["n_al", "k_al"].includes(field)
    ) {
      const alValues = {
        lambda_down_0: "149.0",
        c_down_0: "2440000",
        h_down_0: "7e-8",
        n_al: "2.9",
        k_al: "8.2",
      };
      const updatedParams =
        index !== undefined
          ? {
              ...params,
              [field]: [
                ...params[field].slice(0, index),
                value,
                ...params[field].slice(index + 1),
              ],
            }
          : { ...params, [field]: value };
      if (
        updatedParams.lambda_down[0] !== alValues.lambda_down_0 ||
        updatedParams.c_down[0] !== alValues.c_down_0 ||
        updatedParams.h_down[0] !== alValues.h_down_0 ||
        updatedParams.n_al !== alValues.n_al ||
        updatedParams.k_al !== alValues.k_al
      ) {
        setTransducerOption("custom");
      }
    }
    if (["lambda_up", "eta_up", "c_up", "h_up"].includes(field)) {
      const airValues = {
        lambda_up: "0.028",
        eta_up: "1.0",
        c_up: "1192.0",
        h_up: "0.001",
      };
      const updatedParams = { ...params, [field]: value };
      if (
        !(
          updatedParams.lambda_up === airValues.lambda_up &&
          (isotropyOption === "anisotropy" ||
            updatedParams.eta_up === airValues.eta_up) &&
          updatedParams.c_up === airValues.c_up &&
          (isotropyOption === "anisotropy" ||
            updatedParams.h_up === airValues.h_up)
        )
      ) {
        setMediumOption("custom");
      }
    }
    if (field === "eta_down") {
      const isotropyValue = "1.0,1.0,1.0";
      if (value !== isotropyValue) {
        setIsotropyOption("anisotropy");
      }
    }
    if (
      [
        "f_amp",
        "delay_1",
        "delay_2",
        "incident_pump",
        "incident_probe",
      ].includes(field)
    ) {
      const laserValues = {
        "TOPS 1": {
          f_amp: "95000",
          delay_1: "0.0000089",
          delay_2: "-1.3e-11",
          incident_pump: "0.00106",
          incident_probe: "0.00085",
        },
        "TOPS 2": {
          f_amp: "95000",
          delay_1: "0.0000089",
          delay_2: "-1.3e-11",
          incident_pump: "0.00106",
          incident_probe: "0.00085",
        },
      };
      const updatedParams = { ...params, [field]: value };
      if (
        !Object.values(laserValues).some(
          (vals) =>
            vals.f_amp === updatedParams.f_amp &&
            vals.delay_1 === updatedParams.delay_1 &&
            vals.delay_2 === updatedParams.delay_2 &&
            vals.incident_pump === updatedParams.incident_pump &&
            vals.incident_probe === updatedParams.incident_probe
        )
      ) {
        setLaserOption("custom");
      }
    }
  };

  const handleLensOptionChange = (option: "5x" | "10x" | "20x" | "custom") => {
    setLensOption(option);
    if (option !== "custom") {
      const values = {
        "5x": {
          r_rms: "0.00001120",
          x_offset: "0.0000126",
          lens_transmittance: "0.93",
          detector_gain: "74.0",
          phi: "0",
        },
        "10x": {
          r_rms: "0.0000056",
          x_offset: "0.0000063",
          lens_transmittance: "0.85",
          detector_gain: "37.0",
          phi: "0",
        },
        "20x": {
          r_rms: "0.0000028",
          x_offset: "0.00000315",
          lens_transmittance: "0.80",
          detector_gain: "18.5",
          phi: "0",
        },
      };
      setParams((prev) => ({
        ...prev,
        r_rms: values[option].r_rms,
        x_offset: values[option].x_offset,
        lens_transmittance: values[option].lens_transmittance,
        detector_gain: values[option].detector_gain,
        phi: values[option].phi,
      }));
    }
  };

  const handleTransducerOptionChange = (option: "Al" | "custom") => {
    setTransducerOption(option);
    if (option === "Al") {
      setParams((prev) => ({
        ...prev,
        lambda_down: ["149.0", prev.lambda_down[1], prev.lambda_down[2]],
        c_down: ["2440000", prev.c_down[1], prev.c_down[2]],
        h_down: ["7e-8", prev.h_down[1], prev.h_down[2]],
        n_al: "2.9",
        k_al: "8.2",
      }));
    }
  };

  const handleMediumOptionChange = (option: "air" | "custom") => {
    setMediumOption(option);
    if (option === "air") {
      setParams((prev) => ({
        ...prev,
        lambda_up: "0.028",
        eta_up: isotropyOption === "isotropy" ? "1.0" : prev.eta_up,
        c_up: "1192.0",
        h_up: isotropyOption === "isotropy" ? "0.001" : prev.h_up,
      }));
    }
  };

  const handleIsotropyOptionChange = (option: "isotropy" | "anisotropy") => {
    setIsotropyOption(option);
    if (option === "isotropy") {
      setParams((prev) => ({
        ...prev,
        eta_down: "1.0,1.0,1.0",
      }));
    }
  };

  const handleLaserOptionChange = (option: "TOPS 1" | "TOPS 2" | "custom") => {
    setLaserOption(option);
    if (option !== "custom") {
      const values = {
        "TOPS 1": {
          f_amp: "95000",
          delay_1: "0.0000089",
          delay_2: "-1.3e-11",
          incident_pump: "0.00106",
          incident_probe: "0.00085",
        },
        "TOPS 2": {
          f_amp: "95000",
          delay_1: "0.0000089",
          delay_2: "-1.3e-11",
          incident_pump: "0.00106",
          incident_probe: "0.00085",
        },
      };
      setParams((prev) => ({
        ...prev,
        f_amp: values[option].f_amp,
        delay_1: values[option].delay_1,
        delay_2: values[option].delay_2,
        incident_pump: values[option].incident_pump,
        incident_probe: values[option].incident_probe,
      }));
    }
  };

  const handleClear = () => {
    setParams({
      f_amp: "",
      delay_1: "",
      delay_2: "",
      lambda_down: ["", "", ""],
      eta_down: "",
      c_down: ["", "", ""],
      h_down: ["", "", ""],
      niu: "",
      alpha_t: "",
      lambda_up: "",
      eta_up: "",
      c_up: "",
      h_up: "",
      r_rms: "",
      x_offset: "",
      incident_pump: "",
      incident_probe: "",
      n_al: "",
      k_al: "",
      lens_transmittance: "",
      detector_gain: "",
      phi: "",
    });
    setFile(null);
    setLensOption("custom");
    setTransducerOption("custom");
    setMediumOption("custom");
    setIsotropyOption("anisotropy");
    setLaserOption("custom");
    setStatus("");
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.type === "text/plain") {
      setFile(selectedFile);
      setStatus("");
    } else {
      setFile(null);
      setStatus("Please upload a .txt file");
    }
  };

  const handleSubmit = async () => {
    if (!file) {
      setStatus("Please upload a data file");
      return;
    }
    setIsProcessing(true);
    setStatus("Processing...");

    const formData = new FormData();
    formData.append("file", file);
    const visibleParams = {
      ...params,
      ...(isotropyOption === "anisotropy"
        ? { eta_up: undefined, h_up: undefined }
        : { phi: undefined }),
    };
    formData.append("params", JSON.stringify(visibleParams));

    try {
      const endpoint =
        isotropyOption === "isotropy"
          ? "http://localhost:8000/fdpbd/analyze"
          : "http://localhost:8000/fdpbd/analyze_anisotropy";
      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        setResult(data);
        setStatus("Analysis completed");
      } else {
        setStatus(`Error: ${data.detail || "Unknown error"}`);
      }
    } catch (error) {
      console.error("Error:", error);
      setStatus("Error occurred during analysis");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      {/* Header */}
      <header className="bg-gray-800 p-4 flex justify-between items-center">
        <h1 className="text-white text-xl font-semibold">Analysis</h1>
        <a href="/" className="text-white hover:text-teal-400">
          Back to Dashboard
        </a>
      </header>

      {/* Main Layout */}
      <div className="flex flex-1 p-4 space-x-4">
        {/* Left Panel: Input Form */}
        <div className="w-1/3 flex flex-col space-y-4">
          <div className="bg-gray-800 p-4 rounded-lg shadow-md">
            <h2 className="text-white text-lg font-semibold mb-4">
              Parameters
            </h2>
            {/* File Upload */}
            <div className="mb-6">
              <h3 className="text-white text-md font-semibold mb-2">
                Data File (.txt)
              </h3>
              <input
                type="file"
                accept=".txt"
                onChange={handleFileChange}
                className="bg-gray-700 text-white p-2 rounded w-full"
                disabled={isProcessing}
              />
            </div>

            {/* Experimental Inputs */}
            <div className="mb-6">
              <h3 className="text-white text-md font-semibold mb-2">
                Experimental Inputs
              </h3>
              {/* Isotropy */}
              <div className="bg-gray-700 p-4 rounded-lg mb-4">
                <h4 className="text-white text-sm font-semibold mb-2">
                  Isotropy
                </h4>
                <div className="flex space-x-4 mb-2">
                  {["isotropy", "anisotropy"].map((opt) => (
                    <label key={opt} className="flex items-center text-white">
                      <input
                        type="radio"
                        name="isotropy"
                        value={opt}
                        checked={isotropyOption === opt}
                        onChange={() =>
                          handleIsotropyOptionChange(
                            opt as "isotropy" | "anisotropy"
                          )
                        }
                        className="mr-2"
                        disabled={isProcessing}
                      />
                      {opt}
                    </label>
                  ))}
                </div>
              </div>
              {/* Lens Magnification */}
              <div className="bg-gray-700 p-4 rounded-lg mb-4">
                <h4 className="text-white text-sm font-semibold mb-2">
                  Lens Magnification
                </h4>
                <div className="flex space-x-4 mb-2">
                  {["5x", "10x", "20x", "custom"].map((opt) => (
                    <label key={opt} className="flex items-center text-white">
                      <input
                        type="radio"
                        name="lens"
                        value={opt}
                        checked={lensOption === opt}
                        onChange={() =>
                          handleLensOptionChange(
                            opt as "5x" | "10x" | "20x" | "custom"
                          )
                        }
                        className="mr-2"
                        disabled={isProcessing}
                      />
                      {opt}
                    </label>
                  ))}
                </div>
                {[
                  { field: "r_rms", label: `R RMS [${fieldUnits.r_rms}]` },
                  {
                    field: "x_offset",
                    label: `X Offset [${fieldUnits.x_offset}]`,
                  },
                  {
                    field: "lens_transmittance",
                    label: `Lens Transmittance ${
                      fieldUnits.lens_transmittance
                        ? `[${fieldUnits.lens_transmittance}]`
                        : ""
                    }`,
                  },
                  {
                    field: "detector_gain",
                    label: `Detector Gain [${fieldUnits.detector_gain}]`,
                  },
                  ...(isotropyOption === "anisotropy"
                    ? [{ field: "phi", label: `Phi [${fieldUnits.phi}]` }]
                    : []),
                ].map((param) => (
                  <div key={param.field} className="flex flex-col mb-2">
                    <label className="text-white text-sm mb-1">
                      {param.label}
                    </label>
                    <input
                      type="number"
                      step="any"
                      value={params[param.field as keyof FDPBDParams]}
                      onChange={(e) =>
                        handleInputChange(e, param.field as keyof FDPBDParams)
                      }
                      className={`bg-gray-800 text-white p-2 rounded focus:outline-none border-2 ${
                        isValidDecimal(params[param.field as keyof FDPBDParams])
                          ? "border-gray-600 focus:border-teal-500"
                          : "border-red-500"
                      }`}
                      disabled={isProcessing}
                      required
                    />
                  </div>
                ))}
              </div>
              {/* Laser */}
              <div className="bg-gray-700 p-4 rounded-lg">
                <h4 className="text-white text-sm font-semibold mb-2">Laser</h4>
                <div className="flex space-x-4 mb-2">
                  {["TOPS 1", "TOPS 2", "custom"].map((opt) => (
                    <label key={opt} className="flex items-center text-white">
                      <input
                        type="radio"
                        name="laser"
                        value={opt}
                        checked={laserOption === opt}
                        onChange={() =>
                          handleLaserOptionChange(
                            opt as "TOPS 1" | "TOPS 2" | "custom"
                          )
                        }
                        className="mr-2"
                        disabled={isProcessing}
                      />
                      {opt}
                    </label>
                  ))}
                </div>
                {[
                  { field: "f_amp", label: `F Amp [${fieldUnits.f_amp}]` },
                  {
                    field: "delay_1",
                    label: `Delay 1 [${fieldUnits.delay_1}]`,
                  },
                  {
                    field: "delay_2",
                    label: `Delay 2 [${fieldUnits.delay_2}]`,
                  },
                  {
                    field: "incident_pump",
                    label: `Incident Pump [${fieldUnits.incident_pump}]`,
                  },
                  {
                    field: "incident_probe",
                    label: `Incident Probe [${fieldUnits.incident_probe}]`,
                  },
                ].map((param) => (
                  <div key={param.field} className="flex flex-col mb-2">
                    <label className="text-white text-sm mb-1">
                      {param.label}
                    </label>
                    <input
                      type="number"
                      step="any"
                      value={params[param.field as keyof FDPBDParams]}
                      onChange={(e) =>
                        handleInputChange(e, param.field as keyof FDPBDParams)
                      }
                      className={`bg-gray-800 text-white p-2 rounded focus:outline-none border-2 ${
                        isValidDecimal(params[param.field as keyof FDPBDParams])
                          ? "border-gray-600 focus:border-teal-500"
                          : "border-red-500"
                      }`}
                      disabled={isProcessing}
                      required
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Sample Inputs */}
            <div className="mb-6">
              <h3 className="text-white text-md font-semibold mb-2">
                Sample Inputs
              </h3>
              {/* Medium */}
              <div className="bg-gray-700 p-4 rounded-lg mb-4">
                <h4 className="text-white text-sm font-semibold mb-2">
                  Medium
                </h4>
                <div className="flex space-x-4 mb-2">
                  {["air", "custom"].map((opt) => (
                    <label key={opt} className="flex items-center text-white">
                      <input
                        type="radio"
                        name="medium"
                        value={opt}
                        checked={mediumOption === opt}
                        onChange={() =>
                          handleMediumOptionChange(opt as "air" | "custom")
                        }
                        className="mr-2"
                        disabled={isProcessing}
                      />
                      {opt}
                    </label>
                  ))}
                </div>
                {[
                  {
                    field: "lambda_up",
                    label: `Lambda Up [${fieldUnits.lambda_up}]`,
                  },
                  { field: "c_up", label: `C Up [${fieldUnits.c_up}]` },
                  ...(isotropyOption === "isotropy"
                    ? [
                        {
                          field: "eta_up",
                          label: `Eta Up ${
                            fieldUnits.eta_up ? `[${fieldUnits.eta_up}]` : ""
                          }`,
                        },
                        { field: "h_up", label: `H Up [${fieldUnits.h_up}]` },
                      ]
                    : []),
                ].map((param) => (
                  <div key={param.field} className="flex flex-col mb-2">
                    <label className="text-white text-sm mb-1">
                      {param.label}
                    </label>
                    <input
                      type="number"
                      step="any"
                      value={params[param.field as keyof FDPBDParams]}
                      onChange={(e) =>
                        handleInputChange(e, param.field as keyof FDPBDParams)
                      }
                      className={`bg-gray-800 text-white p-2 rounded focus:outline-none border-2 ${
                        isValidDecimal(params[param.field as keyof FDPBDParams])
                          ? "border-gray-600 focus:border-teal-500"
                          : "border-red-500"
                      }`}
                      disabled={isProcessing}
                      required
                    />
                  </div>
                ))}
              </div>
              {/* Transducer Layer */}
              <div className="bg-gray-700 p-4 rounded-lg mb-4">
                <h4 className="text-white text-sm font-semibold mb-2">
                  Transducer Layer
                </h4>
                <div className="flex space-x-4 mb-2">
                  {["Al", "custom"].map((opt) => (
                    <label key={opt} className="flex items-center text-white">
                      <input
                        type="radio"
                        name="transducer"
                        value={opt}
                        checked={transducerOption === opt}
                        onChange={() =>
                          handleTransducerOptionChange(opt as "Al" | "custom")
                        }
                        className="mr-2"
                        disabled={isProcessing}
                      />
                      {opt}
                    </label>
                  ))}
                </div>
                {[
                  {
                    field: "lambda_down",
                    index: 0,
                    label: `Lambda Down [${fieldUnits.lambda_down}]`,
                  },
                  {
                    field: "c_down",
                    index: 0,
                    label: `C Down [${fieldUnits.c_down}]`,
                  },
                  {
                    field: "h_down",
                    index: 0,
                    label: `H Down [${fieldUnits.h_down}]`,
                  },
                  {
                    field: "n_al",
                    label: `Refractive Index (N) ${
                      fieldUnits.n_al ? `[${fieldUnits.n_al}]` : ""
                    }`,
                  },
                  {
                    field: "k_al",
                    label: `Imaginary Index (K) ${
                      fieldUnits.k_al ? `[${fieldUnits.k_al}]` : ""
                    }`,
                  },
                ].map((param) => (
                  <div
                    key={`${param.field}${param.index ?? ""}`}
                    className="flex flex-col mb-2"
                  >
                    <label className="text-white text-sm mb-1">
                      {param.label}
                    </label>
                    <input
                      type="number"
                      step="any"
                      value={
                        param.index !== undefined
                          ? params[param.field as keyof FDPBDParams][
                              param.index
                            ]
                          : params[param.field as keyof FDPBDParams]
                      }
                      onChange={(e) =>
                        handleInputChange(
                          e,
                          param.field as keyof FDPBDParams,
                          param.index
                        )
                      }
                      className={`bg-gray-800 text-white p-2 rounded focus:outline-none border-2 ${
                        isValidDecimal(
                          param.index !== undefined
                            ? params[param.field as keyof FDPBDParams][
                                param.index
                              ]
                            : params[param.field as keyof FDPBDParams]
                        )
                          ? "border-gray-600 focus:border-teal-500"
                          : "border-red-500"
                      }`}
                      disabled={isProcessing}
                      required
                    />
                  </div>
                ))}
              </div>
              {/* Interface Layer */}
              <div className="bg-gray-700 p-4 rounded-lg mb-4">
                <h4 className="text-white text-sm font-semibold mb-2">
                  Interface Layer
                </h4>
                {[
                  {
                    field: "lambda_down",
                    index: 1,
                    label: `Lambda Down [${fieldUnits.lambda_down}]`,
                  },
                  {
                    field: "c_down",
                    index: 1,
                    label: `C Down [${fieldUnits.c_down}]`,
                  },
                  {
                    field: "h_down",
                    index: 1,
                    label: `H Down [${fieldUnits.h_down}]`,
                  },
                ].map((param) => (
                  <div
                    key={`${param.field}${param.index}`}
                    className="flex flex-col mb-2"
                  >
                    <label className="text-white text-sm mb-1">
                      {param.label}
                    </label>
                    <input
                      type="number"
                      step="any"
                      value={
                        params[param.field as keyof FDPBDParams][param.index]
                      }
                      onChange={(e) =>
                        handleInputChange(
                          e,
                          param.field as keyof FDPBDParams,
                          param.index
                        )
                      }
                      className={`bg-gray-800 text-white p-2 rounded focus:outline-none border-2 ${
                        isValidDecimal(
                          params[param.field as keyof FDPBDParams][param.index]
                        )
                          ? "border-gray-600 focus:border-teal-500"
                          : "border-red-500"
                      }`}
                      disabled={isProcessing}
                      required
                    />
                  </div>
                ))}
              </div>
              {/* Sample Layer */}
              <div className="bg-gray-700 p-4 rounded-lg mb-4">
                <h4 className="text-white text-sm font-semibold mb-2">
                  Sample Layer
                </h4>
                {[
                  {
                    field: "lambda_down",
                    index: 2,
                    label: `Lambda Down [${fieldUnits.lambda_down}]`,
                  },
                  {
                    field: "c_down",
                    index: 2,
                    label: `C Down [${fieldUnits.c_down}]`,
                  },
                  {
                    field: "h_down",
                    index: 2,
                    label: `H Down [${fieldUnits.h_down}]`,
                  },
                  {
                    field: "eta_down",
                    label: `Eta Down ${
                      fieldUnits.eta_down ? `[${fieldUnits.eta_down}]` : ""
                    }`,
                  },
                  {
                    field: "alpha_t",
                    label: `Alpha T [${fieldUnits.alpha_t}]`,
                  },
                  {
                    field: "niu",
                    label: `Niu ${fieldUnits.niu ? `[${fieldUnits.niu}]` : ""}`,
                  },
                ].map((param) => (
                  <div
                    key={`${param.field}${param.index ?? ""}`}
                    className="flex flex-col mb-2"
                  >
                    <label className="text-white text-sm mb-1">
                      {param.label}
                    </label>
                    <input
                      type={param.field === "eta_down" ? "text" : "number"}
                      step={param.field === "eta_down" ? undefined : "any"}
                      value={
                        param.index !== undefined
                          ? params[param.field as keyof FDPBDParams][
                              param.index
                            ]
                          : params[param.field as keyof FDPBDParams]
                      }
                      onChange={(e) =>
                        handleInputChange(
                          e,
                          param.field as keyof FDPBDParams,
                          param.index
                        )
                      }
                      className={`bg-gray-800 text-white p-2 rounded focus:outline-none border-2 ${
                        isValidDecimal(
                          param.index !== undefined
                            ? params[param.field as keyof FDPBDParams][
                                param.index
                              ]
                            : params[param.field as keyof FDPBDParams]
                        )
                          ? "border-gray-600 focus:border-teal-500"
                          : "border-red-500"
                      }`}
                      disabled={isProcessing}
                      required
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Buttons */}
            <div className="flex space-x-4">
              <button
                onClick={handleSubmit}
                disabled={isProcessing || !isFormValid()}
                className={`flex-1 py-2 rounded text-white ${
                  isProcessing || !isFormValid()
                    ? "bg-gray-600 cursor-not-allowed"
                    : "bg-teal-500 hover:bg-teal-600"
                }`}
              >
                {isProcessing ? "Processing..." : "Run Analysis"}
              </button>
              <button
                onClick={handleClear}
                className="flex-1 py-2 rounded text-white bg-gray-500 hover:bg-gray-600"
                disabled={isProcessing}
              >
                Clear
              </button>
            </div>
            {status && (
              <p
                className={`mt-2 text-sm ${
                  status.includes("Error") ? "text-red-400" : "text-green-400"
                }`}
              >
                {status}
              </p>
            )}
          </div>
        </div>

        {/* Right Panel: Results and Graphs */}
        <div className="w-2/3 flex flex-col space-y-4">
          {result && (
            <>
              <div className="bg-gray-800 p-4 rounded-lg shadow-md">
                <h2 className="text-white text-lg font-semibold mb-4">
                  Results
                </h2>
                <p className="text-white">
                  Thermal Conductivity: {result.lambda_measure.toFixed(3)} W/m-K
                </p>
                <p className="text-white">
                  Thermal Expansion: {result.alpha_t_fitted.toExponential(3)} /K
                </p>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg shadow-md">
                <h2 className="text-white text-lg font-semibold mb-4">
                  Graphs
                </h2>
                <div className="flex flex-col space-y-4">
                  <Plot
                    data={[
                      {
                        x: result.plot_data.freq_fit,
                        y: result.plot_data.v_corr_in_fit,
                        type: "scatter",
                        mode: "markers",
                        name: "In-phase (data)",
                        marker: { color: "black" },
                      },
                      {
                        x: result.plot_data.freq_fit,
                        y: result.plot_data.v_corr_out_fit,
                        type: "scatter",
                        mode: "markers",
                        name: "Out-of-phase (data)",
                        marker: { color: "black" },
                      },
                      {
                        x: result.plot_data.freq_fit,
                        y: result.plot_data.delta_in,
                        type: "scatter",
                        mode: "lines",
                        name: "In-phase (model)",
                        line: { color: "blue" },
                      },
                      {
                        x: result.plot_data.freq_fit,
                        y: result.plot_data.delta_out,
                        type: "scatter",
                        mode: "lines",
                        name: "Out-of-phase (model)",
                        line: { color: "red" },
                      },
                    ]}
                    layout={{
                      title: "In/Out-of-phase",
                      xaxis: {
                        title: {
                          text: "Frequency (Hz)",
                          font: { size: 14, color: "black" },
                          standoff: 10,
                        },
                        type: "log",
                        showgrid: false,
                        tickfont: { size: 12, color: "black" },
                        showticklabels: true,
                        tickmode: "auto",
                        nticks: 3, // Limit to major ticks
                      },
                      yaxis: {
                        title: {
                          text: "In/Out-of-phase (V)",
                          font: { size: 14, color: "black" },
                          standoff: 10,
                        },
                        showgrid: false,
                        tickfont: { size: 12, color: "black" },
                        showticklabels: true,
                        tickmode: "auto",
                        nticks: 5, // Limit to major ticks
                      },
                      legend: { x: 1, xanchor: "right", y: 1 },
                      plot_bgcolor: "white",
                      paper_bgcolor: "white",
                      font: { color: "black" },
                      width: 800,
                      height: 400,
                      margin: { l: 60, r: 40, t: 60, b: 60 },
                      shapes: [
                        {
                          type: "rect",
                          xref: "paper",
                          yref: "paper",
                          x0: 0,
                          y0: 0,
                          x1: 1,
                          y1: 1,
                          line: { color: "black", width: 2 },
                        },
                      ],
                    }}
                  />
                  <Plot
                    data={[
                      {
                        x: result.plot_data.freq_fit,
                        y: result.plot_data.v_corr_ratio_fit,
                        type: "scatter",
                        mode: "markers",
                        name: "Ratio (data)",
                        marker: { color: "black" },
                      },
                      {
                        x: result.plot_data.freq_fit,
                        y: result.plot_data.delta_ratio,
                        type: "scatter",
                        mode: "lines",
                        name: "Ratio (model)",
                        line: { color: "blue" },
                      },
                    ]}
                    layout={{
                      title: "Ratio",
                      xaxis: {
                        title: {
                          text: "Frequency (Hz)",
                          font: { size: 14, color: "black" },
                          standoff: 10,
                        },
                        type: "log",
                        showgrid: false,
                        tickfont: { size: 12, color: "black" },
                        showticklabels: true,
                        tickmode: "auto",
                        nticks: 3, // Limit to major ticks
                      },
                      yaxis: {
                        title: {
                          text: "Ratio",
                          font: { size: 14, color: "black" },
                          standoff: 10,
                        },
                        type: "log",
                        showgrid: false,
                        tickfont: { size: 12, color: "black" },
                        showticklabels: true,
                        tickmode: "auto",
                        nticks: 5, // Limit to major ticks
                      },
                      legend: { x: 1, xanchor: "right", y: 1 },
                      plot_bgcolor: "white",
                      paper_bgcolor: "white",
                      font: { color: "black" },
                      width: 800,
                      height: 400,
                      margin: { l: 60, r: 40, t: 60, b: 60 },
                      shapes: [
                        {
                          type: "rect",
                          xref: "paper",
                          yref: "paper",
                          x0: 0,
                          y0: 0,
                          x1: 1,
                          y1: 1,
                          line: { color: "black", width: 2 },
                        },
                      ],
                    }}
                  />
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-800 p-2 text-white text-sm flex justify-between">
        <div>Status: {status || "Idle"}</div>
        <div>{new Date().toLocaleString()}</div>
      </footer>
    </div>
  );
}
