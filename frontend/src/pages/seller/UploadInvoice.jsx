import { useState } from "react";
import { useNavigate } from "react-router-dom";
import bgImage from "../../assets/background.jpeg";

export default function UploadInvoice() {
  const navigate = useNavigate();
  const [buyerGstin, setBuyerGstin] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  const handleFileUpload = async (e) => {
    if (!e.target.files || e.target.files.length === 0) return;
    
    if (!buyerGstin.trim()) {
      alert("Please enter a Buyer ID (GSTIN) first.");
      // Reset file input
      e.target.value = null;
      return;
    }

    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("buyer_gstin", buyerGstin);

    setIsUploading(true);
    try {
      const response = await fetch("http://localhost:8000/invoices/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to upload invoice");
      }

      const result = await response.json();
      alert("Invoice sent to buyer! Invoice ID: " + result.invoice_id);
      navigate("/seller/invoices"); // Go view sent invoices
    } catch (err) {
      console.error(err);
      alert("Error uploading invoice. Please check the backend connection.");
    } finally {
      setIsUploading(false);
      e.target.value = null;
    }
  };

  return (
    <div className="w-full min-h-screen relative bg-white flex flex-col items-center justify-center font-sans overflow-hidden">
      
      {/* Background Image Container mapped to 1346x782 placement */}
      <div 
         className="absolute inset-0 z-0 bg-cover bg-center"
         style={{ backgroundImage: `url(${bgImage})` }}
      ></div>

      {/* Floating Upload Widget - Box mapped to 508x330 measurements */}
      <div className="relative z-10 w-full max-w-[540px] min-h-[400px] mx-4 bg-white rounded-[2rem] border-[2px] border-[#D50000] shadow-[0_10px_35px_rgba(0,0,0,0.1),0_0_15px_rgba(0,0,0,0.06)] flex flex-col items-center p-8 md:p-12 gap-8 mt-16 group transition-shadow duration-300 hover:shadow-[0_15px_45px_rgba(0,0,0,0.12)]">
         
         <div className="flex flex-col items-center justify-center gap-4 opacity-100 transition-opacity duration-300">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 text-[#D50000]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="text-[#D50000] font-bold text-xl tracking-wide text-center">Share Invoice with Buyer</p>
         </div>

         {/* Buyer ID Input */}
         <div className="w-full flex flex-col gap-2">
            <label className="text-gray-700 font-semibold ml-1">Buyer ID (GSTIN)</label>
            <input 
              type="text" 
              placeholder="e.g. BUYER_123"
              value={buyerGstin}
              onChange={(e) => setBuyerGstin(e.target.value)}
              className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 focus:outline-none focus:border-[#D50000] transition-colors"
            />
         </div>

         {/* Action Buttons */}
         <div className="w-full flex justify-center items-center gap-4 flex-wrap mt-2">
            <label 
               className={`flex-1 min-w-[210px] whitespace-nowrap text-center cursor-pointer bg-[#D50000] text-white py-[14px] px-4 rounded-xl font-bold text-[1.15rem] shadow-[0_4px_10px_rgba(213,0,0,0.15)] hover:bg-[#b00116] hover:shadow-[0_6px_15px_rgba(213,0,0,0.25)] transition-all duration-200 active:scale-[0.98] flex justify-center items-center ${isUploading ? "opacity-50 cursor-not-allowed" : ""}`}
            >
               <span>{isUploading ? "Uploading..." : "Upload From Device"}</span>
               <input 
                 type="file" 
                 className="hidden" 
                 onChange={handleFileUpload} 
                 disabled={isUploading}
                 accept=".pdf,image/png,image/jpeg,image/tiff,image/webp"
               />
            </label>
         </div>
      </div>

    </div>
  );
}