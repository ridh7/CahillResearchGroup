"use client";

import { useState } from "react";

type FormData = {
  x1: string;
  x2: string;
  y1: string;
  y2: string;
  steps: string;
};

export default function CalculatePage() {
  const [formData, setFormData] = useState<FormData>({
    x1: "",
    x2: "",
    y1: "",
    y2: "",
    steps: "",
  });

  const handleSubmit = async () => {
    try {
      const response = await fetch("/api/calculate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });
      const data = await response.json();
      // Handle response data
      console.log(data);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center">
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
        </div>
      </div>
    </div>
  );
}
