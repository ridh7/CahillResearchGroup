"use client";

import { useState } from "react";
import Plot from "react-plotly.js";

type FDPBDParams = {
  f_amp: number;
  delay_1: number;
  delay_2: number;
  lambda_down: number[];
  eta_down: number[];
  c_down: number[];
  h_down: number[];
  niu: number;
  alpha_t: number;
  lambda_up: number;
  eta_up: number;
  c_up: number;
  h_up: number;
  r_rms: number;
  x_offset: number;
  incident_pump: number;
  incident_probe: number;
  n_al: number;
  k_al: number;
  lens_transmittance: number;
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
    f_amp: 95000,
    delay_1: 0.0000089,
    delay_2: -1.3e-11,
    lambda_down: [149.0, 0.1, 9.7],
    eta_down: [1.0, 1.0, 1.0],
    c_down: [2440000, 100000, 2730000],
    h_down: [7e-8, 1e-9, 1e-6],
    niu: 0.26,
    alpha_t: 0.00001885,
    lambda_up: 0.028,
    eta_up: 1.0,
    c_up: 1192.0,
    h_up: 0.001,
    r_rms: 0.0000112,
    x_offset: 0.0000126,
    incident_pump: 0.00106,
    incident_probe: 0.00085,
    n_al: 2.9,
    k_al: 8.2,
    lens_transmittance: 0.93,
  });
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<FDPBDResult | null>(null);
  const [status, setStatus] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState(false);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    field: keyof FDPBDParams
  ) => {
    const value = e.target.value;
    if (["lambda_down", "eta_down", "c_down", "h_down"].includes(field)) {
      setParams((prev) => ({
        ...prev,
        [field]: value
          .split(",")
          .map(Number)
          .filter((n) => !isNaN(n)),
      }));
    } else {
      setParams((prev) => ({
        ...prev,
        [field]: Number(value) || 0,
      }));
    }
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
    formData.append("params", JSON.stringify(params));

    try {
      const response = await fetch("http://localhost:8000/fdpbd/analyze", {
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
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(params).map(([key, value]) => (
                <div key={key} className="flex flex-col">
                  <label className="text-white text-sm mb-1 capitalize">
                    {key.replace("_", " ")}
                  </label>
                  <input
                    type="text"
                    value={Array.isArray(value) ? value.join(",") : value}
                    onChange={(e) =>
                      handleInputChange(e, key as keyof FDPBDParams)
                    }
                    className="bg-gray-700 text-white p-2 rounded focus:outline-none focus:ring-2 focus:ring-teal-400"
                    disabled={isProcessing}
                  />
                </div>
              ))}
            </div>
            <div className="mt-4">
              <label className="text-white text-sm mb-1">
                Data File (.txt)
              </label>
              <input
                type="file"
                accept=".txt"
                onChange={handleFileChange}
                className="bg-gray-700 text-white p-2 rounded w-full"
                disabled={isProcessing}
              />
            </div>
            <button
              onClick={handleSubmit}
              disabled={isProcessing || !file}
              className={`mt-4 w-full py-2 rounded text-white ${
                isProcessing || !file
                  ? "bg-gray-600 cursor-not-allowed"
                  : "bg-teal-500 hover:bg-teal-600"
              }`}
            >
              {isProcessing ? "Processing..." : "Run Analysis"}
            </button>
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
                  Thermal Conductivity: {result.lambda_measure.toFixed(4)} W/m-K
                </p>
                <p className="text-white">
                  Thermal Expansion: {result.alpha_t_fitted.toExponential(4)} /K
                </p>
                {/* <p className="text-white">
                  Steady-State Temperature Rise: {result.t_ss_heat.toFixed(2)} K
                </p> */}
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
