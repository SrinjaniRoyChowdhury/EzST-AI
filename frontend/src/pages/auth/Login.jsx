import { useNavigate } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();

  return (
    <div className="h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-6 rounded-xl shadow-md w-80">
        <h2 className="text-xl font-bold mb-4 text-center">Login</h2>

        <input
          type="text"
          placeholder="Username"
          className="w-full mb-3 p-2 border rounded"
        />

        <input
          type="password"
          placeholder="Password"
          className="w-full mb-4 p-2 border rounded"
        />

        <div className="flex justify-between">
          <button
            onClick={() => navigate("/seller")}
            className="bg-blue-500 text-white px-3 py-2 rounded"
          >
            Login as Seller
          </button>

          <button
            onClick={() => navigate("/buyer")}
            className="bg-green-500 text-white px-3 py-2 rounded"
          >
            Login as Buyer
          </button>
        </div>
      </div>
    </div>
  );
}