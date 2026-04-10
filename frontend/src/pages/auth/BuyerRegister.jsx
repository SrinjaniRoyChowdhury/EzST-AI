import { useNavigate } from "react-router-dom";
import bgImage from "../../assets/background.jpeg";

export default function BuyerRegister() {
  const navigate = useNavigate();

  return (
    <div className="w-full min-h-screen bg-white flex flex-col items-center font-sans">
      
      {/* Hero Section */}
      <div 
        className="w-full flex flex-col items-center pt-32 sm:pt-40 pb-48 sm:pb-[16rem] relative bg-cover bg-center"
        style={{ backgroundImage: `url(${bgImage})` }}
      >
        <div className="absolute inset-0 bg-black/50"></div> 
        <div className="relative z-10 flex flex-col items-center gap-4 text-center px-4 w-full max-w-4xl">
          <h1 className="text-white text-5xl md:text-[4rem] font-bold font-inter tracking-tight drop-shadow-[0_4px_4px_rgba(0,0,0,0.5)]">
            Join as Buyer
          </h1>
          <p className="text-white/90 text-lg md:text-xl font-medium max-w-lg leading-relaxed drop-shadow-[0_4px_4px_rgba(0,0,0,0.5)]">
            Create an account to manage, review, and process your received invoices.
          </p>
        </div>
      </div>

      {/* Form Card */}
      <div className="w-full max-w-md px-4 relative z-20 -mt-32 md:-mt-48 mb-20 flex flex-col">
        <div className="bg-white rounded-3xl shadow-[0_10px_40px_rgba(0,0,0,0.15)] p-8 md:p-10 border border-gray-100 flex flex-col gap-6">
           
           <div className="text-center">
             <h2 className="text-[#D50000] text-3xl font-extrabold mb-1 tracking-tight">Sign Up</h2>
             <p className="text-gray-500 font-medium tracking-wide">BUYER PORTAL</p>
           </div>

           <div className="flex flex-col gap-4">
             <div className="flex flex-col gap-1.5">
                <label className="text-black font-bold ml-1 text-sm">Full Name</label>
                <input 
                  type="text" 
                  placeholder="John Doe" 
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:border-[#D50000] focus:ring-1 focus:ring-[#D50000] transition-colors shadow-sm font-medium"
                />
             </div>
             <div className="flex flex-col gap-1.5">
                <label className="text-black font-bold ml-1 text-sm">Email Address</label>
                <input 
                  type="email" 
                  placeholder="name@company.com" 
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:border-[#D50000] focus:ring-1 focus:ring-[#D50000] transition-colors shadow-sm font-medium"
                />
             </div>
             <div className="flex flex-col gap-1.5">
                <label className="text-black font-bold ml-1 text-sm">Password</label>
                <input 
                  type="password" 
                  placeholder="••••••••" 
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:border-[#D50000] focus:ring-1 focus:ring-[#D50000] transition-colors shadow-sm font-medium"
                />
             </div>
           </div>

           <button 
              onClick={() => navigate('/auth/buyer-signin')}
              className="w-full bg-[#D50000] text-white py-4 rounded-xl font-extrabold text-xl shadow-[0_4px_15px_rgba(213,0,0,0.3)] hover:bg-[#b00116] hover:shadow-[0_6px_20px_rgba(213,0,0,0.4)] transition-all duration-200 active:scale-[0.98] mt-2"
           >
              Create Account
           </button>

           <div className="text-center text-sm font-medium mt-2">
             <span className="text-gray-500">Already have an account? </span>
             <button onClick={() => navigate('/auth/buyer-signin')} className="text-[#D50000] hover:underline font-bold">Sign In directly</button>
           </div>
           
           <div className="border-t border-gray-100 pt-6 mt-2 text-center flex justify-center">
             <button 
                onClick={() => navigate('/auth/seller-register')} 
                className="text-gray-400 hover:text-gray-700 font-semibold text-xs flex items-center transition-colors"
              >
                Switch to Seller Sign Up &rarr;
             </button>
           </div>
        </div>
      </div>

    </div>
  );
}
