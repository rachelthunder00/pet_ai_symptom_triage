"use client";
import React, { useState } from "react";
import { ArrowLeft, Edit2, Plus, Calendar, Heart, ClipboardList, TrendingDown } from "lucide-react";
import Link from "next/link";
import { usePet } from "../../components/PetContext";
import BottomNav from "../../components/BottomNav";
import dynamic from "next/dynamic";

const ChatbotModal = dynamic(() => import("../../components/chatbot/ChatbotModal"), { ssr: false });

function ProfilePage() {
  const { petName } = usePet();
  const [chatbotOpen, setChatbotOpen] = useState(false);
  const [ownerName, setOwnerName] = useState("");

  // Get pet details from localStorage (set in onboarding)
  const [petDetails, setPetDetails] = React.useState({
    name: petName && petName !== "your pet" ? petName : "your pet",
    breed: "Golden Retriever",
    weight: "32 kg",
    age: "3 years",
  });

  React.useEffect(() => {
    if (typeof window !== 'undefined') {
      const breed = localStorage.getItem('petBreed');
      const weight = localStorage.getItem('petWeight');
      const age = localStorage.getItem('petAge');
      const storedOwner = localStorage.getItem('ownerName');
      if (storedOwner) setOwnerName(storedOwner);
      setPetDetails((prev) => ({
        ...prev,
        breed: breed || prev.breed,
        weight: weight || prev.weight,
        age: age || prev.age,
      }));
    }
  }, [petName]);

  const medicalHistory = [
    "No Known Allergies",
    "Omega-3 Supplement (Daily)",
    "None",
    "Up to date (Last: Dec 2024)",
    "Spay Surgery (2022)",
  ];

  const metrics = [
    { icon: Calendar, label: "Last Assessment", value: "5 days ago" },
    { icon: Heart, label: "Typical Urgency", value: "Low" },
    { icon: ClipboardList, label: "Symptoms Logged", value: "12" },
    { icon: TrendingDown, label: "Visits Avoided", value: "~3" },
  ];

  const assessments = [
    {
      date: "Jan 18, 2025 • 2:30 PM",
      symptoms: "Slight coughing, clear nasal discharge",
      urgency: "Low",
      urgencyColor: "bg-green-100 text-green-700",
    },
    {
      date: "Jan 10, 2025 • 11:15 AM",
      symptoms: "Limping on rear left leg after play",
      urgency: "Medium",
      urgencyColor: "bg-yellow-100 text-yellow-700",
    },
    {
      date: "Dec 28, 2024 • 6:45 PM",
      symptoms: "Vomiting, reduced appetite",
      urgency: "High",
      urgencyColor: "bg-red-100 text-red-700",
    },
  ];

  return (
    <main className="min-h-screen pb-24" style={{ backgroundColor: '#f2dcdd' }}>
      {/* Header */}
      <section className="bg-gradient-to-br from-blue-400 to-blue-500 pt-8 pb-6 px-4 sticky top-0 z-10">
        <div className="mx-auto max-w-2xl flex items-center gap-4">
          <Link href="/">
            <button className="p-2 hover:bg-white/20 rounded-full transition-colors">
              <ArrowLeft size={24} className="text-white" />
            </button>
          </Link>
          <h1 className="text-2xl font-semibold text-white" style={{ fontFamily: 'var(--font-poppins)' }}>
            My Pets
          </h1>
        </div>
      </section>

      {/* Content */}
      <div className="mx-auto max-w-2xl px-4 mt-8 space-y-8">

        {/* Video and Pet Profile Card Side by Side */}
        <section>
          <div className="bg-white rounded-3xl shadow-lg p-10 max-w-4xl mx-auto">
            <div className="flex items-start gap-8 mb-6">
              {/* Cat video on the left */}
              <div className="flex flex-col gap-4">
                <div className="w-48 h-48 rounded-full overflow-hidden shadow-lg flex-shrink-0">
                  <video
                    className="w-full h-full object-cover"
                    autoPlay
                    loop
                    muted
                    playsInline
                  >
                    <source src="/20620114-hd_1080_1920_50fps.mp4" type="video/mp4" />
                  </video>
                </div>
              </div>
              {/* Pet profile info on the right */}
              <div className="flex items-start gap-4">
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'var(--font-poppins)' }}>
                    {petDetails.name}
                  </h2>
                  <p className="text-sm text-gray-600 mt-1" style={{ fontFamily: 'var(--font-poppins)' }}>
                    {petDetails.breed}
                  </p>
                </div>
              </div>
            </div>

            {/* Pet Details Grid */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-blue-50 rounded-2xl p-4">
                <p className="text-xs text-gray-600 font-medium mb-1" style={{ fontFamily: 'var(--font-poppins)' }}>
                  Age
                </p>
                <p className="text-lg font-bold text-gray-900" style={{ fontFamily: 'var(--font-poppins)' }}>
                  {petDetails.age}
                </p>
              </div>
              <div className="bg-blue-50 rounded-2xl p-4">
                <p className="text-xs text-gray-600 font-medium mb-1" style={{ fontFamily: 'var(--font-poppins)' }}>
                  Breed
                </p>
                <p className="text-lg font-bold text-gray-900" style={{ fontFamily: 'var(--font-poppins)' }}>
                  {petDetails.breed}
                </p>
              </div>
              <div className="bg-blue-50 rounded-2xl p-4">
                <p className="text-xs text-gray-600 font-medium mb-1" style={{ fontFamily: 'var(--font-poppins)' }}>
                  Weight
                </p>
                <p className="text-lg font-bold text-gray-900" style={{ fontFamily: 'var(--font-poppins)' }}>
                  {petDetails.weight}
                </p>
              </div>
              <div className="bg-blue-50 rounded-2xl p-4">
                <p className="text-xs text-gray-600 font-medium mb-1" style={{ fontFamily: 'var(--font-poppins)' }}>
                  Status
                </p>
                <p className="text-lg font-bold text-green-600" style={{ fontFamily: 'var(--font-poppins)' }}>
                  Healthy
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button className="flex-1 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-bold py-3 px-4 rounded-2xl flex items-center justify-center gap-2 hover:shadow-lg hover:from-blue-600 hover:to-blue-700 transition-all active:scale-95" style={{ fontFamily: 'var(--font-poppins)' }}>
                <Edit2 size={18} />
                Edit Profile
              </button>
              <button className="flex-1 bg-blue-100 text-blue-600 font-bold py-3 px-4 rounded-2xl flex items-center justify-center gap-2 hover:bg-blue-200 transition-all active:scale-95" style={{ fontFamily: 'var(--font-poppins)' }}>
                <Plus size={18} />
                Add Pet
              </button>
            </div>
          </div>
        </section>

        {/* Medical History */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900" style={{ fontFamily: 'var(--font-poppins)' }}>
              Medical History
            </h3>
          </div>

          <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
            <div className="divide-y divide-gray-200">
              {medicalHistory.map((item, idx) => (
                <div key={idx} className="p-4 hover:bg-gray-50 transition-colors">
                  <p className="text-sm text-gray-700 font-medium" style={{ fontFamily: 'var(--font-poppins)' }}>
                    {item}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <button className="w-full mt-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-bold py-3 px-4 rounded-2xl hover:shadow-lg hover:from-blue-600 hover:to-blue-700 transition-all active:scale-95" style={{ fontFamily: 'var(--font-poppins)' }}>
            Update History
          </button>
        </section>

        {/* Metrics / Insights */}
        <section>
          <h3 className="text-lg font-medium text-gray-900 mb-4" style={{ fontFamily: 'var(--font-poppins)' }}>
            Health Insights
          </h3>

          <div className="grid grid-cols-2 gap-4 mb-4">
            {metrics.map((metric, idx) => {
              const Icon = metric.icon;
              return (
                <div key={idx} className="bg-white rounded-2xl shadow-sm p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-2 mb-3">
                    <Icon size={20} className="text-blue-600" />
                    <p className="text-xs text-gray-600 font-medium" style={{ fontFamily: 'var(--font-poppins)' }}>
                      {metric.label}
                    </p>
                  </div>
                  <p className="text-xl font-bold text-gray-900" style={{ fontFamily: 'var(--font-poppins)' }}>
                    {metric.value}
                  </p>
                </div>
              );
            })}
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-2xl p-4">
            <p className="text-xs text-blue-700 font-medium" style={{ fontFamily: 'var(--font-poppins)' }}>
              ℹ️ Estimates are informational only. Consult your veterinarian for medical advice.
            </p>
          </div>
        </section>

        {/* Recent Assessments */}
        <section>
          <h3 className="text-lg font-medium text-gray-900 mb-4" style={{ fontFamily: 'var(--font-poppins)' }}>
            Recent Assessments
          </h3>

          <div className="space-y-3">
            {assessments.map((assessment, idx) => (
              <div key={idx} className="bg-white rounded-2xl shadow-sm p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <p className="text-xs text-gray-600 font-medium" style={{ fontFamily: 'var(--font-poppins)' }}>
                      {assessment.date}
                    </p>
                    <p className="text-sm text-gray-900 font-semibold mt-2" style={{ fontFamily: 'var(--font-poppins)' }}>
                      {assessment.symptoms}
                    </p>
                  </div>
                  <span className={`${assessment.urgencyColor} text-xs font-bold px-3 py-1 rounded-full whitespace-nowrap ml-2`}>
                    {assessment.urgency}
                  </span>
                </div>
                <button className="w-full text-blue-600 font-bold text-sm hover:text-blue-700 transition-colors text-left pt-2 border-t border-gray-200" style={{ fontFamily: 'var(--font-poppins)' }}>
                  View Details →
                </button>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Bottom Navigation */}
      <BottomNav onChatClick={() => setChatbotOpen(true)} />
      <ChatbotModal open={chatbotOpen} onClose={() => setChatbotOpen(false)} ownerName={ownerName} petName={petName} />
    </main>
  );
}

export default ProfilePage;


