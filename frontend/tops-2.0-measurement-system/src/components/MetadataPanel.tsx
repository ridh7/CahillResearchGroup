import { FormData } from "../app/page";

type MetadataPanelProps = {
  formData: FormData;
  setFormData: React.Dispatch<React.SetStateAction<FormData>>;
};

interface MetadataField {
  key: keyof FormData;
  label: string;
  type?: "text" | "textarea"; // Optional, defaults to "text"
}

export default function MetadataPanel({
  formData,
  setFormData,
}: MetadataPanelProps) {
  const metadataFields: MetadataField[] = [
    { key: "sampleId", label: "Sample ID" },
    { key: "sampleName", label: "Sample Name" },
    { key: "probeLaserPower", label: "Probe Laser Power (mW)" },
    { key: "pumpLaserPower", label: "Pump Laser Power (mW)" },
    { key: "aluminumThickness", label: "Aluminum Thickness (nm)" },
    { key: "comments", label: "Comments", type: "textarea" },
  ];

  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow-lg">
      <h2 className="text-white text-lg font-semibold mb-4">Sample Metadata</h2>
      <div className="space-y-4">
        {metadataFields.map((field) =>
          field.type === "textarea" ? (
            <textarea
              key={field.key}
              placeholder={field.label}
              className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600 focus:border-teal-500 focus:outline-none"
              value={formData[field.key as keyof FormData]}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  [field.key as keyof FormData]: e.target.value,
                })
              }
              rows={3}
            />
          ) : (
            <input
              key={field.key}
              type="text"
              placeholder={field.label}
              className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600 focus:border-teal-500 focus:outline-none"
              value={formData[field.key as keyof FormData]}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  [field.key as keyof FormData]: e.target.value,
                })
              }
            />
          )
        )}
      </div>
    </div>
  );
}
