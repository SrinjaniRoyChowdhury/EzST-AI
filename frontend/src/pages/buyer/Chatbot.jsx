import { useState } from "react";
import { useNavigate } from "react-router-dom";
import bgImage from "../../assets/background.jpeg";

export default function Chatbot() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    const userMessage = query;
    setMessages((prev) => [...prev, { role: "user", text: userMessage }]);
    setQuery("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/gst/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMessage, session_id: "buyer-chatbot" }),
      });

      if (!response.ok) throw new Error("API error");
      const data = await response.json();

      setMessages((prev) => [...prev, { role: "bot", text: data.answer }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: "Sorry, I couldn't reach the server. Please make sure the backend is running." },
      ]);
    } finally {
      setIsLoading(false);
    }
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
               placeholder="Ask about invoices, GST, payments..."
               disabled={isLoading}
               className="flex-1 w-full px-6 py-4 outline-none text-[#D50000] text-xl font-medium placeholder-[#D50000]/50 disabled:opacity-60"
             />
             <button type="submit" disabled={isLoading} className="bg-transparent hover:bg-red-50 p-4 transition-colors flex items-center justify-center shrink-0 border-l-[3px] border-[#D50000]/20 disabled:opacity-50">
               {isLoading ? (
                 <div className="h-8 w-8 border-4 border-[#D50000]/30 border-t-[#D50000] rounded-full animate-spin" />
               ) : (
                 <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-[#D50000]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                 </svg>
               )}
             </button>
           </form>
        </div>
      </div>

      {/* Chat Area */}
      <div className="w-full max-w-4xl px-4 py-8 flex flex-col gap-4 flex-1">
         {messages.length === 0 && !isLoading ? (
            <div className="text-center text-gray-400 mt-10">
               <p className="font-bold text-xl mb-4">Try asking:</p>
               <div className="flex gap-2 justify-center flex-wrap">
                  {[
                    "Which invoice has the highest amount?",
                    "What is the status of INV-2026-001?",
                    "Show me all pending invoices",
                    "What is the total value of all invoices?",
                  ].map((s) => (
                    <button key={s} onClick={() => setQuery(s)} className="bg-white border border-gray-200 rounded-full px-4 py-2 text-sm shadow hover:border-[#D50000] hover:text-[#D50000] transition-colors font-medium">
                      {s}
                    </button>
                  ))}
               </div>
            </div>
         ) : (
            <>
              {messages.map((msg, idx) => (
                 <div key={idx} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[75%] rounded-2xl p-4 shadow-sm text-base leading-relaxed whitespace-pre-wrap ${msg.role === 'user' ? 'bg-[#D50000] text-white rounded-br-sm' : 'bg-white text-gray-800 border border-gray-200 rounded-bl-sm'}`}>
                       {msg.text}
                    </div>
                 </div>
              ))}
              {isLoading && (
                 <div className="flex justify-start">
                    <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-5 py-4 shadow-sm flex gap-1 items-center">
                       <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}} />
                       <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}} />
                       <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}} />
                    </div>
                 </div>
              )}
            </>
         )}
      </div>

      <div className="w-full h-24"></div> {/* Spacer */}

    </div>
  );
}
