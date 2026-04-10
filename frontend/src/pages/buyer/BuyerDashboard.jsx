import { useNavigate } from "react-router-dom";

export default function BuyerDashboard() {
  const navigate = useNavigate();

  const invoices = [
    { id: 1, seller: "ABC Pvt Ltd", amount: "₹5000" },
    { id: 2, seller: "XYZ Traders", amount: "₹12000" },
  ];

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Buyer Dashboard</h2>

      <div className="flex gap-4 mb-4">
        <button className="bg-blue-500 text-white px-3 py-2 rounded">
          Recent
        </button>

        <button
          onClick={() => navigate("/buyer/invoices")}
          className="bg-gray-800 text-white px-3 py-2 rounded"
        >
          All Invoices
        </button>
      </div>

      {invoices.map((inv) => (
        <div key={inv.id} className="border p-3 mb-3 rounded">
          <p>Seller: {inv.seller}</p>
          <p>Amount: {inv.amount}</p>

          <div className="flex gap-2 mt-2">
            <button className="bg-green-500 text-white px-2 py-1 rounded">
              Accept
            </button>
            <button className="bg-red-500 text-white px-2 py-1 rounded">
              Reject
            </button>
            <button
              onClick={() => navigate(`/buyer/invoice/${inv.id}`)}
              className="bg-yellow-500 text-white px-2 py-1 rounded"
            >
              Modify
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}