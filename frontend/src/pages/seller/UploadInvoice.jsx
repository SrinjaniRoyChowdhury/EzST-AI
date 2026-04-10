export default function UploadInvoice() {
  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Upload Invoice</h2>

      <input type="file" className="mb-4" />

      <div className="flex gap-4">
        <button className="bg-blue-500 text-white px-4 py-2 rounded">
          Upload
        </button>

        <button className="bg-purple-500 text-white px-4 py-2 rounded">
          Validate Invoice (AI)
        </button>
      </div>
    </div>
  );
}