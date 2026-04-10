import { Outlet } from "react-router-dom";
import Navbar from "../../components/Navbar";

export default function BuyerLayout() {
  const buyerLinks = [
    { label: "Dashboard", path: "/buyer" },
    { label: "Your Invoice", path: "/buyer/check-your-invoice" }
  ];

  return (
    <div className="w-full min-h-screen bg-gray-50 flex flex-col font-sans">
      <Navbar role="Buyer Portal" links={buyerLinks} />
      {/* Content wrapper with top padding to account for fixed navbar */}
      <main className="w-full flex-1">
        <Outlet />
      </main>
    </div>
  );
}
