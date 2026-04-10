/**
 * src/routes/AppRoutes.jsx
 * Updated to use ProtectedRoute for all dashboard pages.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from '../components/ProtectedRoute';

import Login from '../pages/auth/Login';
import SellerDashboard from '../pages/seller/SellerDashboard';
import UploadInvoice from '../pages/seller/UploadInvoice';
import SentInvoices from '../pages/seller/SentInvoices';
import BuyerDashboard from '../pages/buyer/BuyerDashboard';
import ReceivedInvoices from '../pages/buyer/ReceivedInvoices';
import InvoiceDetails from '../pages/buyer/InvoiceDetails';

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>

        {/* Default */}
        <Route path="/" element={<Navigate to="/auth/login" />} />

        {/* Auth – public */}
        <Route path="/auth/login" element={<Login />} />

        {/* Seller routes – only seller or both */}
        <Route path="/seller" element={
          <ProtectedRoute role="seller"><SellerDashboard /></ProtectedRoute>
        } />
        <Route path="/seller/upload" element={
          <ProtectedRoute role="seller"><UploadInvoice /></ProtectedRoute>
        } />
        <Route path="/seller/invoices" element={
          <ProtectedRoute role="seller"><SentInvoices /></ProtectedRoute>
        } />

        {/* Buyer routes – only buyer or both */}
        <Route path="/buyer" element={
          <ProtectedRoute role="buyer"><BuyerDashboard /></ProtectedRoute>
        } />
        <Route path="/buyer/invoices" element={
          <ProtectedRoute role="buyer"><ReceivedInvoices /></ProtectedRoute>
        } />
        <Route path="/buyer/invoice/:id" element={
          <ProtectedRoute role="buyer"><InvoiceDetails /></ProtectedRoute>
        } />

      </Routes>
    </BrowserRouter>
  );
}