import { useNavigate } from "react-router-dom";
import bgImage from "../../assets/background.jpeg";

export default function Register() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-[#f87883] via-[#ffb9bf] to-[#fce4e6] p-4 font-sans py-10">
      
      {/* Top Header */}
      <div className="text-center mb-6 text-white">
        <h1 className="text-2xl font-bold tracking-wide mb-1 drop-shadow-md">EzST-AI Registration</h1>
        <p className="text-sm font-medium drop-shadow-md">New Member Signup</p>
      </div>

      {/* Main Card */}
      <div className="bg-white p-6 sm:p-8 rounded-[1rem] shadow-2xl max-w-2xl w-full mb-6">
        
        {/* Card Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-8 pb-6 border-b border-gray-200 gap-4 sm:gap-0">
           <div>
             <div className="text-5xl font-black tracking-tighter text-black flex items-end">
               EzST<span className="text-[#d0021b] text-2xl mb-1 ml-1 transform -rotate-90 origin-bottom-left block font-bold leading-none">AI</span>
             </div>
             <p className="text-[10px] uppercase font-bold text-gray-500 tracking-widest mt-1">Building Digital Solutions</p>
           </div>
           <h2 className="text-4xl font-bold tracking-tight text-black sm:mt-2">Register</h2>
        </div>
        
        {/* User Info */}
        <div className="flex flex-col sm:flex-row justify-between sm:items-end mb-6 text-sm gap-4 sm:gap-0">
          <div className="text-gray-700 space-y-1">
            <p className="font-bold text-gray-900 mb-1 sm:mb-2 text-base">Registration Details:</p>
            <p><span className="font-semibold text-gray-800">Type:</span> New Account</p>
            <p><span className="font-semibold text-gray-800">Company:</span> Independent</p>
            <p><span className="font-semibold text-gray-800">Platform:</span> EzST-AI Portal</p>
          </div>
          <div className="text-left sm:text-right text-gray-800 space-y-1">
             <p className="font-bold text-base">Form No. {Math.floor(Math.random() * 1000) + 1000}</p>
             <p className="font-medium">Date: {new Date().toLocaleDateString('en-GB')}</p>
          </div>
        </div>

        {/* Form area mimicking the Invoice breakdown */}
        <div className="border-[2px] border-[#d0021b] rounded-[1.5rem] overflow-hidden flex flex-col">
            
            <div className="p-4 sm:p-6">
              <div className="flex items-center justify-between font-bold text-gray-900 border-b border-red-200 pb-3 mb-4">
                <span className="text-base sm:text-lg">Information required</span>
                <span className="text-base sm:text-lg">Input Data</span>
              </div>
              
              <div className="space-y-4 sm:space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 sm:gap-4">
                  <span className="font-semibold text-gray-800 text-sm sm:text-base">Full Name</span>
                  <input
                    type="text"
                    className="w-full sm:w-2/3 p-2 sm:text-right border-none focus:outline-none focus:ring-2 focus:ring-[#d0021b] rounded bg-gray-50 sm:bg-white text-gray-800 placeholder-gray-400 font-medium transition-shadow"
                    placeholder="Enter full name"
                  />
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 sm:gap-4">
                  <span className="font-semibold text-gray-800 text-sm sm:text-base">Email Address</span>
                  <input
                    type="email"
                    className="w-full sm:w-2/3 p-2 sm:text-right border-none focus:outline-none focus:ring-2 focus:ring-[#d0021b] rounded bg-gray-50 sm:bg-white text-gray-800 placeholder-gray-400 font-medium transition-shadow"
                    placeholder="Enter email address"
                  />
                </div>

                 <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 sm:gap-4">
                  <span className="font-semibold text-gray-800 text-sm sm:text-base">Password</span>
                  <input
                    type="password"
                    className="w-full sm:w-2/3 p-2 sm:text-right border-none focus:outline-none focus:ring-2 focus:ring-[#d0021b] rounded bg-gray-50 sm:bg-white text-gray-800 placeholder-gray-400 font-medium transition-shadow"
                    placeholder="Choose password"
                  />
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 sm:gap-4">
                  <span className="font-semibold text-gray-800 text-sm sm:text-base">Select Role</span>
                  <select 
                    className="w-full sm:w-2/3 p-2 sm:text-right border border-gray-200 sm:border-none focus:outline-none focus:ring-2 focus:ring-[#d0021b] rounded bg-gray-50 sm:bg-white text-gray-800 font-medium appearance-none" 
                    defaultValue="" 
                    dir="ltr"
                  >
                    <option value="" disabled>Select role</option>
                    <option value="seller">Seller</option>
                    <option value="buyer">Buyer</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="bg-[#d0021b] text-white p-4 sm:p-5 font-bold flex flex-col sm:flex-row justify-between items-center text-base sm:text-lg">
               <span>Action Required:</span>
               <span>Create Profile</span>
            </div>
        </div>

      </div>

      <div className="flex flex-col sm:flex-row justify-center gap-3 w-full max-w-2xl px-2">
        <button className="flex-1 bg-[#d0021b] text-white py-3 rounded-lg font-bold shadow-lg hover:bg-[#b00116] transition-colors text-base sm:text-lg">
          Complete
        </button>
        <button 
          onClick={() => navigate('/auth/login')}
          className="flex-1 bg-white text-[#d0021b] py-3 rounded-lg font-bold shadow-lg hover:bg-gray-50 transition-colors text-base sm:text-lg border border-transparent"
        >
          Cancel
        </button>
        <button 
          onClick={() => navigate('/buyer')}
          className="flex-1 bg-white text-[#d0021b] py-3 rounded-lg font-bold hover:bg-red-50 transition-colors text-base sm:text-lg border border-[rgba(208,2,27,0.3)] shadow-[0_4px_10px_rgba(208,2,27,0.15)]"
        >
          Buyer Demo
        </button>
      </div>

    </div>
  );
}
