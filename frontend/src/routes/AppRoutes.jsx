import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import SignIn from "../pages/auth/SignIn";
import BuyerRegister from "../pages/auth/BuyerRegister";
import SellerRegister from "../pages/auth/SellerRegister";
import SellerLogin from "../pages/auth/SellerLogin";

import SellerLayout from "../pages/seller/SellerLayout";
import SellerDashboard from "../pages/seller/SellerDashboard";
import UploadInvoice from "../pages/seller/UploadInvoice";
import SentInvoices from "../pages/seller/SentInvoices";

import BuyerLayout from "../pages/buyer/BuyerLayout";
import BuyerDashboard from "../pages/buyer/BuyerDashboard";
import ReceivedInvoices from "../pages/buyer/ReceivedInvoices";
import InvoiceDetails from "../pages/buyer/InvoiceDetails";
import CheckYourInvoice from "../pages/buyer/CheckYourInvoice";
import SocialMediaInvoice from "../pages/buyer/SocialMediaInvoice";
import Chatbot from "../pages/buyer/Chatbot";

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>

        {/* Default Route */}
        <Route path="/" element={<Navigate to="/auth/buyer-signin" />} />

        {/* Auth */}
        <Route path="/auth/login" element={<Navigate to="/auth/buyer-signin" />} />
        <Route path="/auth/buyer-login" element={<Navigate to="/auth/buyer-signin" />} />
        <Route path="/auth/seller-login" element={<Navigate to="/auth/seller-signin" />} />
        
        <Route path="/auth/buyer-signin" element={<SignIn />} />
        <Route path="/auth/seller-signin" element={<SellerLogin />} />
        
        <Route path="/auth/buyer-register" element={<BuyerRegister />} />
        <Route path="/auth/seller-register" element={<SellerRegister />} />

        {/* Seller */}
        <Route element={<SellerLayout />}>
           <Route path="/seller" element={<SellerDashboard />} />
           <Route path="/seller/upload" element={<UploadInvoice />} />
           <Route path="/seller/invoices" element={<SentInvoices />} />
        </Route>

        {/* Buyer */}
        <Route element={<BuyerLayout />}>
           <Route path="/buyer" element={<BuyerDashboard />} />
           <Route path="/buyer/invoices" element={<ReceivedInvoices />} />
           <Route path="/buyer/invoice/:id" element={<InvoiceDetails />} />
           <Route path="/buyer/check-your-invoice" element={<CheckYourInvoice />} />
           <Route path="/buyer/social-media-invoice" element={<SocialMediaInvoice />} />
           <Route path="/buyer/chatbot" element={<Chatbot />} />
        </Route>
        <Route path="/buyer/socila-media-invoice" element={<Navigate to="/buyer/social-media-invoice" replace />} />

      </Routes>
    </BrowserRouter>
  );
}