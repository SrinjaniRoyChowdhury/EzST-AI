import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";

export default function InvoiceDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reason, setReason] = useState("");
  const [updating, setUpdating] = useState(false);
  const [showModBox, setShowModBox] = useState(false);
  const [actionType, setActionType] = useState(""); // "modified" or "rejected"

  useEffect(() => {
    const fetchInvoice = async () => {
      try {
        const response = await fetch(`http://localhost:8000/invoices/${id}`);
        if (!response.ok) throw new Error("Failed to fetch invoice");
        const data = await response.json();
        setInvoice(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchInvoice();
  }, [id]);

  const handleUpdateStatus = async (status) => {
    if ((status === "rejected" || status === "modified") && !reason.trim()) {
      alert(`Please provide a reason for marking as ${status}.`);
      return;
    }

    setUpdating(true);
    try {
      const response = await fetch(`http://localhost:8000/invoices/${id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status, reason }),
      });

      if (!response.ok) throw new Error("Failed to update status");
      alert(`Invoice marked as ${status.toUpperCase()}!`);
      navigate(-1); // Go back to dashboard
    } catch (err) {
      console.error(err);
      alert("Error updating status");
    } finally {
      setUpdating(false);
    }
  };

  const handleSuggestClick = (type) => {
    setActionType(type);
    setShowModBox(true);
  };

  if (loading) {
    return <div className="p-10 text-center font-bold text-2xl">Loading Invoice Details...</div>;
  }

  if (!invoice) {
    return <div className="p-10 text-center font-bold text-2xl text-red-500">Invoice Not Found!</div>;
  }

  return (
    <div className="w-full min-h-screen bg-gray-50 flex flex-col items-center py-12 px-4 md:px-12 font-sans">
      <div className="w-full max-w-6xl flex justify-between items-center mb-8">
         <button 
           onClick={() => navigate(-1)}
           className="text-[#D50000] font-bold flex items-center gap-2 hover:bg-red-50 p-2 rounded-lg transition-colors"
         >
           ← Back to Dashboard
         </button>
         <h1 className="text-3xl font-extrabold text-gray-900">
           Review Invoice
         </h1>
         <div className="w-24"></div> {/* Spacer to center title */}
      </div>

      <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Side: Document Viewer */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden flex flex-col h-[700px]">
           <div className="bg-gray-100 p-4 border-b border-gray-200">
             <h2 className="font-bold text-gray-700">Document Viewer</h2>
           </div>
           <div className="flex-1 bg-gray-50 flex items-center justify-center p-2">
              {invoice.file_url ? (
                 <embed 
                   src={`http://localhost:8000/uploads/${invoice.file_url}#toolbar=0`} 
                   className="w-full h-full rounded shadow-sm border border-gray-200 bg-white"
                 />
              ) : (
                 <div className="text-gray-400 font-bold text-xl flex flex-col items-center">
                    <span className="text-6xl mb-4">📄</span>
                    No document attached
                 </div>
              )}
           </div>
        </div>

        {/* Right Side: Details & Actions */}
        <div className="flex flex-col gap-6">
           {/* Details Card */}
           <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 flex flex-col gap-4">
              <h3 className="text-xl font-bold border-b pb-2">Invoice Summary</h3>
              
              <div className="flex justify-between">
                <span className="text-gray-500 font-semibold">Number</span>
                <span className="font-bold text-gray-900">{invoice.invoice_number || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 font-semibold">Date</span>
                <span className="font-bold text-gray-900">{invoice.invoice_date || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 font-semibold">Total Amount</span>
                <span className="font-black text-[#D50000] text-xl">₹{invoice.grand_total || 0}</span>
              </div>
              <div className="flex justify-between items-center mt-2 pt-2 border-t">
                <span className="text-gray-500 font-semibold">Current Status</span>
                <span className={`px-3 py-1 rounded-full text-sm font-bold bg-gray-100 ${invoice.status === 'accepted' ? 'text-green-600 bg-green-100' : invoice.status === 'rejected' ? 'text-red-600 bg-red-100' : 'text-blue-600 bg-blue-100'}`}>
                   {invoice.status.toUpperCase()}
                </span>
              </div>
           </div>

           {/* Actions Card */}
           <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 flex flex-col gap-4">
              <h3 className="text-xl font-bold mb-2">Buyer Actions</h3>
              
              {!showModBox ? (
                 <div className="flex flex-col gap-3 mt-2">
                   <button 
                     onClick={() => handleUpdateStatus("accepted")}
                     disabled={updating}
                     className="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-3 rounded-xl shadow-md transition-all active:scale-[0.98] disabled:opacity-50"
                   >
                     Confirm & Accept
                   </button>
                   <div className="flex gap-3">
                      <button 
                        onClick={() => handleSuggestClick("modified")}
                        disabled={updating}
                        className="flex-1 bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-3 rounded-xl shadow-md transition-all active:scale-[0.98] disabled:opacity-50"
                      >
                        Suggest Mods
                      </button>
                      <button 
                        onClick={() => handleSuggestClick("rejected")}
                        disabled={updating}
                        className="flex-1 bg-[#D50000] hover:bg-red-700 text-white font-bold py-3 rounded-xl shadow-md transition-all active:scale-[0.98] disabled:opacity-50"
                      >
                        Reject
                      </button>
                   </div>
                 </div>
              ) : (
                 <div className="flex flex-col gap-3 mt-2 animate-fade-in">
                    <p className="text-sm font-bold text-gray-700 mb-1">
                      {actionType === "modified" ? "What modifications do you suggest?" : "Why are you rejecting this invoice?"}
                    </p>
                    <textarea
                      className="w-full border-2 border-gray-200 p-3 rounded-xl focus:outline-none focus:border-[#D50000] min-h-[120px] resize-y transition-colors"
                      placeholder="Type your message to the seller here..."
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      disabled={updating}
                    />
                    <div className="flex gap-3 mt-2">
                       <button 
                         onClick={() => setShowModBox(false)}
                         disabled={updating}
                         className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-3 rounded-xl transition-all active:scale-[0.98]"
                       >
                         Cancel
                       </button>
                       <button 
                         onClick={() => handleUpdateStatus(actionType)}
                         disabled={updating}
                         className="flex-[2] bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl shadow-md transition-all active:scale-[0.98] flex items-center justify-center gap-2"
                       >
                         <span>Send {actionType === "modified" ? "Suggestions" : "Rejection"}</span>
                         <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                           <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                         </svg>
                       </button>
                    </div>
                 </div>
              )}
           </div>
        </div>

      </div>
    </div>
  );
}