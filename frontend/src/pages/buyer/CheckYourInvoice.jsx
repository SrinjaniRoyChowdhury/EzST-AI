import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function CheckYourInvoice() {
  const navigate = useNavigate();
  // Using state to manage active tab for interactive feeling
  const [activeTab, setActiveTab] = useState("All");

  const tabs = ["All", "Pending", "Rejected", "Completed"];

  const invoices = [
    { title: "Social Media Invoice", date: "19/03/2025", img: "https://placehold.co/496x372", id: 1 },
    { title: "Google Ads Campaign Invoice", date: "09/04/2025", img: "https://placehold.co/496x372", id: 2 },
    { title: "Shoot Invoice", date: "29/04/2025", img: "https://placehold.co/496x372", id: 3 },
    { title: "Facebook Ads Campaign Invoice", date: "07/05/2025", img: "https://placehold.co/496x372", id: 4 },
    { title: "SEO Optimization Invoice", date: "02/07/2025", img: "https://placehold.co/496x372", id: 5 },
    { title: "Content Creation Invoice", date: "08/08/2025", img: "https://placehold.co/496x372", id: 6 },
  ];

  return (
    <div className="w-full min-h-screen bg-white font-sans flex flex-col">
      
      {/* Top Banner Section */}
      <div 
        className="relative w-full py-16 md:py-24 px-6 md:px-16 lg:px-32 bg-cover bg-center flex flex-col justify-end"
        style={{ backgroundImage: "url(https://placehold.co/1280x308/101010/333333)" }}
      >
        {/* Dark overlay to assure contrast with white texts */}
        <div className="absolute inset-0 bg-black/40"></div>

        <div className="relative z-10 w-full max-w-7xl mx-auto flex flex-col items-start gap-10 mt-6 lg:mt-12">
          <h1 className="text-white text-5xl md:text-[4rem] leading-none font-bold font-inter tracking-tight drop-shadow-[0_4px_4px_rgba(0,0,0,0.5)]">
            Your Invoices
          </h1>
          
          <div className="flex flex-wrap gap-4 md:gap-6 mt-4">
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
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-20">
            {invoices.map((inv) => (
              <div 
                key={inv.id} 
                className="flex flex-col gap-6 group cursor-pointer"
                onClick={() => navigate(`/buyer/invoice/${inv.id}`)} // Redirect to details if desired
              >
                <div className="w-full aspect-[4/3] rounded-2xl overflow-hidden shadow-[0_4px_10px_rgba(0,0,0,0.12)] group-hover:shadow-[0_8px_24px_rgba(0,0,0,0.18)] transition-all duration-300 relative border border-gray-100">
                  <img 
                    src={inv.img} 
                    alt={inv.title} 
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" 
                  />
                  {/* Subtle overlay effect on hover */}
                  <div className="absolute inset-0 bg-black/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </div>
                
                <div className="flex justify-between items-baseline px-2 gap-4">
                  <h3 className="text-black text-2xl font-bold font-inter leading-snug group-hover:text-[#D50000] transition-colors line-clamp-2">
                    {inv.title}
                  </h3>
                  <p className="text-black/55 text-lg font-medium whitespace-nowrap">
                    {inv.date}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      
    </div>
  );
}
