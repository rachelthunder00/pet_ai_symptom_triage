"use client";

import { Search, MapPin, Star, Phone, Home, User, MessageCircle, Users, Settings } from "lucide-react";
import { useRouter } from "next/navigation";
import BottomNav from "../components/BottomNav";
import { useState, useRef, useEffect } from "react";
// Fun facts for modal
const FUN_FACTS = [
  "Cats have five toes on their front paws, but only four on the back!",
  "Dogs' noses are as unique as human fingerprints.",
  "A group of kittens is called a kindle.",
  "Dalmatian puppies are born completely white and develop their spots as they grow.",
  "Cats can rotate their ears 180 degrees.",
  "Dogs have about 1,700 taste buds. Humans have about 9,000!",
  "The world’s oldest known pet cat existed 9,500 years ago.",
  "A Greyhound could beat a Cheetah in a long-distance race.",
  "Cats sleep for 70% of their lives.",
  "Dogs' sense of smell is 40x better than humans!"
];
import { usePet } from "../components/PetContext";
import dynamic from "next/dynamic";


const ChatbotModal = dynamic(() => import("../components/chatbot/ChatbotModal"), { ssr: false });

function HomePage() {
  // Fun fact modal state
  const [showFact, setShowFact] = useState(false);
  const [fact, setFact] = useState("");
  const handleVideoClick = () => {
    const randomFact = FUN_FACTS[Math.floor(Math.random() * FUN_FACTS.length)];
    setFact(randomFact);
    setShowFact(true);
  };
  const { petName } = usePet();
  const clinicScrollRef = useRef<HTMLDivElement>(null);
  const vetScrollRef = useRef<HTMLDivElement>(null);

  // Manual scroll handlers for arrows
  const scrollByAmount = (ref: React.RefObject<HTMLDivElement | null>, direction: 'left' | 'right', amount = 200) => {
    if (ref.current) {
      ref.current.scrollBy({ left: direction === 'left' ? -amount : amount, behavior: 'smooth' });
    }
  };
  // Owner name from localStorage
  const [ownerName, setOwnerName] = useState("");
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedOwner = localStorage.getItem('ownerName');
      if (storedOwner) setOwnerName(storedOwner);
      // Get user location if available
      const storedLoc = localStorage.getItem('userLocation');
      if (storedLoc) {
        try {
          const loc = JSON.parse(storedLoc);
          setUserLocation(loc);
        } catch { }
      }
    }
  }, []);

  // User location state
  const [userLocation, setUserLocation] = useState<{ lat: number, lng: number } | null>(null);
  const [activeTab, setActiveTab] = useState("home");
  const [chatbotOpen, setChatbotOpen] = useState(false);
  const [clinics, setClinics] = useState<any[]>([]);
  const [clinicsLoading, setClinicsLoading] = useState(false);
  const router = useRouter();

  // API base URL
  const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

  // Hero background images
  // Use exact filenames as in public folder (with Unicode narrow no-break space U+202F)
  const heroImages = [
    "/Screenshot 2026-01-26 at 1.52.39 PM.png",
    "/Screenshot 2026-01-26 at 1.54.22 PM.png",
    "/Screenshot 2026-01-26 at 1.54.38 PM.png",
    "/Screenshot 2026-01-26 at 1.54.48 PM.png",
  ];

  // Tabs are now handled in BottomNav

  // Fallback clinics (used when no location or API fails)
  const fallbackClinics = [
    { id: 1, name: "Paws Veterinary Clinic", address: "16950 Jog Rd #103, Delray Beach, FL 33446", rating: 5.0, mapsUrl: "https://maps.app.goo.gl/yD5t2sbRUS3Vd6897" },
    { id: 2, name: "Happy Tails Veterinary", address: "456 Animal Ave, Midtown", rating: 4.9 },
    { id: 3, name: "City Pet Hospital", address: "789 Main Rd, Uptown", rating: 4.7 },
  ];

  // Fetch nearby clinics when location is available
  useEffect(() => {
    if (userLocation) {
      setClinicsLoading(true);
      fetch(`${API_BASE_URL}/api/nearby-vets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude: userLocation.lat,
          longitude: userLocation.lng,
          radius_meters: 10000,
          max_results: 8
        })
      })
        .then(res => res.json())
        .then(data => {
          if (data.success && data.vets?.length > 0) {
            setClinics(data.vets.map((v: any, idx: number) => ({
              id: idx + 1,
              name: v.name,
              address: v.address || `${v.distance_miles || v.distance_km} ${v.distance_miles ? 'mi' : 'km'} away`,
              rating: v.rating || 4.5,
              distance_miles: v.distance_miles,
              distance_km: v.distance_km,
              phone: v.phone,
              opening_hours: v.opening_hours,
              is_24_hour: v.is_24_hour,
              is_emergency_clinic: v.is_emergency_clinic
            })));
          } else {
            setClinics(fallbackClinics);
          }
        })
        .catch(() => setClinics(fallbackClinics))
        .finally(() => setClinicsLoading(false));
    } else {
      setClinics(fallbackClinics);
    }
  }, [userLocation]);

  const vets = [
    { id: 1, name: "Dr. Sarah Johnson", title: "DVM", hospital: "Paws & Care Clinic", status: "Available to chat", avatar: "🐾" },
    { id: 2, name: "Dr. Michael Chen", title: "DVM", hospital: "Happy Tails Veterinary", status: "Available to chat", avatar: "🩺" },
    { id: 3, name: "Dr. Priya Patel", title: "DVM", hospital: "City Pet Hospital", status: "Available to chat", avatar: "🐶" },
    { id: 4, name: "Dr. Emily Lee", title: "DVM", hospital: "Greenfield Animal Care", status: "Available to chat", avatar: "🐱" },
    { id: 5, name: "Dr. Carlos Rivera", title: "DVM", hospital: "Sunshine Vet Clinic", status: "Available to chat", avatar: "🦴" },
    { id: 6, name: "Dr. Anna Kim", title: "DVM", hospital: "Riverbend Veterinary", status: "Available to chat", avatar: "🐾" },
    { id: 7, name: "Dr. John Smith", title: "DVM", hospital: "Pet Wellness Center", status: "Available to chat", avatar: "🐕" },
    { id: 8, name: "Dr. Lisa Wong", title: "DVM", hospital: "Companion Animal Hospital", status: "Available to chat", avatar: "🐈" },
  ];

  return (
    <main className="min-h-screen pb-24" style={{ backgroundColor: '#f2dcdd' }}>
      {/* Hero Header with auto-scrolling screenshots background */}
      <section className="relative pt-8 pb-32 px-4 overflow-hidden" style={{ backgroundColor: '#f2dcdd' }}>
        <style>{`
          .hero-marquee {
            display: flex;
            width: max-content;
            animation: hero-scroll 28s linear infinite;
          }
          @keyframes hero-scroll {
            0% { transform: translateX(0); }
            100% { transform: translateX(-50%); }
          }
        `}</style>

        {/* Moving background screenshots */}
        <div className="absolute inset-0 z-0 overflow-hidden bg-gray-900">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-400/80 via-blue-500/80 to-blue-600/80" />
          <div className="absolute left-0 top-0 h-full w-[200%]">
            <div className="hero-marquee h-full">
              {[...heroImages, ...heroImages].map((src, idx) => (
                <div key={idx} className="h-full w-[25vw] min-w-[220px] flex-shrink-0">
                  <div
                    className="h-full w-full bg-center bg-cover flex items-center justify-center"
                    style={{ backgroundImage: `url(${src})` }}
                  >
                    <img src={src} alt="screenshot" className="h-full w-full object-cover" style={{ pointerEvents: 'none' }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="mx-auto max-w-2xl relative z-10">
          <div className="absolute inset-0 bg-white/70 backdrop-blur-sm rounded-3xl" aria-hidden="true"></div>
          <div className="flex items-center justify-between relative px-4 py-3 rounded-3xl">
            {/* Left: Avatar & Greeting */}
            <div className="flex-1">
              <h1 className="text-2xl font-semibold" style={{ fontFamily: 'Poppins, var(--font-poppins)', color: '#2741cc' }}>
                {ownerName ? `Hello, ${ownerName} 👋` : "Hello 👋"}
              </h1>
              <p className="mt-1 text-sm font-medium text-gray-600" style={{ fontFamily: 'Poppins, var(--font-poppins)' }}>
                {`How can we help${petName && petName !== "your pet" ? ` ${petName}` : " your pet"} today?`}
              </p>
            </div>
            {/* Right: Decorative Interactive Paw */}
            <div
              className="group cursor-pointer ml-4"
              onClick={() => router.push("/auth")}
              title="Go to onboarding"
              style={{ cursor: "pointer" }}
            >
              <style>{`
                @keyframes paw-rotate {
                  0%, 100% { transform: rotate(0deg) scale(1); }
                  25% { transform: rotate(-5deg) scale(1.1); }
                  50% { transform: rotate(0deg) scale(1.2); }
                  75% { transform: rotate(5deg) scale(1.1); }
                }
                .paw-interactive:hover {
                  animation: paw-rotate 0.8s ease-in-out infinite;
                }
              `}</style>
              <div className="w-16 h-16 rounded-full bg-white/25 backdrop-blur-sm flex items-center justify-center text-4xl ring-2 ring-white/50 group-hover:ring-white/80 group-hover:bg-white/40 transition-all duration-300 paw-interactive">
                🐾
              </div>
              <div className="text-white/70 text-xs font-semibold text-center mt-2 group-hover:text-white transition-colors" style={{ fontFamily: 'var(--font-poppins)' }}>

              </div>
            </div>
          </div>
        </div>
        {/* Quick Symptom Check Card - Overlapping, styled like hero card */}
        <div className="mx-auto max-w-2xl -mb-20 relative z-20 mt-12">
          <div className="relative">
            <div className="absolute inset-0 bg-white/70 backdrop-blur-sm rounded-3xl" aria-hidden="true"></div>
            <div className="flex items-center justify-between relative px-4 py-3 rounded-3xl">
              <div className="flex-1">
                <h2 className="text-lg font-bold" style={{ fontFamily: 'Poppins, var(--font-poppins)', color: '#2741cc' }}>
                  AI Pet Health Check
                </h2>
                <p className="mt-1 text-sm font-medium text-gray-600" style={{ fontFamily: 'Poppins, var(--font-poppins)' }}>
                  Describe symptoms or upload a photo for instant AI assessment
                </p>
              </div>
              <span className="bg-blue-100 text-blue-700 text-xs font-bold px-3 py-1 rounded-full whitespace-nowrap ml-2">
                Recommended
              </span>
            </div>
            <div className="relative px-4 pb-4">
              <button
                type="button"
                onClick={() => setChatbotOpen(true)}
                className="w-full block bg-gradient-to-r from-blue-500 to-blue-600 text-white font-bold py-3 px-4 rounded-2xl text-center hover:shadow-lg hover:from-blue-600 hover:to-blue-700 transition-all active:scale-95 mt-4"
                style={{ fontFamily: 'Poppins, var(--font-poppins)' }}
              >
                Let’s Take a Look!
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Content Sections */}
      <div className="mt-12 space-y-8 px-4" style={{ backgroundColor: '#f2dcdd' }}>
        <div className="mx-auto max-w-2xl space-y-8">
          {/* Nearby Clinics */}
          <section className="relative mb-8">
            <div className="bg-white rounded-3xl shadow-lg p-6">
              <div className="mb-2 flex items-center gap-2">
                <MapPin className="w-5 h-5 text-blue-500" />
                <span className="text-sm font-semibold text-gray-700"></span>
                {userLocation ? (
                  <span className="text-xs text-green-600 ml-2">Location enabled</span>
                ) : (
                  <span className="text-xs text-gray-400 ml-2">Enable location in onboarding</span>
                )}
              </div>
              <style>{`
              .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
              .scrollbar-hide::-webkit-scrollbar { display: none; }
              .clinic-scroll { scroll-snap-type: x mandatory; scroll-behavior: smooth; }
            .clinic-card { scroll-snap-align: start; scroll-snap-stop: always; }
            .bubble-bg {
              background: radial-gradient(circle at 20% 40%, #e0f2fe 30%, transparent 70%),
                          radial-gradient(circle at 80% 60%, #bae6fd 30%, transparent 70%),
                          #f0f9ff;
            }
          `}</style>
              <div className="flex flex-col md:flex-row gap-8 items-stretch">
                {/* Clinics List - Left Side */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center mb-4 gap-4">
                    <h2 className="text-lg font-medium" style={{ fontFamily: 'Poppins, var(--font-poppins)', color: '#2741cc' }}>
                      Nearby Clinics
                    </h2>
                  </div>
                  <div className="bubble-bg rounded-3xl p-4 relative group">
                    {/* Side Arrows - show on hover */}
                    <button
                      type="button"
                      aria-label="Scroll left"
                      className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-white rounded-full shadow p-2 hover:bg-blue-100"
                      style={{ pointerEvents: 'auto' }}
                      onClick={() => scrollByAmount(clinicScrollRef, 'left')}
                    >
                      <span className="sr-only">Scroll left</span>
                      <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M15 19l-7-7 7-7" /></svg>
                    </button>
                    <button
                      type="button"
                      aria-label="Scroll right"
                      className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-white rounded-full shadow p-2 hover:bg-blue-100"
                      style={{ pointerEvents: 'auto' }}
                      onClick={() => scrollByAmount(clinicScrollRef, 'right')}
                    >
                      <span className="sr-only">Scroll right</span>
                      <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" /></svg>
                    </button>
                    <div ref={clinicScrollRef} className="clinic-scroll flex gap-4 pb-2 overflow-x-auto scrollbar-hide">
                      {clinics.map((clinic) => {
                        const mapsUrl = clinic.mapsUrl || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(clinic.name + ' ' + clinic.address)}`;
                        return (
                          <div
                            key={clinic.id}
                            className="clinic-card bg-white rounded-2xl p-4 shadow-sm hover:shadow-md transition-shadow flex-shrink-0 w-72"
                          >
                            <div className="flex items-start gap-4">
                              <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-xl flex-shrink-0">🏥</div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <h4 className="font-bold text-sm" style={{ fontFamily: 'Poppins, var(--font-poppins)', color: '#2741cc' }}>
                                    <a href={mapsUrl} target="_blank" rel="noopener noreferrer" className="hover:underline" style={{ color: '#2741cc' }}>
                                      {clinic.name}
                                    </a>
                                  </h4>
                                  {clinic.is_24_hour && (
                                    <span className="text-[10px] bg-green-500 text-white px-1.5 py-0.5 rounded-full font-semibold">24hr</span>
                                  )}
                                  {clinic.is_emergency_clinic && !clinic.is_24_hour && (
                                    <span className="text-[10px] bg-red-500 text-white px-1.5 py-0.5 rounded-full font-semibold">ER</span>
                                  )}
                                </div>
                                <div className="flex items-start gap-1 text-xs text-gray-600 mt-1" style={{ fontFamily: 'var(--font-poppins)' }}>
                                  <MapPin size={14} className="flex-shrink-0 mt-0.5" />
                                  <span className="line-clamp-2">{clinic.address}</span>
                                </div>
                                <div className="text-[10px] text-gray-500 mt-1" style={{ fontFamily: 'var(--font-poppins)' }}>
                                  {clinic.distance_miles ? `${clinic.distance_miles} mi` : (clinic.distance_km ? `${clinic.distance_km} km` : '')}
                                  {clinic.opening_hours && ` • ${clinic.opening_hours}`}
                                </div>
                              </div>
                              <div className="flex items-center gap-1 flex-shrink-0">
                                <Star size={14} className="fill-yellow-400 text-yellow-400" />
                                <span className="text-xs font-semibold text-gray-700">{clinic.rating}</span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
                {/* Video - Right Side */}
                <div className="flex items-center justify-center md:justify-end mt-6 md:mt-0 md:ml-8">
                  <div
                    style={{ width: 180, height: 180 }}
                    className="rounded-full overflow-hidden shadow-md flex-shrink-0 cursor-pointer group relative"
                    onClick={handleVideoClick}
                    title="Click for a fun fact!"
                  >
                    <video
                      src="/7515916-hd_1080_1920_30fps.mp4"
                      autoPlay
                      loop
                      muted
                      playsInline
                      className="w-full h-full object-cover group-hover:opacity-80 transition"
                      style={{ width: 180, height: 180, objectFit: 'cover', borderRadius: '50%' }}
                    />
                    <span className="absolute left-1/2 top-full mt-2 -translate-x-1/2 text-xs text-gray-500 opacity-0 group-hover:opacity-100 transition">Click for a fun fact!</span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Vets / Available to Chat */}
          <section className="relative mb-8" style={{ backgroundColor: '#f2dcdd' }}>
            <div className="bg-white rounded-3xl shadow-lg p-6">
              <style>{`
            .vet-scroll { scroll-snap-type: x mandatory; scroll-behavior: smooth; }
            .vet-card { scroll-snap-align: start; scroll-snap-stop: always; }
            .bubble-bg-vet {
              background: radial-gradient(circle at 80% 30%, #fbcfe8 30%, transparent 70%),
                          radial-gradient(circle at 20% 70%, #f9a8d4 30%, transparent 70%),
                          #fdf2f8;
            }
          `}</style>
              <div className="flex flex-col md:flex-row gap-8 items-stretch">
                {/* Video - Left Side */}
                <div
                  className="flex items-center justify-center md:justify-start mb-6 md:mb-0 md:mr-8"
                >
                  <div
                    style={{ width: 180, height: 180 }}
                    className="rounded-full overflow-hidden shadow-md flex-shrink-0 cursor-pointer group relative"
                    onClick={handleVideoClick}
                    title="Click for a fun fact!"
                  >
                    <video
                      src="/10467051-hd_2160_3840_30fps.mp4"
                      autoPlay
                      loop
                      muted
                      playsInline
                      className="w-full h-full object-cover group-hover:opacity-80 transition"
                      style={{ width: 180, height: 180, objectFit: 'cover', borderRadius: '50%' }}
                    />
                    <span className="absolute left-1/2 top-full mt-2 -translate-x-1/2 text-xs text-gray-500 opacity-0 group-hover:opacity-100 transition">Click for a fun fact!</span>
                  </div>
                </div>
                {/* Vets List - Right Side */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center mb-4">
                    <h2 className="text-lg font-medium" style={{ fontFamily: 'Poppins, var(--font-poppins)', color: '#2741cc' }}>
                      Vets
                    </h2>
                  </div>
                  <div className="bubble-bg-vet rounded-3xl p-4 relative group">
                    {/* Side Arrows - show on hover */}
                    <button
                      type="button"
                      aria-label="Scroll left"
                      className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-white rounded-full shadow p-2 hover:bg-pink-100"
                      style={{ pointerEvents: 'auto' }}
                      onClick={() => scrollByAmount(vetScrollRef, 'left')}
                    >
                      <span className="sr-only">Scroll left</span>
                      <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M15 19l-7-7 7-7" /></svg>
                    </button>
                    <button
                      type="button"
                      aria-label="Scroll right"
                      className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-white rounded-full shadow p-2 hover:bg-pink-100"
                      style={{ pointerEvents: 'auto' }}
                      onClick={() => scrollByAmount(vetScrollRef, 'right')}
                    >
                      <span className="sr-only">Scroll right</span>
                      <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" /></svg>
                    </button>
                    <div ref={vetScrollRef} className="vet-scroll flex gap-4 pb-2 overflow-x-auto scrollbar-hide">
                      {vets.map((vet) => {
                        return (
                          <div
                            key={vet.id}
                            className="vet-card bg-white rounded-2xl p-4 shadow-sm hover:shadow-md transition-shadow flex-shrink-0 w-80"
                          >
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex items-start gap-3 flex-1 min-w-0">
                                <div className="w-12 h-12 rounded-full bg-pink-100 flex items-center justify-center text-xl flex-shrink-0">{vet.avatar}</div>
                                <div className="min-w-0">
                                  <h4 className="font-bold text-gray-900 text-sm" style={{ fontFamily: 'var(--font-poppins)' }}>
                                    {vet.name === "Dr. Sarah Johnson" ? (
                                      <a href="https://dalemabryanimalhospital.com/dvm/sarah-a-johnson-dvm/" target="_blank" rel="noopener noreferrer" className="hover:underline text-pink-700">
                                        {vet.name}
                                      </a>
                                    ) : vet.name === "Dr. Michael Chen" ? (
                                      <a href="https://coronadoanimalhospital.com/about-us?srsltid=AfmBOopr21g76AHGsAdYsPxHVxOOlhvlcFcMEkwUFH32Ca5xuGyxem16-" target="_blank" rel="noopener noreferrer" className="hover:underline text-pink-700">
                                        {vet.name}
                                      </a>
                                    ) : (
                                      vet.name
                                    )}, {vet.title}
                                  </h4>
                                  <p className="text-xs text-gray-600 mt-1" style={{ fontFamily: 'var(--font-poppins)' }}>{vet.hospital}</p>
                                  <div className="mt-2">
                                    <span className="inline-block bg-green-100 text-green-700 text-xs font-semibold px-2 py-1 rounded-full" style={{ fontFamily: 'var(--font-poppins)' }}>
                                      ✓ {vet.status}
                                    </span>
                                  </div>
                                </div>
                              </div>
                              <Phone
                                size={20}
                                className="text-pink-500 flex-shrink-0 hover:scale-110 transition-transform cursor-pointer"
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* About Us with Dog Video */}
          <section className="mb-8">
            <div className="bg-white rounded-2xl p-6 shadow-sm flex items-center gap-6 flex-row-reverse">
              {/* Dog video frame on right */}
              <div style={{ width: 180, height: 180 }} className="rounded-full overflow-hidden shadow-md flex-shrink-0 cursor-pointer group" onClick={handleVideoClick} title="Click for a fun fact!">
                <video
                  className="w-full h-full object-cover group-hover:opacity-80 transition"
                  autoPlay
                  loop
                  muted
                  playsInline
                  style={{ width: 180, height: 180, objectFit: 'cover', borderRadius: '50%' }}
                >
                  <source src="/7516662-hd_1080_1920_30fps.mp4" type="video/mp4" />
                </video>
                <span className="absolute left-1/2 top-full mt-2 -translate-x-1/2 text-xs text-gray-500 opacity-0 group-hover:opacity-100 transition">Click for a fun fact!</span>
              </div>
              {/* Fun Fact Modal */}
              {showFact && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
                  <div className="bg-white rounded-2xl shadow-lg p-6 max-w-xs w-full text-center relative animate-fade-in">
                    <button
                      className="absolute top-2 right-2 text-gray-400 hover:text-gray-700 text-xl font-bold"
                      onClick={() => setShowFact(false)}
                      aria-label="Close"
                    >
                      ×
                    </button>
                    <h4 className="text-lg font-semibold mb-2 text-blue-700">Fun Fact</h4>
                    <p className="text-gray-700 text-base">{fact}</p>
                  </div>
                </div>
              )}
              <div className="flex-1">
                <h3 className="text-lg font-medium mb-3" style={{ fontFamily: 'Poppins, var(--font-poppins)', color: '#2741cc' }}>
                  About Fuzzy Friend
                </h3>
                <p className="text-sm text-gray-600 font-medium leading-relaxed mb-4" style={{ fontFamily: 'var(--font-poppins)' }}>
                  Fuzzy Friend is an AI-powered pet symptom triage app that helps dog and cat owners quickly assess whether their pet needs emergency care, a same-day vet visit, or can safely be monitored at home. Our product vision is to provide clear answers in anxious moments and help you make confident care decisions.
                </p>
                <button className="text-blue-600 font-bold text-sm hover:text-blue-700 transition-colors" style={{ fontFamily: 'var(--font-poppins)' }}>
                  Learn more →
                </button>
              </div>
            </div>
          </section>

          {/* Bottom Navigation */}
          <BottomNav onChatClick={() => setChatbotOpen(true)} />
        </div>
      </div>
      <ChatbotModal open={chatbotOpen} onClose={() => setChatbotOpen(false)} ownerName={ownerName} petName={petName} />
    </main>
  );
}

export default HomePage;
