import { useState } from "react";
import { useNavigate } from "react-router-dom";
import bgImage from "../../assets/background.jpeg";

export default function Chatbot() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    // Add user message
    const newMessages = [...messages, { role: "user", text: query }];
    setMessages(newMessages);
    setQuery("");

    // Simulate bot response
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: "I'm currently a mock assistant! LLM integration is coming soon. Let me know if you need help navigating your invoices." }
      ]);
    }, 1000);
  };

  return (
    <div className="w-full min-h-screen bg-gray-50 font-sans flex flex-col items-center">
      
      {/* Search & Hero Section */}
      <div 
        className="w-full flex flex-col items-center pt-24 pb-16 px-4 relative bg-cover bg-center"
        style={{ backgroundImage: `url(${bgImage})` }}
      >
        <div className="absolute inset-0 bg-black/30 pointer-events-none"></div>

        <div className="relative z-10 w-full max-w-4xl flex flex-col items-center gap-8 mt-8">
           <h1 className="text-white text-5xl md:text-[4rem] font-bold font-inter tracking-tight text-center drop-shadow-[0_4px_4px_rgba(0,0,0,0.5)] leading-tight">
             Hi, How Can I Help You
           </h1>
           
           {/* Search Bar */}
           <form onSubmit={handleSearch} className="w-full max-w-2xl bg-white rounded-2xl shadow-[0_10px_35px_rgba(0,0,0,0.15)] overflow-hidden flex items-center border-[4px] border-[#D50000]">
             <input 
               type="text" 
               value={query}
               onChange={(e) => setQuery(e.target.value)}
               placeholder="Ask me anything about your invoices..." 
               className="flex-1 w-full px-6 py-4 outline-none text-[#D50000] text-xl font-medium placeholder-[#D50000]/50"
             />
             <button type="submit" className="bg-transparent hover:bg-red-50 p-4 transition-colors flex items-center justify-center shrink-0 border-l-[3px] border-[#D50000]/20">
               <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-[#D50000]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
               </svg>
             </button>
           </form>
        </div>
      </div>

      {/* Chat Area */}
      <div className="w-full max-w-4xl px-4 py-8 flex flex-col gap-4 flex-1">
         {messages.length === 0 ? (
            <div className="text-center text-gray-400 mt-10">
               <p className="font-bold text-xl mb-2">Try asking:</p>
               <div className="flex gap-2 justify-center flex-wrap">
                  <span className="bg-white border rounded-full px-4 py-1 text-sm shadow inline-block">Are there any overdue invoices?</span>
                  <span className="bg-white border rounded-full px-4 py-1 text-sm shadow inline-block">Calculate my GST for April</span>
               </div>
            </div>
         ) : (
            messages.map((msg, idx) => (
               <div key={idx} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[75%] rounded-2xl p-4 shadow-sm text-lg ${msg.role === 'user' ? 'bg-[#D50000] text-white rounded-br-sm' : 'bg-white text-gray-800 border border-gray-200 rounded-bl-sm'}`}>
                     {msg.text}
                  </div>
               </div>
            ))
         )}
      </div>

      <div className="w-full h-24"></div> {/* Spacer */}

    </div>
  );
}
