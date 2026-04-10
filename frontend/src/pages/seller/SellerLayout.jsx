import { Outlet } from "react-router-dom";
import Navbar from "../../components/Navbar";

export default function SellerLayout() {
  const sellerLinks = [
    { label: "Dashboard", path: "/seller" },
    { label: "Upload Invoice", path: "/seller/upload" }
  ];

  return (
    <div className="w-full min-h-screen bg-gray-50 flex flex-col font-sans">
      <Navbar role="Seller Portal" links={sellerLinks} />
      {/* Content wrapper with top padding to account for fixed navbar */}
      <main className="w-full flex-1">
        <Outlet />
      </main>
    </div>
  );
}
