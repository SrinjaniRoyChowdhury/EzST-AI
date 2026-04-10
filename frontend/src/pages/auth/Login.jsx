import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [isSignup, setIsSignup] = useState(false);
  const navigate = useNavigate();

  return (
    <div className="h-screen flex items-center justify-center bg-gray-100">
      
      <div className="bg-white p-8 rounded-2xl shadow-lg w-96">
        
        {/* Title */}
        <h2 className="text-2xl font-bold text-center mb-6">
          {isSignup ? "Create Account" : "Login"}
        </h2>

        {/* Form */}
        <div className="space-y-4">
          
          {isSignup && (
            <input
              type="text"
              placeholder="Full Name"
              className="w-full p-2 border rounded"
            />
          )}

          <input
            type="text"
            placeholder="Email"
            className="w-full p-2 border rounded"
          />

          <input
            type="password"
            placeholder="Password"
            className="w-full p-2 border rounded"
          />

          {isSignup && (
            <select className="w-full p-2 border rounded">
              <option value="">Select Role</option>
              <option value="buyer">Buyer</option>
              <option value="seller">Seller</option>
            </select>
          )}

          {/* Buttons */}
          <button
            className="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600"
          >
            {isSignup ? "Sign Up" : "Login"}
          </button>
        </div>

        {/* Quick Demo Login Buttons */}
        {!isSignup && (
          <div className="flex gap-3 mt-4">
            <button
              onClick={() => navigate("/seller")}
              className="w-1/2 bg-purple-500 text-white py-2 rounded"
            >
              Seller Demo
            </button>

            <button
              onClick={() => navigate("/buyer")}
              className="w-1/2 bg-green-500 text-white py-2 rounded"
            >
              Buyer Demo
            </button>
          </div>
        )}

        {/* Toggle */}
        <p className="text-sm text-center mt-6">
          {isSignup ? "Already have an account?" : "New user?"}
          <span
            onClick={() => setIsSignup(!isSignup)}
            className="text-blue-500 cursor-pointer ml-1"
          >
            {isSignup ? "Login" : "Sign up"}
          </span>
        </p>

      </div>
    </div>
  );
}

