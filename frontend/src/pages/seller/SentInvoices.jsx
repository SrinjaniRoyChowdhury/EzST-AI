import { useNavigate } from "react-router-dom";

export default function SentInvoices() {
  const navigate = useNavigate();

  return (
    <div className="w-full min-h-screen bg-gray-50 flex flex-col items-center font-sans tracking-tight">
      
      {/* 1. Header Section */}
      <div className="w-full bg-[#F38E96] pt-32 pb-40 px-6 flex flex-col items-center justify-center gap-6 shadow-sm relative z-10 text-center">
        <div className="text-white text-lg font-medium tracking-wide drop-shadow-md opacity-90">
          January 1, 2025
        </div>
        <h1 className="text-white text-4xl md:text-5xl lg:text-[3.5rem] font-bold font-inter drop-shadow-lg leading-tight max-w-4xl">
          Social Media Invoice
        </h1>
      </div>

      {/* 2. Main Content Wrapper */}
      <div 
        className="w-full flex justify-center pt-8 pb-32 px-4 sm:px-8 md:px-16 -mt-24 relative z-20"
      >
        <div className="flex flex-col items-center w-full max-w-[1101px] gap-16">
            
            {/* Invoice Document Placeholder */}
            <div className="w-full bg-white rounded-3xl shadow-[0_10px_40px_rgba(0,0,0,0.15)] overflow-hidden border border-gray-100 aspect-[1101/1059]">
               <img src="https://placehold.co/1101x1059/fafafa/e5e5e5?text=Invoice+Preview" alt="Invoice Document" className="w-full h-full object-contain p-2"/>
            </div>

            {/* Action Buttons styled according to requirements */}
            <div className="flex flex-col md:flex-row items-center justify-center gap-6 w-full">
               <button 
                 className="w-full md:w-auto min-w-[280px] bg-white text-[#D50000] py-5 px-8 rounded-xl font-extrabold text-2xl md:text-[1.8rem] shadow-[0_6px_15px_rgba(0,0,0,0.08)] hover:shadow-[0_8px_20px_rgba(0,0,0,0.12)] transition-all duration-200 active:scale-[0.98] border border-gray-100 text-center"
               >
                 Calculate GST
               </button>
               <button 
                 className="w-full md:w-auto min-w-[280px] bg-transparent text-[#D50000] py-5 px-8 flex-1 max-w-[500px] rounded-xl font-extrabold text-2xl md:text-[1.8rem] border-[3px] border-[#D50000] shadow-sm hover:bg-[#D50000]/5 transition-all duration-200 active:scale-[0.98] text-center"
               >
                 Check Modification Request
               </button>
            </div>
            
        </div>
      </div>
      
    </div>
  );
}