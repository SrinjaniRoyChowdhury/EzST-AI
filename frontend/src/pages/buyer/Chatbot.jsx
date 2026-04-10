import { useNavigate } from "react-router-dom";
import bgImage from "../../assets/background.jpeg";

export default function Chatbot() {
  const navigate = useNavigate();

  return (
    <div className="w-full min-h-screen bg-white font-sans flex flex-col items-center">
      
      {/* Search & Hero Section */}
      <div 
        className="w-full flex flex-col items-center pt-24 pb-24 md:pt-32 md:pb-32 px-4 relative bg-cover bg-center"
        style={{ backgroundImage: `url(${bgImage})` }}
      >
        {/* Dark overlay for contrast */}
        <div className="absolute inset-0 bg-black/20 pointer-events-none"></div>

        <div className="relative z-10 w-full max-w-4xl flex flex-col items-center gap-10 mt-8">
           <h1 className="text-white text-5xl md:text-[4rem] font-bold font-inter tracking-tight text-center drop-shadow-[0_4px_4px_rgba(0,0,0,0.5)] leading-tight">
             Hi, How Can I Help You
           </h1>
           
           {/* Search Bar */}
           <div className="w-full max-w-2xl bg-white rounded-2xl shadow-[0_10px_35px_rgba(0,0,0,0.15)] overflow-hidden flex items-center border-[4px] border-[#D50000]">
             <input 
               type="text" 
               placeholder="Search..." 
               className="flex-1 w-full px-6 py-4 outline-none text-[#D50000] text-xl font-medium placeholder-[#D50000]/50"
             />
             <button className="bg-transparent hover:bg-red-50 p-4 transition-colors flex items-center justify-center shrink-0 border-l-[3px] border-[#D50000]/20">
               <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-[#D50000]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
               </svg>
             </button>
           </div>
        </div>
      </div>

      {/* Quick Action Cards Grid (Mapped from design coordinates) */}
      <div className="w-full max-w-7xl px-6 lg:px-8 py-20 -mt-24 md:-mt-16 z-20 relative">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8">
           
           {/* Action 1 */}
           <div className="group cursor-pointer rounded-2xl overflow-hidden relative shadow-[0_5px_20px_rgba(0,0,0,0.1)] hover:shadow-[0_10px_30px_rgba(0,0,0,0.2)] transition-all duration-300 transform hover:-translate-y-2 aspect-[275/150] bg-black">
              <img src="https://placehold.co/275x150/111111/333333?text=+" className="absolute inset-0 w-full h-full object-cover opacity-80 group-hover:opacity-60 transition-opacity" alt="Validate Invoice bg" />
              <div className="absolute inset-0 flex items-center justify-center p-4">
                <h3 className="text-white text-2xl md:text-3xl font-bold font-inter text-center leading-tight drop-shadow-[0_4px_4px_rgba(0,0,0,0.5)]">
                  Validate<br/>Invoice
                </h3>
              </div>
           </div>

           {/* Action 2 */}
           <div className="group cursor-pointer rounded-2xl overflow-hidden relative shadow-[0_5px_20px_rgba(0,0,0,0.1)] hover:shadow-[0_10px_30px_rgba(0,0,0,0.2)] transition-all duration-300 transform hover:-translate-y-2 aspect-[275/150] bg-black">
              <img src="https://placehold.co/275x150/111111/333333?text=+" className="absolute inset-0 w-full h-full object-cover opacity-80 group-hover:opacity-60 transition-opacity" alt="Predict Cashflow bg" />
              <div className="absolute inset-0 flex items-center justify-center p-4">
                <h3 className="text-white text-2xl md:text-3xl font-bold font-inter text-center leading-tight drop-shadow-[0_4px_4px_rgba(0,0,0,0.5)]">
                  Predict<br/>Cashflow
                </h3>
              </div>
           </div>

           {/* Action 3 */}
           <div className="group cursor-pointer rounded-2xl overflow-hidden relative shadow-[0_5px_20px_rgba(0,0,0,0.1)] hover:shadow-[0_10px_30px_rgba(0,0,0,0.2)] transition-all duration-300 transform hover:-translate-y-2 aspect-[275/150] bg-black">
              <img src="https://placehold.co/275x150/111111/333333?text=+" className="absolute inset-0 w-full h-full object-cover opacity-80 group-hover:opacity-60 transition-opacity" alt="Calculate GST bg" />
              <div className="absolute inset-0 flex items-center justify-center p-4">
                <h3 className="text-white text-2xl md:text-3xl font-bold font-inter text-center leading-tight drop-shadow-[0_4px_4px_rgba(0,0,0,0.5)]">
                  Calculate<br/>My GST
                </h3>
              </div>
           </div>

           {/* Action 4 */}
           <div className="group cursor-pointer rounded-2xl overflow-hidden relative shadow-[0_5px_20px_rgba(0,0,0,0.1)] hover:shadow-[0_10px_30px_rgba(0,0,0,0.2)] transition-all duration-300 transform hover:-translate-y-2 aspect-[275/150] bg-black">
              <img src="https://placehold.co/275x150/111111/333333?text=+" className="absolute inset-0 w-full h-full object-cover opacity-80 group-hover:opacity-60 transition-opacity" alt="Simplify Invoice bg" />
              <div className="absolute inset-0 flex items-center justify-center p-4">
                <h3 className="text-white text-2xl md:text-3xl font-bold font-inter text-center leading-tight drop-shadow-[0_4px_4px_rgba(0,0,0,0.5)]">
                  Simplify<br/>Invoice
                </h3>
              </div>
           </div>

        </div>
      </div>

    </div>
  );
}
