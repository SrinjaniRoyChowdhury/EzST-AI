import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import bgImage from "../../assets/background.jpeg";
import chatbot from "../../assets/chatbot.png";
import manageInventory from "../../assets/manageInventory.png";
import predictCashFlow from "../../assets/predictcashflow.png";
import viewPayments from "../../assets/viewPayment.png";
import inv1 from "../../assets/inv1.jpeg";
import inv2 from "../../assets/inv2.jpeg";
import inv3 from "../../assets/inv3.jpeg";
import inv4 from "../../assets/inv4.jpeg";
import invoicePreview from "../../assets/invoicePreview.jpeg"; // 👈 replace with your actual filename


export default function BuyerDashboard() {
  const navigate = useNavigate();
  const [latestInvoice, setLatestInvoice] = useState(null);

  useEffect(() => {
    const fetchLatestInvoice = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/invoices/buyer/received?buyer_gstin=BUYER_123`
        );
        if (!response.ok) throw new Error("Failed to fetch");
        const data = await response.json();
        data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        if (data.length > 0) {
          setLatestInvoice(data[0]);
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchLatestInvoice();
  }, []);

  return (
    <div className="w-full bg-white font-sans overflow-x-hidden">

      {/* 1. Hero Section */}
      <div
        className="relative w-full flex flex-col items-center pt-24 pb-64 px-4 sm:px-8 lg:px-24 bg-cover bg-center"
        style={{ backgroundImage: `url(${bgImage})` }}
      >
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative z-10 flex flex-col items-center gap-12 text-center mt-12 w-full">
          <h1 className="text-white text-5xl md:text-6xl font-bold font-inter tracking-tight drop-shadow-[0_4px_4px_rgba(0,0,0,0.5)]">
            Hello, Mr. Dutta
          </h1>
          <div className="flex flex-wrap items-center justify-center gap-4 p-2 shadow-[0_4px_4px_rgba(0,0,0,0.25)] rounded-2xl max-w-full">
            <button
              onClick={() => navigate('/buyer/social-media-invoice')}
              className="bg-white text-[#D50000] px-6 py-4 rounded-xl font-semibold text-lg transition-transform hover:scale-105 active:scale-95 shadow-md flex items-center justify-center"
            >
              Check New Invoice
            </button>
            <button className="bg-transparent border-2 border-white/70 text-white px-6 py-4 rounded-xl font-semibold text-lg transition-transform hover:scale-105 hover:bg-white/10 active:scale-95 shadow-md flex items-center justify-center drop-shadow-[0_4px_4px_rgba(0,0,0,0.25)]">
              Check Pending Invoice
            </button>
          </div>
        </div>
      </div>

      {/* Hero Overlapping Image */}
      <div className="relative z-20 w-full -mt-32 md:-mt-40 mb-16 px-4 sm:px-8 lg:px-24">
        <div className="relative max-w-2xl mx-auto overflow-hidden rounded-2xl border-2 border-[#D50000] shadow-[0_5px_19px_rgba(0,0,0,0.12)]">
          <img
            src={invoicePreview}
            alt="Invoice Preview"
            className="w-full object-contain block"
          />

          {/* Gradient fade at bottom so button sits cleanly over image */}
          <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-black/40 to-transparent" />

          {/* Button pinned to bottom center */}
          <div className="absolute bottom-6 left-0 right-0 flex justify-center">
            <button
              onClick={() => latestInvoice && navigate(`/buyer/invoice/${latestInvoice.id}`)}
              disabled={!latestInvoice}
              className="bg-white text-[#D50000] font-bold text-lg px-8 py-3 rounded-xl shadow-lg hover:bg-[#D50000] hover:text-white transition-all duration-200 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Click to open latest invoice →
            </button>
          </div>
        </div>
      </div>

      {/* 2. Invoices Section (Staggered Grid) */}
      <div className="w-full py-20 px-4 sm:px-8 lg:px-24 bg-gray-50 flex flex-col bg-cover bg-center">
        <div className="max-w-6xl mx-auto w-full flex flex-col lg:flex-row gap-16 lg:gap-24">

          {/* Left Text */}
          <div className="flex-1 flex flex-col items-start gap-8 lg:py-16">
            <h2 className="text-black text-[2.5rem] leading-[1.2] font-extrabold font-inter tracking-tight">
              View All Invoices
            </h2>
            <p className="text-black/60 text-xl md:text-[1.5rem] font-medium leading-[1.45] max-w-lg">
              Browse a complete list of your invoices with details like date, amount, and payment status.
            </p>
            <button
              onClick={() => navigate('/buyer/invoices')}
              className="mt-4 bg-[#D50000] text-white px-8 py-4 rounded-xl font-bold text-lg hover:bg-red-700 hover:shadow-lg transition-all active:scale-95"
            >
              Check All Your Invoices
            </button>
          </div>

          {/* Right Images (Staggered Layout) */}
          <div className="flex-1 flex gap-6 md:gap-8 justify-center h-[500px] sm:h-[700px] overflow-hidden">
            <div className="flex flex-col gap-6 md:gap-8 flex-1">
              <img src={inv1} className="w-full rounded-2xl shadow-[0_4px_4px_rgba(0,0,0,0.25)] object-cover aspect-[504/390]" alt="Invoice 1" />
              <img src={inv2} className="w-full rounded-2xl shadow-[0_4px_4px_rgba(0,0,0,0.25)] object-cover aspect-[504/390]" alt="Invoice 2" />
            </div>
            <div className="flex flex-col gap-6 md:gap-8 flex-1 mt-16 md:mt-24">
              <img src={inv3} className="w-full rounded-2xl shadow-[0_4px_4px_rgba(0,0,0,0.25)] object-cover aspect-[504/390]" alt="Invoice 3" />
              <img src={inv4} className="w-full rounded-2xl shadow-[0_4px_4px_rgba(0,0,0,0.25)] object-cover aspect-[504/390]" alt="Invoice 4" />
            </div>
          </div>
        </div>
      </div>

      {/* 3. Features Section */}
      <div
        className="w-full py-24 sm:py-32 px-4 sm:px-8 lg:px-24 flex justify-center items-center bg-cover bg-center"
        style={{ backgroundImage: `url(${bgImage})` }}
      >
        <div className="max-w-6xl w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 md:gap-12">

          <div
            onClick={() => navigate('/buyer/chatbot')}
            className="flex flex-col items-center justify-center gap-6 group hover:-translate-y-2 transition-transform duration-300 cursor-pointer"
          >
            <div className="w-[80%] aspect-[252/148] rounded-[1rem] bg-white shadow-md relative overflow-hidden flex items-center justify-center border border-gray-100">
              <img src={chatbot} className="w-full h-full object-cover" alt="Validate Invoice with AI" />
            </div>
            <h3 className="text-[#D50000] text-lg md:text-xl font-extrabold text-center font-inter px-4 leading-snug">
              Validate Invoice with AI
            </h3>
          </div>

          <div className="flex flex-col items-center justify-center gap-6 group hover:-translate-y-2 transition-transform duration-300">
            <div className="w-[80%] aspect-[188/114] rounded-[1rem] bg-white shadow-md flex items-center justify-center border border-gray-100 overflow-hidden">
              <img src={predictCashFlow} className="w-full h-full object-cover" alt="Predict Cash Flow" />
            </div>
            <h3 className="text-[#D50000] text-lg md:text-xl font-extrabold text-center font-inter px-4 leading-snug">
              Predict Cash Flow
            </h3>
          </div>

          <div className="flex flex-col items-center justify-center gap-6 group hover:-translate-y-2 transition-transform duration-300">
            <div className="w-[80%] aspect-[166/143] rounded-[1rem] bg-white shadow-md flex items-center justify-center border border-gray-100 overflow-hidden">
              <img src={viewPayments} className="w-full h-full object-cover" alt="View Payments" />
            </div>
            <h3 className="text-[#D50000] text-lg md:text-xl font-extrabold text-center font-inter px-4 leading-snug">
              View Payments
            </h3>
          </div>

          <div className="flex flex-col items-center justify-center gap-6 group hover:-translate-y-2 transition-transform duration-300">
            <div className="w-[80%] aspect-[188/141] rounded-[1rem] bg-white shadow-md flex items-center justify-center border border-gray-100 overflow-hidden">
              <img src={manageInventory} className="w-full h-full object-cover" alt="Manage Inventory" />
            </div>
            <h3 className="text-[#D50000] text-lg md:text-xl font-extrabold text-center font-inter px-4 leading-snug">
              Manage Inventory
            </h3>
          </div>

        </div>
      </div>

    </div>
  );
}