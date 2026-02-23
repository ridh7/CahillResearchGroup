import { FormData } from '../app/page';

type MetadataPanelProps = {
  formData: FormData;
  setFormData: React.Dispatch<React.SetStateAction<FormData>>;
  onBrowseSaveDir: () => void;
  defaultSaveDir: string;
};

export default function MetadataPanel({
  formData,
  setFormData,
  onBrowseSaveDir,
  defaultSaveDir,
}: MetadataPanelProps) {
  return (
    <div className="rounded-lg bg-gray-800 p-4 shadow-lg">
      <h2 className="mb-4 text-lg font-semibold text-white">Sample Metadata</h2>
      <div className="space-y-4">
        {/* Save Directory */}
        <div>
          <label className="mb-1 block text-xs text-gray-400">Save Directory</label>
          <div className="flex gap-2">
            <input
              type="text"
              readOnly
              placeholder={defaultSaveDir || 'Loading...'}
              title={formData.saveDir || defaultSaveDir}
              className="min-w-0 flex-1 overflow-hidden text-ellipsis whitespace-nowrap rounded border border-gray-600 bg-gray-700 p-2 text-sm text-gray-300 focus:outline-none"
              style={{ direction: 'rtl', textAlign: 'left', unicodeBidi: 'plaintext' }}
              value={formData.saveDir}
            />
            <button
              onClick={onBrowseSaveDir}
              className="shrink-0 rounded bg-gray-600 px-3 py-2 text-sm text-white hover:bg-gray-500"
            >
              Browse
            </button>
          </div>
        </div>

        {/* Sample ID */}
        <input
          type="text"
          placeholder="Sample ID"
          className="w-full rounded border border-gray-600 bg-gray-700 p-2 text-white focus:border-teal-500 focus:outline-none"
          value={formData.sampleId}
          onChange={(e) => setFormData({ ...formData, sampleId: e.target.value })}
        />

        {/* Comments */}
        <textarea
          placeholder="Comments"
          className="w-full rounded border border-gray-600 bg-gray-700 p-2 text-white focus:border-teal-500 focus:outline-none"
          value={formData.comments}
          onChange={(e) => setFormData({ ...formData, comments: e.target.value })}
          rows={3}
        />
      </div>
    </div>
  );
}
