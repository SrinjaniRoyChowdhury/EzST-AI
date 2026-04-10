import { useNavigate } from "react-router-dom";

export default function SellerDashboard() {
  const navigate = useNavigate();

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Seller Dashboard</h2>

      <div className="flex gap-4">
        <button
          onClick={() => navigate("/seller/upload")}
          className="bg-blue-500 text-white px-4 py-2 rounded"
        >
          Upload Invoice
        </button>

        <button
          onClick={() => navigate("/seller/invoices")}
          className="bg-gray-800 text-white px-4 py-2 rounded"
        >
          Sent Invoices
        </button>
      </div>
    </div>
  );
}