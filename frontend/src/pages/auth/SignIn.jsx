import { useNavigate } from "react-router-dom";

export default function SignIn() {
  const navigate = useNavigate();

  return (
    <div 
      className="w-full min-h-screen flex flex-col items-center font-sans relative bg-gradient-to-br from-[#ffe4e6] via-[#fecdd3] to-[#ffe4e6]"
    >

      {/* Main Content Wrapper - Provides centering and spacing */}
      <div className="relative z-10 flex flex-col items-center w-full pt-24 pb-20 px-4">
          
          {/* Header Text */}
          <div className="flex flex-col items-center gap-4 text-center w-full max-w-4xl mb-12">
            <h1 className="text-[#D50000] text-5xl md:text-[4rem] font-bold font-inter tracking-tight drop-shadow-sm">
              Hello, Buyer
            </h1>
            <p className="text-[#D50000]/80 text-lg md:text-xl font-medium max-w-lg leading-relaxed">
              Sign In to your account, to access your Invoices.
            </p>
          </div>

          {/* Login Form Card centered below the text */}
          <div className="w-full max-w-md flex flex-col">
            <div className="bg-white rounded-3xl shadow-[0_10px_40px_rgba(0,0,0,0.2)] p-8 md:p-10 border border-gray-100 flex flex-col gap-8">
               
               <div className="text-center">
                 <h2 className="text-[#D50000] text-3xl font-extrabold mb-1 tracking-tight">Sign In</h2>
                 <p className="text-gray-500 font-medium tracking-wide">BUYER PORTAL</p>
               </div>

               {/* Form Inputs */}
               <div className="flex flex-col gap-5">
                 <div className="flex flex-col gap-1.5">
                    <label className="text-black font-bold ml-1 text-sm">Email Address</label>
                    <input 
                      type="email" 
                      placeholder="name@company.com" 
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:border-[#D50000] focus:ring-1 focus:ring-[#D50000] transition-colors shadow-sm font-medium"
                    />
                 </div>
                 <div className="flex flex-col gap-1.5 flex-1">
                    <div className="flex justify-between items-center ml-1">
                      <label className="text-black font-bold text-sm">Password</label>
                      <a href="#" className="text-xs text-[#D50000] font-bold hover:underline">Forgot?</a>
                    </div>
                    <input 
                      type="password" 
                      placeholder="••••••••" 
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:border-[#D50000] focus:ring-1 focus:ring-[#D50000] transition-colors shadow-sm font-medium"
                    />
                 </div>
               </div>

               {/* Submit Button */}
               <button 
                  onClick={() => navigate('/buyer')}
                  className="w-full bg-[#D50000] text-white py-4 rounded-xl font-extrabold text-xl shadow-[0_4px_15px_rgba(213,0,0,0.3)] hover:bg-[#b00116] hover:shadow-[0_6px_20px_rgba(213,0,0,0.4)] transition-all duration-200 active:scale-[0.98]"
               >
                  Sign In Securely
               </button>

               <div className="text-center text-sm font-medium mt-2">
                 <span className="text-gray-500">Don't have an account? </span>
                 <button onClick={() => navigate('/auth/buyer-register')} className="text-[#D50000] hover:underline font-bold">Register as Buyer</button>
               </div>
               
               {/* Link to Seller SignIn to switch contexts easily */}
               <div className="border-t border-gray-100 pt-6 mt-2 text-center flex justify-center">
                 <button 
                    onClick={() => navigate('/auth/seller-signin')} 
                    className="text-gray-400 hover:text-gray-700 font-semibold text-xs flex items-center transition-colors"
                  >
                    Switch to Seller Sign In &rarr;
                 </button>
               </div>
            </div>
          </div>

      </div>
    </div>
  );
}
