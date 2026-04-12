import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import bgImage from "../../assets/background.jpeg";

const BUYER_GSTIN = "BUYER_123"; // Fixed - no manual entry needed

export default function CheckYourInvoice() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("All");
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(false);

  const tabs = ["All", "Pending", "ACCEPTED", "REJECTED", "MODIFIED"];

  useEffect(() => {
    const fetchInvoices = async () => {
      setLoading(true);
      try {
        const response = await fetch(
          `http://localhost:8000/invoices/buyer/received?buyer_gstin=${BUYER_GSTIN}`
        );
        if (!response.ok) throw new Error("Failed to fetch");
        const data = await response.json();
        // Sort latest first
        data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        setInvoices(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchInvoices();
  }, []);

  const filteredInvoices = invoices.filter((inv) => {
    if (activeTab === "All") return true;
    if (activeTab === "Pending")
      return (
        inv.status.toLowerCase() === "pending" ||
        inv.status.toLowerCase() === "shared"
      );
    return inv.status.toUpperCase() === activeTab.toUpperCase();
  });

  const statusColor = (status) => {
    switch ((status || "").toLowerCase()) {
      case "accepted": return "text-green-600 bg-green-50 border-green-200";
      case "rejected": return "text-red-600 bg-red-50 border-red-200";
      case "modified": return "text-yellow-700 bg-yellow-50 border-yellow-200";
      default:         return "text-blue-600 bg-blue-50 border-blue-200";
    }
  };

  return (
    <div className="w-full min-h-screen bg-white font-sans flex flex-col">

      {/* ── Top Banner ── */}
      <div
        className="relative w-full py-16 md:py-24 px-6 md:px-16 lg:px-32 bg-cover bg-center flex flex-col justify-end"
        style={{ backgroundImage: `url(${bgImage})` }}
      >
        <div className="absolute inset-0 bg-black/20" />

        <div className="relative z-10 w-full max-w-7xl mx-auto flex flex-col items-start gap-8 mt-6 lg:mt-12">
          <h1 className="text-white text-5xl md:text-[4rem] leading-none font-bold font-inter tracking-tight drop-shadow-[0_4px_4px_rgba(0,0,0,0.5)]">
            Your Invoices
          </h1>

          {/* Filter tabs */}
          <div className="flex flex-wrap gap-3 md:gap-4">
            {tabs.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-2.5 rounded-xl font-extrabold text-base font-inter transition-all duration-200 shadow-md
                  ${activeTab === tab
                    ? "bg-[#D50000] text-white"
                    : "bg-white/10 backdrop-blur border-2 border-white/70 text-white hover:bg-white/20"
                  }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Invoices Grid ── */}
      <div className="w-full flex-1 mb-24 px-6 md:px-16 lg:px-32 flex justify-center">
        <div className="w-full max-w-7xl py-12 md:py-16">
          {loading ? (
            <div className="text-center text-2xl font-bold text-gray-400 py-24">
              Loading Invoices...
            </div>
          ) : filteredInvoices.length === 0 ? (
            <div className="flex flex-col items-center gap-4 py-24 text-gray-400">
              <span className="text-7xl">📭</span>
              <p className="text-2xl font-bold">No invoices found.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-16 gap-y-20">
              {filteredInvoices.map((inv) => (
                <div
                  key={inv.id}
                  className="flex flex-col gap-5 group cursor-pointer"
                  onClick={() => navigate(`/buyer/invoice/${inv.id}`)}
                >
                  {/* ── PDF Preview card: 504 × 390 ratio ── */}
                  <div
                    className="w-full rounded-2xl overflow-hidden shadow-[0_4px_14px_rgba(0,0,0,0.10)] group-hover:shadow-[0_10px_30px_rgba(0,0,0,0.18)] transition-all duration-300 relative border border-gray-100 bg-gray-50"
                    style={{ aspectRatio: "504 / 390" }}
                  >
                    {inv.file_url ? (
                      <embed
                        src={`http://localhost:8000/uploads/${inv.file_url}#toolbar=0&navpanes=0&scrollbar=0&view=FitH`}
                        type="application/pdf"
                        className="w-full h-full pointer-events-none"
                      />
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center gap-3 text-gray-300">
                        <span className="text-6xl">📄</span>
                        <span className="font-semibold text-sm">No preview available</span>
                      </div>
                    )}
                    {/* Hover overlay */}
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors duration-300 flex items-end p-4">
                      <span className="opacity-0 group-hover:opacity-100 transition-opacity bg-white/90 backdrop-blur-sm text-[#D50000] font-bold text-sm px-3 py-1.5 rounded-lg shadow">
                        Click to review →
                      </span>
                    </div>
                  </div>

                  {/* ── Invoice meta below card ── */}
                  <div className="flex justify-between items-start px-1 gap-4">
                    <div className="flex flex-col gap-1.5 min-w-0">
                      <h3 className="text-black text-xl font-bold font-inter leading-snug group-hover:text-[#D50000] transition-colors truncate">
                        {inv.invoice_number || `Invoice #${inv.id.slice(0, 8)}`}
                      </h3>
                      <span className={`inline-block self-start px-3 py-0.5 rounded-full border text-xs font-bold uppercase tracking-wide ${statusColor(inv.status)}`}>
                        {inv.status}
                      </span>
                    </div>
                    <div className="flex flex-col items-end shrink-0 gap-1">
                      <p className="text-black font-extrabold text-2xl">
                        ₹{Number(inv.grand_total || 0).toLocaleString("en-IN")}
                      </p>
                      <p className="text-gray-400 text-sm font-medium whitespace-nowrap">
                        {inv.invoice_date
                          ? new Date(inv.invoice_date).toLocaleDateString("en-IN", {
                              day: "2-digit", month: "short", year: "numeric",
                            })
                          : inv.created_at
                          ? new Date(inv.created_at).toLocaleDateString("en-IN", {
                              day: "2-digit", month: "short", year: "numeric",
                            })
                          : "N/A"}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
