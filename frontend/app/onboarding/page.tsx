"use client";

import { useState } from "react";
import { usePet, dispatchPetInfoUpdated } from "../../components/PetContext";
import { useRouter } from "next/navigation";
import { useAuth } from "../../components/AuthContext";

// Location permission helper
function requestLocation(setLocation: (loc: GeolocationPosition | null) => void, setError: (err: string) => void) {
  if (!navigator.geolocation) {
    setError("Geolocation is not supported by your browser.");
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (position) => {
      setLocation(position);
      setError("");
      // Save to localStorage for homepage use
      if (typeof window !== 'undefined') {
        localStorage.setItem('userLocation', JSON.stringify({
          lat: position.coords.latitude,
          lng: position.coords.longitude
        }));
      }
    },
    (err) => {
      setError("Location permission denied or unavailable.");
      setLocation(null);
    }
  );
}

export default function OnboardingPage() {
  const [nameError, setNameError] = useState("");
  const [ownerNameError, setOwnerNameError] = useState("");
  const [weightError, setWeightError] = useState("");
  const [allergiesError, setAllergiesError] = useState("");
  const [speciesError, setSpeciesError] = useState("");
  const [ageError, setAgeError] = useState("");
  const [breedError, setBreedError] = useState("");
  const [sexError, setSexError] = useState("");
  const [spayStatusError, setSpayStatusError] = useState("");
  const [heatCycleError, setHeatCycleError] = useState("");
  const [vaccinationError, setVaccinationError] = useState("");
  const [lifestyleError, setLifestyleError] = useState("");
  const [historyFlagsError, setHistoryFlagsError] = useState("");
  const [localPetName, setLocalPetName] = useState("");
  const [ownerName, setOwnerName] = useState("");
  const [weight, setWeight] = useState("");
  const [weightUnit, setWeightUnit] = useState<'kg' | 'lb'>("kg");
  const [allergies, setAllergies] = useState("");
  const { setPetName } = usePet();
  const router = useRouter();
  const { completeOnboarding, isLoading: authLoading } = useAuth();
  const [species, setSpecies] = useState<"Dog" | "Cat">("Dog");
  const [age, setAge] = useState(2);
  const [breed, setBreed] = useState("");
  const [sex, setSex] = useState<"Male" | "Female" | "Unknown">("Female");
  const [spayStatus, setSpayStatus] = useState<"Yes" | "No" | "Unknown">("Yes");
  const [heatCycle, setHeatCycle] = useState("Unknown");
  const [vaccination, setVaccination] = useState("Fully vaccinated");
  const [lifestyle, setLifestyle] = useState("Indoor only");
  const [historyFlags, setHistoryFlags] = useState<string[]>([]);

  // Location state
  const [location, setLocation] = useState<GeolocationPosition | null>(null);
  const [locationError, setLocationError] = useState("");
  const [locationRequested, setLocationRequested] = useState(false);

  const heatCycleVisible = spayStatus === "No" && sex === "Female" && (species === "Dog" || species === "Cat");

  const toggleFlag = (flag: string) => {
    setHistoryFlags((prev) =>
      prev.includes(flag) ? prev.filter((f) => f !== flag) : [...prev, flag]
    );
  };

  const historyOptions = [
    "Surgery",
    "Hospitalization",
    "Adverse reaction to medication",
    "History of eating things they shouldn’t",
    "Seizures",
    "Previous emergency vet visit",
    "None of the above",
  ];

  const heatOptions = [
    "Within 1 month",
    "1–3 months",
    "3–6 months",
    "More than 6 months",
    "Unknown",
  ];

  const vaccinationOptions = [
    "Fully vaccinated",
    "Started but not completed",
    "Not vaccinated",
    "Unknown",
  ];

  const lifestyleOptions = [
    "Indoor only",
    "Mostly indoor with supervised outdoor time",
    "Indoor/outdoor",
    "Mostly outdoor",
  ];

  const [saving, setSaving] = useState(false);
  const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    let valid = true;
    // Owner name
    if (!ownerName.trim()) {
      setOwnerNameError("Please enter your name.");
      valid = false;
    } else {
      setOwnerNameError("");
    }
    // Pet name
    if (!localPetName.trim()) {
      setNameError("Please enter your pet's name.");
      valid = false;
    } else {
      setNameError("");
    }
    // Weight
    if (!weight.trim() || isNaN(Number(weight)) || Number(weight) <= 0) {
      setWeightError("Please enter your pet's weight.");
      valid = false;
    } else {
      setWeightError("");
    }
    // Allergies
    if (!allergies.trim()) {
      setAllergiesError("Please enter allergies or 'none'.");
      valid = false;
    } else {
      setAllergiesError("");
    }
    // Species
    if (!species) {
      setSpeciesError("Please select a species.");
      valid = false;
    } else {
      setSpeciesError("");
    }
    // Age
    if (age === undefined || age === null || isNaN(Number(age)) || Number(age) < 0) {
      setAgeError("Please enter your pet's age.");
      valid = false;
    } else {
      setAgeError("");
    }
    // Breed
    if (!breed.trim()) {
      setBreedError("Please enter your pet's breed.");
      valid = false;
    } else {
      setBreedError("");
    }
    // Sex
    if (!sex) {
      setSexError("Please select your pet's sex.");
      valid = false;
    } else {
      setSexError("");
    }
    // Spay/Neuter
    if (!spayStatus) {
      setSpayStatusError("Please select spay/neuter status.");
      valid = false;
    } else {
      setSpayStatusError("");
    }
    // Heat cycle (if visible)
    if (heatCycleVisible && (!heatCycle || heatCycle === "Unknown")) {
      setHeatCycleError("Please select last heat cycle.");
      valid = false;
    } else {
      setHeatCycleError("");
    }
    // Vaccination
    if (!vaccination) {
      setVaccinationError("Please select vaccination status.");
      valid = false;
    } else {
      setVaccinationError("");
    }
    // Lifestyle
    if (!lifestyle) {
      setLifestyleError("Please select a lifestyle.");
      valid = false;
    } else {
      setLifestyleError("");
    }
    // Medical history flags
    if (!historyFlags.length) {
      setHistoryFlagsError("Please select at least one medical history flag.");
      valid = false;
    } else {
      setHistoryFlagsError("");
    }
    if (!valid) return;
    
    setSaving(true);
    
    // Save pet profile to backend (non-blocking - we save to localStorage too)
    const token = localStorage.getItem('authToken');
    if (token) {
      fetch(`${API_BASE_URL}/api/pet-profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: localPetName.trim(),
          species: species.toLowerCase(),
          breed: breed.trim(),
          age_years: age,
          weight: Number(weight),
          weight_unit: weightUnit,
          sex: sex,
          spay_neuter_status: spayStatus,
          last_heat_cycle: heatCycleVisible ? heatCycle : null,
          vaccination_status: vaccination,
          lifestyle: lifestyle,
          allergies: allergies.trim(),
          medical_history_flags: historyFlags
        })
      })
        .then(res => res.json())
        .then(data => {
          if (!data.success) {
            console.warn('Backend save failed, using localStorage:', data.error);
          }
        })
        .catch(err => console.warn('Backend save failed, using localStorage:', err));
    }
    
    // Also save to localStorage for offline access
    setPetName(localPetName.trim());
    if (typeof window !== 'undefined') {
      if (ownerName.trim()) {
        localStorage.setItem('ownerName', ownerName.trim());
      }
      localStorage.setItem('petWeight', weight);
      localStorage.setItem('petWeightUnit', weightUnit);
      localStorage.setItem('petBreed', breed);
      localStorage.setItem('petAge', age ? age.toString() : '');
      localStorage.setItem('petSpecies', species.toLowerCase());
      localStorage.setItem('petName', localPetName.trim());
      
      // Notify PetContext about the update
      dispatchPetInfoUpdated();
    }
    
    setSaving(false);
    
    // Mark onboarding complete and redirect
    completeOnboarding();
    router.push("/");
  };

  return (
    <main className="min-h-screen bg-gray-50 pb-24 px-4">
      <div className="max-w-2xl mx-auto py-6 space-y-6">
        {/* Header */}
        <header className="space-y-1">
          <h1 className="text-2xl font-bold text-gray-900">
            Let’s learn a bit about your fuzzy friend!
          </h1>
          <p className="text-sm text-gray-500">
            This will take under 2 minutes.
          </p>
        </header>

        {/* Pet Basics */}
        <form onSubmit={handleSubmit}>
          <section className="bg-white rounded-2xl shadow-sm p-5 space-y-4 border border-gray-100">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Pet basics</h2>
              <p className="text-sm text-gray-500">Tell us a bit about your pet and yourself.</p>
            </div>
            <div className="space-y-3">
              <label className="block">
                <span className="text-sm font-medium text-gray-900">What is your name? (Pet owner) <span className="text-red-500">*</span></span>
                <input
                  type="text"
                  value={ownerName}
                  onChange={(e) => setOwnerName(e.target.value)}
                  placeholder="e.g., Alex Smith"
                  className="mt-1 w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                />
                {ownerNameError && <span className="text-xs text-red-500">{ownerNameError}</span>}
              </label>
            </div>
          </section>

          {/* Location Permission - below pet basics */}
          <section className="bg-white rounded-2xl shadow-sm p-5 space-y-3 border border-gray-100 mt-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <span className="text-sm font-medium text-gray-900">Enable location to find nearby clinics</span>
              <div className="flex flex-row sm:flex-col items-center gap-2 sm:gap-2">
                {/* Video removed */}
                {/* Toggle switch below video on all screens */}
                <button
                  type="button"
                  role="switch"
                  aria-checked={location ? 'true' : 'false'}
                  onClick={() => {
                    if (!location) {
                      setLocationRequested(true);
                      requestLocation(setLocation, setLocationError);
                    } else {
                      setLocation(null);
                      setLocationError("");
                      if (typeof window !== 'undefined') {
                        localStorage.removeItem('userLocation');
                      }
                    }
                  }}
                  className={`relative inline-flex h-6 w-12 items-center rounded-full transition-colors focus:outline-none ${location ? 'bg-blue-600' : 'bg-gray-300'}`}
                  style={{ minWidth: 48 }}
                >
                  <span className="sr-only">Enable location</span>
                  <span
                    className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${location ? 'translate-x-6' : 'translate-x-1'}`}
                  />
                  <span className="ml-3 text-xs font-semibold text-gray-700 select-none">{location ? 'Yes' : 'No'}</span>
                </button>
              </div>
            </div>
            {locationRequested && !location && (
              <span className="text-xs text-red-500">{locationError || 'Waiting for permission...'}</span>
            )}
            {location && (
              <span className="text-xs text-green-600">Location saved!</span>
            )}
          </section>

          {/* Pet Details continued */}
          <section className="bg-white rounded-2xl shadow-sm p-5 space-y-4 border border-gray-100 mt-4">
            <div className="space-y-3">
              <label className="block">
                <span className="text-sm font-medium text-gray-900">What is your pet's name? <span className="text-red-500">*</span></span>
                <input
                  type="text"
                  value={localPetName}
                  onChange={(e) => setLocalPetName(e.target.value)}
                  placeholder="e.g., Bella"
                  required
                  className="mt-1 w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                />
                {nameError && <span className="text-xs text-red-500">{nameError}</span>}
              </label>
              <label className="block">
                <span className="text-sm font-medium text-gray-900">Pet's Weight <span className="text-red-500">*</span></span>
                <div className="flex gap-2 mt-1">
                  <input
                    type="number"
                    min="0"
                    value={weight}
                    onChange={(e) => setWeight(e.target.value)}
                    placeholder={weightUnit === 'kg' ? 'e.g., 32' : 'e.g., 70'}
                    className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                  />
                  <select
                    value={weightUnit}
                    onChange={e => setWeightUnit(e.target.value as 'kg' | 'lb')}
                    className="rounded-xl border border-gray-200 bg-white px-2 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                  >
                    <option value="kg">kg</option>
                    <option value="lb">lb</option>
                  </select>
                </div>
                {weightError && <span className="text-xs text-red-500">{weightError}</span>}
              </label>
              <label className="block">
                <span className="text-sm font-medium text-gray-900">Allergies (if any) <span className="text-red-500">*</span></span>
                <input
                  type="text"
                  value={allergies}
                  onChange={(e) => setAllergies(e.target.value)}
                  placeholder="e.g., Chicken, pollen, none"
                  className="mt-1 w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                />
                {allergiesError && <span className="text-xs text-red-500">{allergiesError}</span>}
              </label>
            <div className="space-y-1">
              <span className="text-sm font-medium text-gray-900">Species <span className="text-red-500">*</span></span>
              <div className="grid grid-cols-2 gap-2">
                {["Dog", "Cat"].map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setSpecies(option as "Dog" | "Cat")}
                    className={`rounded-xl border px-3 py-2 text-sm font-semibold transition shadow-sm ${
                      species === option
                        ? "border-blue-500 bg-blue-50 text-blue-700"
                        : "border-gray-200 bg-white text-gray-700"
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
              {speciesError && <span className="text-xs text-red-500">{speciesError}</span>}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="text-sm font-medium text-gray-900">Age (years) <span className="text-red-500">*</span></span>
                <input
                  type="number"
                  min={0}
                  value={age}
                  onChange={(e) => setAge(Number(e.target.value))}
                  className="mt-1 w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                />
                {ageError && <span className="text-xs text-red-500">{ageError}</span>}
              </label>
              <label className="block">
                <span className="text-sm font-medium text-gray-900">Breed <span className="text-red-500">*</span></span>
                <input
                  type="text"
                  value={breed}
                  onChange={(e) => setBreed(e.target.value)}
                  placeholder="e.g., Labrador"
                  className="mt-1 w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                />
                {breedError && <span className="text-xs text-red-500">{breedError}</span>}
              </label>
            </div>
            <div className="space-y-1">
              <span className="text-sm font-medium text-gray-900">Sex <span className="text-red-500">*</span></span>
              <div className="grid grid-cols-3 gap-2">
                {["Male", "Female", "Unknown"].map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setSex(option as "Male" | "Female" | "Unknown")}
                    className={`rounded-xl border px-3 py-2 text-sm font-semibold transition shadow-sm ${
                      sex === option
                        ? "border-blue-500 bg-blue-50 text-blue-700"
                        : "border-gray-200 bg-white text-gray-700"
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
              {sexError && <span className="text-xs text-red-500">{sexError}</span>}
            </div>
          </div>
          </section>

        {/* Spay/Neuter + Heat */}
        <section className="bg-white rounded-2xl shadow-sm p-5 space-y-3 border border-gray-100">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Spay/Neuter + Heat cycle <span className="text-red-500">*</span></h2>
            <p className="text-sm text-gray-500">Required</p>
          </div>
          <div className="space-y-2">
            {["Yes", "No", "Unknown"].map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setSpayStatus(option as "Yes" | "No" | "Unknown")}
                className={`rounded-xl border px-3 py-2 text-sm font-semibold transition shadow-sm ${
                  spayStatus === option
                    ? "border-blue-500 bg-blue-50 text-blue-700"
                    : "border-gray-200 bg-white text-gray-700"
                }`}
              >
                {option}
              </button>
            ))}
            {spayStatusError && <span className="text-xs text-red-500">{spayStatusError}</span>}
          </div>
          {heatCycleVisible && (
            <div className="space-y-2">
              <span className="text-sm font-medium text-gray-900">When was her last heat cycle? <span className="text-red-500">*</span></span>
              <div className="relative">
                <select
                  value={heatCycle}
                  onChange={(e) => setHeatCycle(e.target.value)}
                  className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                >
                  {heatOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
                {heatCycleError && <span className="text-xs text-red-500">{heatCycleError}</span>}
              </div>
            </div>
          )}
        </section>

        {/* Vaccination Status */}
        <section className="bg-white rounded-2xl shadow-sm p-5 space-y-3 border border-gray-100">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Vaccination status <span className="text-red-500">*</span></h2>
            <p className="text-sm text-gray-500">Required</p>
          </div>
          <div className="space-y-2">
            <div className="space-y-2">
              {vaccinationOptions.map((option) => (
                <label
                  key={option}
                  className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition hover:border-blue-300"
                >
                  <input
                    type="radio"
                    name="vaccination"
                    value={option}
                    checked={vaccination === option}
                    onChange={() => setVaccination(option)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                  />
                  <span>{option}</span>
                </label>
              ))}
              {vaccinationError && <span className="text-xs text-red-500">{vaccinationError}</span>}
            </div>
          </div>
        </section>

        {/* Lifestyle */}
        <section className="bg-white rounded-2xl shadow-sm p-5 space-y-3 border border-gray-100">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Lifestyle / Environment <span className="text-red-500">*</span></h2>
            <p className="text-sm text-gray-500">Required</p>
          </div>
          <div className="space-y-2">
            <div className="space-y-2">
              {lifestyleOptions.map((option) => (
                <label
                  key={option}
                  className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition hover:border-blue-300"
                >
                  <input
                    type="radio"
                    name="lifestyle"
                    value={option}
                    checked={lifestyle === option}
                    onChange={() => setLifestyle(option)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                  />
                  <span>{option}</span>
                </label>
              ))}
              {lifestyleError && <span className="text-xs text-red-500">{lifestyleError}</span>}
            </div>
          </div>
        </section>

        {/* Medical History Flags */}
        <section className="bg-white rounded-2xl shadow-sm p-5 space-y-3 border border-gray-100">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Medical history flags <span className="text-red-500">*</span></h2>
            <p className="text-sm text-gray-500">Required • Select all that apply</p>
          </div>
          <div className="space-y-2">
            <div className="space-y-2">
              {historyOptions.map((flag) => (
                <label
                  key={flag}
                  className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition hover:border-blue-300"
                >
                  <input
                    type="checkbox"
                    checked={historyFlags.includes(flag)}
                    onChange={() => toggleFlag(flag)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                  />
                  <span>{flag}</span>
                </label>
              ))}
              {historyFlagsError && <span className="text-xs text-red-500">{historyFlagsError}</span>}
            </div>
            <p className="text-xs text-gray-500">These help us assess risk factors.</p>
          </div>
        </section>

          {/* Primary Action */}
          <section className="space-y-2">
            <button
              type="submit"
              className="w-full rounded-2xl bg-blue-600 px-4 py-3 text-center text-white text-base font-semibold shadow-md hover:bg-blue-700 active:scale-[0.99] transition"
            >
              Let’s begin 🐾
            </button>
          
          </section>
        </form>

        {/* Safety Disclaimer */}
        <section className="bg-amber-50 border border-amber-200 text-amber-900 rounded-2xl p-4 shadow-sm">
          <p className="text-sm font-semibold">Safety first</p>
          <p className="text-sm mt-1">
            If your pet has trouble breathing, collapses, has seizures, or heavy bleeding, seek emergency veterinary care immediately.
          </p>
        </section>
      </div>
    </main>
  );
}
