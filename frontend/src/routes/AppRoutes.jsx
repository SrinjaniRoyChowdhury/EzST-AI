import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Login from "../pages/auth/Login";
import SellerDashboard from "../pages/seller/SellerDashboard";
import UploadInvoice from "../pages/seller/UploadInvoice";
import SentInvoices from "../pages/seller/SentInvoices";

import BuyerDashboard from "../pages/buyer/BuyerDashboard";
import ReceivedInvoices from "../pages/buyer/ReceivedInvoices";
import InvoiceDetails from "../pages/buyer/InvoiceDetails";

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>

        {/* Default Route */}
        <Route path="/" element={<Navigate to="/auth/login" />} />

        {/* Auth */}
        <Route path="/auth/login" element={<Login />} />

        {/* Seller */}
        <Route path="/seller" element={<SellerDashboard />} />
        <Route path="/seller/upload" element={<UploadInvoice />} />
        <Route path="/seller/invoices" element={<SentInvoices />} />

        {/* Buyer */}
        <Route path="/buyer" element={<BuyerDashboard />} />
        <Route path="/buyer/invoices" element={<ReceivedInvoices />} />
        <Route path="/buyer/invoice/:id" element={<InvoiceDetails />} />

      </Routes>
    </BrowserRouter>
  );
}