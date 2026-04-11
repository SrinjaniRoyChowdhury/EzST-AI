import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function SentInvoices() {
  const navigate = useNavigate();
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInvoices = async () => {
      try {
        const response = await fetch("http://localhost:8000/invoices/seller/my-invoices", {
           headers: {
              // Usually we'd pass Authorization: Bearer token here
           }
        });
        if (!response.ok) throw new Error("Failed to fetch");
        const data = await response.json();
        setInvoices(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchInvoices();
  }, []);

  return (
    <div className="w-full min-h-screen bg-gray-50 flex flex-col items-center font-sans tracking-tight">
      
      {/* Header Section */}
      <div className="w-full bg-[#D50000] pt-24 pb-20 px-6 flex flex-col items-center justify-center gap-4 shadow-md text-center">
        <h1 className="text-white text-4xl md:text-5xl font-bold font-inter drop-shadow-lg leading-tight mt-10">
          Your Sent Invoices
        </h1>
        <p className="text-white/80 text-xl font-medium max-w-2xl">
          Review the status of the invoices you've sent to buyers and check for requested modifications.
        </p>
      </div>

      {/* Main Content Wrapper */}
      <div className="w-full max-w-6xl flex flex-col px-4 sm:px-8 md:px-12 py-12 gap-8">
         {loading ? (
            <div className="text-center font-bold text-2xl text-gray-500 py-20">Loading your invoices...</div>
         ) : invoices.length === 0 ? (
            <div className="text-center font-bold text-2xl text-gray-400 py-20">You haven't uploaded any invoices yet.</div>
         ) : (
            <div className="grid grid-cols-1 gap-8">
               {invoices.map((inv) => (
                  <div key={inv.id} className="bg-white rounded-2xl shadow-md border-2 border-transparent hover:border-gray-200 transition-all overflow-hidden flex flex-col md:flex-row">
                     {/* Preview */}
                     <div className="w-full md:w-1/3 bg-gray-100 flex items-center justify-center p-4 min-h-[250px] border-b md:border-b-0 md:border-r border-gray-200">
                        {inv.file_url ? (
                           <embed 
                             src={`http://localhost:8000/uploads/${inv.file_url}#toolbar=0&navpanes=0&scrollbar=0`} 
                             className="w-full h-[250px] object-cover bg-white shadow-sm border border-gray-200"
                           />
                        ) : (
                           <span className="text-6xl text-gray-300">📄</span>
                        )}
                     </div>
                     
                     {/* Details */}
                     <div className="w-full md:w-2/3 p-6 flex flex-col justify-between">
                        <div>
                           <div className="flex justify-between items-start mb-4">
                              <div>
                                 <h2 className="text-2xl font-bold text-gray-900 border-b pb-1 inline-block">
                                   {inv.invoice_number || "Draft Invoice"}
                                 </h2>
                                 <p className="text-gray-500 font-medium mt-1 uppercase text-sm">
                                   To: {inv.buyer_gstin || "Unknown Buyer"}
                                 </p>
                              </div>
                              <span className={`px-4 py-2 rounded-full text-sm font-bold shadow-sm ${
                                inv.status === 'accepted' ? 'bg-green-100 text-green-700 border border-green-200' :
                                inv.status === 'rejected' ? 'bg-red-100 text-[#D50000] border border-red-200' :
                                inv.status === 'modified' ? 'bg-yellow-100 text-yellow-700 border border-yellow-200' :
                                'bg-blue-50 text-blue-600 border border-blue-200'
                              }`}>
                                {inv.status ? inv.status.toUpperCase() : "PENDING"}
                              </span>
                           </div>

                           <div className="flex gap-8 mb-4">
                             <div>
                               <p className="text-sm text-gray-400 font-bold uppercase">Date</p>
                               <p className="font-semibold">{inv.invoice_date || 'N/A'}</p>
                             </div>
                             <div>
                               <p className="text-sm text-gray-400 font-bold uppercase">Total</p>
                               <p className="font-semibold">₹{inv.grand_total || '0'}</p>
                             </div>
                           </div>
                        </div>

                        {/* Message Box if modified or rejected */}
                        {(inv.status === 'modified' || inv.status === 'rejected') && inv.buyer_action_reason && (
                           <div className="mt-4 bg-red-50/50 border border-red-100 p-4 rounded-xl flex items-start gap-4 shadow-sm">
                              <span className="text-2xl mt-1">💬</span>
                              <div className="flex-1">
                                 <p className="font-bold text-[#D50000] mb-1">
                                    Buyer {inv.status === 'modified' ? "Modification Request" : "Rejection Reason"}
                                 </p>
                                 <p className="text-gray-800 font-medium break-words">
                                    "{inv.buyer_action_reason}"
                                 </p>
                              </div>
                           </div>
                        )}
                     </div>
                  </div>
               ))}
            </div>
         )}
      </div>
    </div>
  );
}