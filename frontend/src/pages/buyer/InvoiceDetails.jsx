import { useParams } from "react-router-dom";

export default function InvoiceDetails() {
  const { id } = useParams();

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">
        Modify Invoice #{id}
      </h2>

      <textarea
        className="w-full border p-2 mb-4"
        placeholder="Enter changes..."
      />

      <button className="bg-blue-500 text-white px-4 py-2 rounded">
        Submit
      </button>
    </div>
  );
}