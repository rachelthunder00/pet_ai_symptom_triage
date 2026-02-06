"use client";

import { Bell, Trash2, ChevronRight, LogOut, User } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { useAuth } from "../../components/AuthContext";
import { usePet } from "../../components/PetContext";
import BottomNav from "../../components/BottomNav";
import dynamic from "next/dynamic";

const ChatbotModal = dynamic(() => import("../../components/chatbot/ChatbotModal"), { ssr: false });

export default function SettingsPage() {
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const router = useRouter();
  const { logout, user } = useAuth();
  const { petName } = usePet();
  const [chatbotOpen, setChatbotOpen] = useState(false);
  const [ownerName, setOwnerName] = useState("");

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedOwner = localStorage.getItem('ownerName');
      if (storedOwner) setOwnerName(storedOwner);
    }
  }, []);

  const handleSignOut = () => {
    logout();
    router.push("/auth");
  };

  return (
    <div className="min-h-screen pb-24" style={{ backgroundColor: '#f2dcdd' }}>
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Settings & Information</h1>
          <p className="text-gray-600 mt-1">Manage your account and preferences</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-6">

        {/* Notifications Section */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Bell className="w-5 h-5 text-indigo-600" />
            Notifications
          </h2>

          {/* Toggle Row */}
          <div className="flex items-center justify-between py-4 border-b border-gray-200">
            <div className="flex-1">
              <p className="text-gray-900 font-medium">Push Notifications</p>
              <p className="text-sm text-gray-600 mt-1">Receive updates about your pet's health</p>
            </div>
            <button
              onClick={() => setNotificationsEnabled(!notificationsEnabled)}
              className={`ml-4 relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${notificationsEnabled ? "bg-indigo-600" : "bg-gray-300"
                }`}
            >
              <span
                className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${notificationsEnabled ? "translate-x-7" : "translate-x-1"
                  }`}
              />
            </button>
          </div>
        </div>

        {/* Privacy Policy Section */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Privacy Policy</h2>
          <div className="space-y-4">
            <p className="text-gray-700 leading-relaxed">
              Your privacy is important to us. We are committed to protecting your personal information and ensuring transparency in how we collect, use, and maintain your data.
            </p>
            <p className="text-gray-700 leading-relaxed">
              All information you provide to us is encrypted and stored securely. We do not share your data with third parties without your explicit consent. For detailed information about our privacy practices, please contact our support team.
            </p>
            <button className="text-indigo-600 hover:text-indigo-700 font-medium text-sm flex items-center gap-1 mt-4">
              Read Full Privacy Policy
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* About Us Section */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">About Us</h2>
          <div className="space-y-4">
            <p className="text-gray-700 leading-relaxed">
              Our mission is to reduce unnecessary emergency room visits for pets by providing accessible, timely guidance and support from qualified veterinarians.
            </p>
            <p className="text-gray-700 leading-relaxed">
              We believe that every pet owner should have access to expert veterinary advice when they need it most. Through our platform, we connect pet owners with knowledgeable professionals who can help determine the right level of care their pets need.
            </p>
            <div className="bg-indigo-50 border-l-4 border-indigo-600 p-4 mt-4 rounded">
              <p className="text-indigo-900 text-sm font-medium">Version 1.0.0</p>
            </div>
          </div>
        </div>

        {/* Contact Support Section */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Contact Support</h2>
          <div className="space-y-4">
            <p className="text-gray-700">
              Have questions or need help? Our support team is here to assist you.
            </p>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Email</p>
              <p className="text-gray-900 font-medium mt-1">support@petshealth.com</p>
            </div>
            <button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-3 rounded-lg transition-colors">
              Send us a Message
            </button>
          </div>
        </div>

        {/* Account Section */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <User className="w-5 h-5 text-indigo-600" />
            Account
          </h2>
          {user && (
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <p className="text-sm text-gray-600">Signed in as</p>
              <p className="text-gray-900 font-medium mt-1">{user.email}</p>
            </div>
          )}
          <button
            onClick={handleSignOut}
            className="w-full bg-gray-800 hover:bg-gray-900 text-white font-medium py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <LogOut className="w-5 h-5" />
            Sign Out
          </button>
        </div>

        {/* Delete Data Section */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6 border-2 border-red-100">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Trash2 className="w-5 h-5 text-red-600" />
            Data Management
          </h2>
          <p className="text-gray-700 text-sm mb-4">
            Permanently delete your account and all associated data. This action cannot be undone.
          </p>
          <button className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-3 rounded-lg transition-colors flex items-center justify-center gap-2">
            <Trash2 className="w-5 h-5" />
            Delete My Data
          </button>
        </div>

      </div>

      {/* Bottom Navigation */}
      <BottomNav onChatClick={() => setChatbotOpen(true)} />
      <ChatbotModal open={chatbotOpen} onClose={() => setChatbotOpen(false)} ownerName={ownerName} petName={petName} />
    </div>
  );
}

