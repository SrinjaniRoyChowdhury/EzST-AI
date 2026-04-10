export default function SentInvoices() {
  const invoices = [
    { id: 1, buyer: "Client A", status: "Pending" },
    { id: 2, buyer: "Client B", status: "Accepted" },
  ];

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Sent Invoices</h2>

      {invoices.map((inv) => (
        <div key={inv.id} className="border p-3 mb-2 rounded">
          <p>Buyer: {inv.buyer}</p>
          <p>Status: {inv.status}</p>
        </div>
      ))}
    </div>
  );
}