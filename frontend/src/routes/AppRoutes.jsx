import { BrowserRouter, Routes, Route } from "react-router-dom";

import Login from "../pages/auth/Login";
import Register from "../pages/auth/Register";

import SellerDashboard from "../pages/seller/SellerDashboard";
import CreateInvoice from "../pages/seller/UploadInvoice";
import SentInvoices from "../pages/seller/SentInvoices";

import BuyerDashboard from "../pages/buyer/BuyerDashboard";
import ReceivedInvoices from "../pages/buyer/ReceivedInvoices";
import InvoiceDetails from "../pages/buyer/InvoiceDetails";

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>

        {/* Auth Routes */}
        <Route path="/auth/login" element={<Login />} />
        <Route path="/auth/register" element={<Register />} />

        {/* Seller Routes */}
        <Route path="/seller" element={<SellerDashboard />} />
        <Route path="/seller/create" element={<CreateInvoice />} />
        <Route path="/seller/invoices" element={<SentInvoices />} />

        {/* Buyer Routes */}
        <Route path="/buyer" element={<BuyerDashboard />} />
        <Route path="/buyer/invoices" element={<ReceivedInvoices />} />
        <Route path="/buyer/invoice/:id" element={<InvoiceDetails />} />

      </Routes>
    </BrowserRouter>
  );
}