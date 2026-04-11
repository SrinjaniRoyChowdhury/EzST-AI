import { useNavigate } from "react-router-dom";
import bgImage from "../../assets/background.jpeg";
import Epsilon from "../../assets/EpsilonInvoice.png";

export default function SocialMediaInvoice() {
  const navigate = useNavigate();

  return (
    <div className="w-full min-h-screen bg-white flex flex-col font-sans overflow-x-hidden">
      
      {/* Top Banner */}
      <div className="w-full bg-[#f38e96] relative flex flex-col justify-center items-center py-12 md:py-16 px-4 shadow-sm z-10">
         <div className="md:absolute md:top-8 md:right-12 text-white text-lg font-semibold drop-shadow-md mb-4 md:mb-0">
            January 1, 2025
         </div>
         <h1 className="text-white text-4xl md:text-[3.25rem] font-extrabold tracking-tight drop-shadow-lg text-center leading-tight">
            Social Media Invoice
         </h1>
      </div>

      {/* Main Content Area */}
      <div 
        className="flex-1 w-full flex flex-col items-center py-12 md:py-20 px-4 md:px-8 bg-cover bg-center relative"
        style={{ backgroundImage: `url(${bgImage})` }}
      >
        {/* Subtle grid or overlay if needed */}
        <div className="absolute inset-0 bg-white/40 pointer-events-none"></div>

        {/* Invoice Document Viewer Placeholder */}
        <div className="relative z-10 w-full max-w-5xl rounded-3xl shadow-[0_10px_35px_rgba(0,0,0,0.15)] overflow-hidden bg-white mb-16 border border-gray-100">
          <img 
            src={Epsilon} 
            alt="Social Media Invoice Document" 
            className="w-full h-auto object-cover" 
          />
        </div>

        {/* Action Buttons */}
        <div className="relative z-10 flex flex-col lg:flex-row flex-wrap justify-center items-center gap-6 w-full max-w-5xl px-2">
           <button className="w-full lg:w-auto flex-[1.2] min-w-[200px] bg-[#D50000] text-white py-4 md:py-5 rounded-2xl text-2xl md:text-[1.8rem] font-extrabold shadow-[0_6px_15px_rgba(0,0,0,0.2)] hover:bg-[#b80000] hover:shadow-[0_8px_20px_rgba(0,0,0,0.25)] transition-all duration-200 active:scale-95 flex items-center justify-center">
             Accept
           </button>
           
           <button className="w-full lg:w-auto flex-1 min-w-[200px] bg-white text-[#D50000] py-4 md:py-5 rounded-2xl text-2xl md:text-[1.8rem] font-extrabold shadow-[0_6px_15px_rgba(0,0,0,0.15)] hover:bg-red-50 hover:shadow-[0_8px_20px_rgba(0,0,0,0.2)] transition-all duration-200 active:scale-95 flex items-center justify-center">
             Reject
           </button>
           
           <button className="w-full lg:w-auto flex-[1.5] min-w-[280px] bg-transparent text-[#D50000] py-4 md:py-5 rounded-2xl text-2xl md:text-[1.8rem] font-extrabold border-[3px] border-[#D50000] shadow-sm hover:bg-[#D50000]/5 hover:shadow-md transition-all duration-200 active:scale-95 flex items-center justify-center">
             Request Modification
           </button>
        </div>
      </div>
    
    </div>
  );
}
