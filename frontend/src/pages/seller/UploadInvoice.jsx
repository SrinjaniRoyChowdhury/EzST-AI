export default function UploadInvoice() {
  return (
    <div className="w-full min-h-screen relative bg-white flex flex-col items-center justify-center font-sans overflow-hidden">
      
      {/* Background Image Container mapped to 1346x782 placement */}
      <div 
         className="absolute inset-0 z-0 bg-cover bg-center"
         style={{ backgroundImage: 'url(https://placehold.co/1920x1080/f8f8f8/e5e5e5)' }}
      ></div>

      {/* Floating Upload Widget - Box mapped to 508x330 measurements */}
      <div className="relative z-10 w-full max-w-[540px] min-h-[350px] mx-4 bg-white rounded-[2rem] border-[2px] border-[#D50000] shadow-[0_10px_35px_rgba(0,0,0,0.1),0_0_15px_rgba(0,0,0,0.06)] flex flex-col items-center justify-center p-8 md:p-12 gap-10 mt-16 group hover:shadow-[0_15px_45px_rgba(0,0,0,0.12)] transition-shadow duration-300">
         
         <div className="flex flex-col items-center justify-center gap-4 opacity-70 group-hover:opacity-100 transition-opacity duration-300 transform -translate-y-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-20 w-20 text-[#D50000]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="text-[#D50000] font-bold text-xl tracking-wide">Select your document source</p>
         </div>

         {/* Action Buttons mapped from absolute positions */}
         <div className="w-full flex justify-center items-center gap-4 flex-wrap">
            <button 
               className="flex-1 min-w-[210px] bg-[#D50000] text-white py-[14px] px-4 rounded-xl font-extrabold text-[1.15rem] shadow-[0_4px_10px_rgba(213,0,0,0.15)] hover:bg-[#b00116] hover:shadow-[0_6px_15px_rgba(213,0,0,0.25)] transition-all duration-200 active:scale-[0.98] flex justify-center items-center"
            >
               Upload From Device
            </button>
            <button 
               className="flex-1 min-w-[210px] bg-transparent text-[#D50000] py-[14px] px-4 rounded-xl font-extrabold text-[1.15rem] border-[2px] border-[#D50000] hover:bg-[#D50000]/5 hover:shadow-[0_4px_10px_rgba(0,0,0,0.05)] transition-all duration-200 active:scale-[0.98] flex justify-center items-center"
            >
               Upload From Drive
            </button>
         </div>
      </div>

    </div>
  );
}