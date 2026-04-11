import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import bgImage from "../../assets/background.jpeg";

export default function CheckYourInvoice() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("All");
  const [buyerGstin, setBuyerGstin] = useState("BUYER_123");
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(false);

  const tabs = ["All", "Pending", "SHARED", "ACCEPTED", "REJECTED", "MODIFIED"];

  const fetchInvoices = async () => {
    if (!buyerGstin) return;
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/invoices/buyer/received?buyer_gstin=${buyerGstin}`);
      if (!response.ok) throw new Error("Failed to fetch");
      const data = await response.json();
      setInvoices(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, [buyerGstin]);

  const filteredInvoices = invoices.filter((inv) => {
    if (activeTab === "All") return true;
    if (activeTab === "Pending") return inv.status.toLowerCase() === "pending" || inv.status.toLowerCase() === "shared";
    return inv.status.toUpperCase() === activeTab.toUpperCase();
  });

  return (
    <div className="w-full min-h-screen bg-white font-sans flex flex-col">
      
      {/* Top Banner Section */}
      <div 
        className="relative w-full py-16 md:py-24 px-6 md:px-16 lg:px-32 bg-cover bg-center flex flex-col justify-end"
        style={{ backgroundImage: `url(${bgImage})` }}
      >
        <div className="absolute inset-0 bg-black/15"></div>

        <div className="relative z-10 w-full max-w-7xl mx-auto flex flex-col items-start gap-8 mt-6 lg:mt-12">
          <h1 className="text-white text-5xl md:text-[4rem] leading-none font-bold font-inter tracking-tight drop-shadow-[0_4px_4px_rgba(0,0,0,0.5)]">
            Your Invoices
          </h1>
          
          <div className="flex flex-col gap-2 p-4 bg-white/20 backdrop-blur-md rounded-xl w-full max-w-sm">
             <label className="text-white font-bold drop-shadow-md">Enter Your Buyer ID (GSTIN):</label>
             <div className="flex gap-2">
                <input 
                  type="text" 
                  value={buyerGstin}
                  onChange={(e) => setBuyerGstin(e.target.value)}
                  placeholder="BUYER_123"
                  className="flex-1 px-3 py-2 rounded-lg text-black font-semibold focus:outline-none"
                />
             </div>
          </div>

          <div className="flex flex-wrap gap-4 md:gap-6 mt-2">
            {tabs.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`
                  px-6 py-3 rounded-[0.75rem] font-extrabold text-lg font-inter transition-all duration-200 shadow-md flex items-center justify-center
                  ${
                    activeTab === tab
                      ? "bg-[#D50000] text-white hover:bg-red-700"
                      : "bg-transparent border-2 border-white/80 text-white hover:bg-white/10 drop-shadow-[0_4px_4px_rgba(0,0,0,0.25)]"
                  }
                `}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Invoices Grid Section */}
      <div className="w-full flex-1 mb-20 px-6 md:px-16 lg:px-32 flex justify-center">
        <div className="w-full max-w-7xl py-12 md:py-20 flex flex-col">
          {loading ? (
             <div className="text-center text-2xl font-bold text-gray-500 py-20">Loading Invoices...</div>
          ) : filteredInvoices.length === 0 ? (
             <div className="text-center text-2xl font-bold text-gray-400 py-20">No invoices found for this ID.</div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-20">
              {filteredInvoices.map((inv) => (
                <div 
                  key={inv.id} 
                  className="flex flex-col gap-6 group cursor-pointer"
                  onClick={() => navigate(`/buyer/invoice/${inv.id}`)}
                >
                  <div className="w-full h-80 rounded-2xl overflow-hidden shadow-[0_4px_10px_rgba(0,0,0,0.12)] group-hover:shadow-[0_8px_24px_rgba(0,0,0,0.18)] transition-all duration-300 relative border border-gray-100 flex items-center justify-center bg-gray-50">
                    {inv.file_url ? (
                       <embed src={`http://localhost:8000/uploads/${inv.file_url}#toolbar=0&navpanes=0&scrollbar=0`} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                    ) : (
                       <div className="text-gray-400 text-6xl">📄</div>
                    )}
                    <div className="absolute inset-0 bg-black/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  </div>
                  
                  <div className="flex justify-between items-baseline px-2 gap-4">
                    <div className="flex flex-col">
                       <h3 className="text-black text-2xl font-bold font-inter leading-snug group-hover:text-[#D50000] transition-colors line-clamp-2">
                         {inv.invoice_number || `Invoice from ${inv.seller_id}`}
                       </h3>
                       <p className="text-[#D50000] font-bold text-sm uppercase">Status: {inv.status}</p>
                    </div>
                    <div className="flex flex-col items-end">
                       <p className="text-black font-extrabold text-xl">₹{inv.grand_total || "N/A"}</p>
                       <p className="text-black/55 text-lg font-medium whitespace-nowrap">
                         {inv.created_at ? new Date(inv.created_at).toLocaleDateString() : 'N/A'}
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
