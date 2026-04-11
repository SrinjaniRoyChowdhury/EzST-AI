import { useNavigate } from "react-router-dom";
import bgImage from "../../assets/background.jpeg";
import whitebgImage from "../../assets/whitebackground.jpeg";

export default function SellerDashboard() {
  const navigate = useNavigate();

  return (
    <div className="w-full min-h-screen bg-white font-sans overflow-x-hidden flex flex-col items-center">
      
      {/* 1. Hero Section */}
      <div 
        className="w-full flex flex-col items-center pt-28 md:pt-36 pb-56 md:pb-64 px-6 sm:px-16 bg-cover bg-center"
        style={{ backgroundImage: `url(${whitebgImage})` }}
      >
        <div className="flex flex-col items-center gap-10 max-w-4xl w-full z-10 relative">
           
           <div className="flex flex-col items-center gap-4 text-center">
              <h1 className="text-[#D50000] text-5xl md:text-[4rem] font-bold font-inter leading-tight tracking-tight drop-shadow-sm">
                 Hello, Mr. Roy
              </h1>
              <p className="text-[#D50000]/90 text-lg md:text-[1.25rem] font-medium font-inter max-w-[28rem] leading-relaxed drop-shadow-sm">
                 Submit your invoices quickly and securely so we can process and reconcile your payments faster.
              </p>
           </div>
           
           <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6 w-full mt-2">
              <button 
                 onClick={() => navigate("/seller/upload")}
                 className="w-full sm:w-auto min-w-[200px] bg-white text-[#D50000] px-8 py-4 rounded-[0.75rem] font-extrabold text-lg shadow-[0_4px_10px_rgba(0,0,0,0.1)] hover:shadow-[0_8px_20px_rgba(0,0,0,0.15)] transition-all duration-200 active:scale-95 border border-gray-100 flex justify-center items-center"
              >
                 Upload Invoice
              </button>
              <button 
                 onClick={() => navigate("/seller/invoices")}
                 className="w-full sm:w-auto min-w-[200px] bg-transparent text-[#D50000] px-8 py-4 rounded-[0.75rem] font-extrabold text-lg border-2 border-[#D50000] hover:bg-[#D50000]/5 transition-all duration-200 active:scale-95 flex justify-center items-center"
              >
                 Go to Dashboard
              </button>
           </div>
           
        </div>
      </div>

      {/* Overlapping Image using negative margin to keep document flow responsive */}
      <div className="w-full px-4 sm:px-8 md:px-12 flex justify-center -mt-40 md:-mt-48 mb-24 z-20 relative">
         <div className="w-full max-w-6xl rounded-[1.5rem] md:rounded-[2rem] overflow-hidden border-[2px] border-[#D50000] shadow-[0_8px_30px_rgba(0,0,0,0.12),0_0_10px_rgba(0,0,0,0.06)] bg-white aspect-[1154/751] group">
            <img 
              src="https://placehold.co/1154x751/fcfcfc/dddddd?text=Seller+Dashboard+Interface" 
              alt="Seller Dashboard" 
              className="w-full h-full object-cover group-hover:scale-[1.01] transition-transform duration-500 ease-out" 
            />
         </div>
      </div>

      {/* NEW: Seller Dashboard Body Sections */}
      <div className="w-full flex justify-center py-16 px-6 relative z-10">
        <h2 className="text-[#D50000] text-5xl md:text-6xl font-bold font-inter text-center">
            Seller Dashboard
        </h2>
      </div>

      {/* Accepted & Rejected Cards */}
      <div className="max-w-6xl w-full px-6 flex flex-col md:flex-row justify-center gap-12 mb-32 z-10 relative">
        {/* Accepted Card */}
        <div className="flex-1 flex flex-col gap-6 max-w-sm w-full mx-auto group">
            <div className="w-full aspect-[388/236] rounded-2xl overflow-hidden shadow-[0_4px_15px_rgba(0,0,0,0.1)] border-[2px] border-transparent group-hover:border-green-400 transition-colors duration-300">
                <img src="https://placehold.co/388x236/f0fdf4/bbf7d0?text=Accepted+Docs" alt="Accepted" className="w-full h-full object-cover"/>
            </div>
            <div className="flex flex-col gap-2 text-center md:text-left">
                <h3 className="text-[#D50000] text-2xl font-bold font-inter">Accepted Invoices</h3>
                <p className="text-black/55 text-lg font-medium font-inter leading-relaxed">
                    All required details are correct, and the invoice is now sent for payment processing.
                </p>
            </div>
        </div>

        {/* Rejected Card */}
        <div className="flex-1 flex flex-col gap-6 max-w-sm w-full mx-auto group">
            <div className="w-full aspect-[394/234] rounded-2xl overflow-hidden shadow-[0_4px_15px_rgba(0,0,0,0.1)] border-[2px] border-transparent group-hover:border-red-400 transition-colors duration-300">
                <img src="https://placehold.co/394x234/fef2f2/fecaca?text=Rejected+Docs" alt="Rejected" className="w-full h-full object-cover"/>
            </div>
            <div className="flex flex-col gap-2 text-center md:text-left">
                <h3 className="text-[#D50000] text-2xl font-bold font-inter">Rejected Invoices</h3>
                <p className="text-black/55 text-lg font-medium font-inter leading-relaxed">
                    Review the suggested changes, update the details, and resubmit to complete the process.
                </p>
            </div>
        </div>
      </div>

      {/* Cleared Invoices Section */}
      <div 
        className="w-full flex flex-col items-center pt-24 pb-32 px-6 sm:px-16 bg-cover bg-center"
        style={{ backgroundImage: `url(${bgImage})` }}
      >
        <h2 className="text-[#D50000] text-5xl md:text-6xl font-bold font-inter text-center mb-16 drop-shadow-sm">
            Cleared Invoices
        </h2>

        {/* Grid 2x2 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 md:gap-12 max-w-5xl w-full mb-20">
            <div className="w-full aspect-[504/390] rounded-2xl overflow-hidden shadow-lg border border-gray-100 group">
                <img src="https://placehold.co/504x390/f8f8f8/e5e5e5?text=Doc+1" alt="Invoice 1" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out" />
            </div>
            <div className="w-full aspect-[504/390] rounded-2xl overflow-hidden shadow-lg border border-gray-100 group">
                <img src="https://placehold.co/504x390/f8f8f8/e5e5e5?text=Doc+2" alt="Invoice 2" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out" />
            </div>
            <div className="w-full aspect-[504/390] rounded-2xl overflow-hidden shadow-lg border border-gray-100 group">
                <img src="https://placehold.co/504x390/f8f8f8/e5e5e5?text=Doc+3" alt="Invoice 3" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out" />
            </div>
            <div className="w-full aspect-[504/390] rounded-2xl overflow-hidden shadow-lg border border-gray-100 group">
                <img src="https://placehold.co/504x390/f8f8f8/e5e5e5?text=Doc+4" alt="Invoice 4" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out" />
            </div>
        </div>

        {/* Calculate GST */}
        <button className="bg-[#D50000] text-white px-12 py-5 rounded-2xl font-extrabold text-2xl md:text-3xl shadow-[0_6px_20px_rgba(213,0,0,0.3)] hover:bg-[#b00116] hover:shadow-[0_8px_25px_rgba(213,0,0,0.4)] transition-all duration-200 active:scale-[0.98]">
            Calculate GST
        </button>

      </div>

    </div>
  );
}