import { useNavigate } from "react-router-dom";
import bgImage from "../../assets/background.jpeg";

export default function SellerLogin() {
  const navigate = useNavigate();

  return (
    <div 
      className="w-full min-h-screen flex flex-col items-center font-sans relative bg-cover bg-center"
      style={{ backgroundImage: `url(${bgImage})` }}
    >
      <div className="absolute inset-0 bg-black/10 pointer-events-none"></div> 

      <div className="relative z-10 flex flex-col items-center w-full pt-24 pb-20 px-4">
          
          <div className="flex flex-col items-center gap-4 text-center w-full max-w-4xl mb-12">
            <h1 className="text-white text-5xl md:text-[4rem] font-bold font-inter tracking-tight drop-shadow-md">
              Hello, Seller
            </h1>
            <p className="text-white/90 text-lg md:text-xl font-medium max-w-lg leading-relaxed drop-shadow-sm">
              Sign In to your account, to manage your Uploaded Invoices.
            </p>
          </div>

          <div className="w-full max-w-md flex flex-col">
            <div className="bg-white rounded-3xl shadow-[0_10px_40px_rgba(0,0,0,0.15)] p-8 md:p-10 border-[2px] border-[#D50000] flex flex-col gap-8">
               
               <div className="text-center">
                 <h2 className="text-[#D50000] text-3xl font-extrabold mb-1 tracking-tight">Sign In</h2>
                 <p className="text-[#D50000]/70 font-bold tracking-wide">SELLER PORTAL</p>
               </div>

               <div className="flex flex-col gap-5">
                 <div className="flex flex-col gap-1.5">
                    <label className="text-gray-900 font-bold ml-1 text-sm">Business Email</label>
                    <input 
                      type="email" 
                      placeholder="seller@domain.com" 
                      className="w-full px-4 py-3 bg-white border border-red-100 rounded-xl focus:outline-none focus:border-[#D50000] focus:ring-1 focus:ring-[#D50000] transition-colors shadow-sm font-medium"
                    />
                 </div>
                 <div className="flex flex-col gap-1.5 flex-1">
                    <div className="flex justify-between items-center ml-1">
                      <label className="text-gray-900 font-bold text-sm">Password</label>
                      <a href="#" className="text-xs text-[#D50000] font-bold hover:underline">Forgot?</a>
                    </div>
                    <input 
                      type="password" 
                      placeholder="••••••••" 
                      className="w-full px-4 py-3 bg-white border border-red-100 rounded-xl focus:outline-none focus:border-[#D50000] focus:ring-1 focus:ring-[#D50000] transition-colors shadow-sm font-medium"
                    />
                 </div>
               </div>

               <button 
                  onClick={() => navigate('/seller')}
                  className="w-full bg-[#D50000] text-white py-4 rounded-xl font-extrabold text-xl shadow-[0_4px_15px_rgba(213,0,0,0.3)] hover:bg-[#b00116] hover:shadow-[0_6px_20px_rgba(213,0,0,0.4)] transition-all duration-200 active:scale-[0.98]"
               >
                  Access Dashboard
               </button>

               <div className="text-center text-sm font-medium mt-2">
                 <span className="text-gray-500">New to EzST? </span>
                 <button onClick={() => navigate('/auth/seller-register')} className="text-[#D50000] hover:underline font-bold">Register as Seller</button>
               </div>
               
               <div className="border-t border-gray-100 pt-6 mt-2 text-center flex justify-center">
                 <button 
                    onClick={() => navigate('/auth/buyer-signin')} 
                    className="text-gray-400 hover:text-[#D50000] font-semibold text-xs flex items-center transition-colors"
                  >
                    &larr; Switch to Buyer Sign In
                 </button>
               </div>
            </div>
          </div>
      </div>
    </div>
  );
}
