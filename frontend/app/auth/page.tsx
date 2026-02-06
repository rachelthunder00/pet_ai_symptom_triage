"use client";

import { useState } from "react";
import { useAuth } from "../../components/AuthContext";
import { dispatchPetInfoUpdated } from "../../components/PetContext";

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export default function AuthPage() {
  const [isSignUp, setIsSignUp] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, isLoading: authLoading } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email.trim() || !password.trim() || (isSignUp && !name.trim())) {
      setError("Please fill in all required fields.");
      return;
    }
    
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    
    setError("");
    setLoading(true);
    
    try {
      const endpoint = isSignUp ? '/api/auth/register' : '/api/auth/login';
      const body = isSignUp 
        ? { name: name.trim(), email: email.trim(), password }
        : { email: email.trim(), password };
      
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      
      const data = await response.json();
      
      if (data.success && data.token) {
        // Store pet profile if returned (on login)
        if (data.pet_profile) {
          localStorage.setItem('petSpecies', data.pet_profile.species || '');
          localStorage.setItem('petBreed', data.pet_profile.breed || '');
          localStorage.setItem('petName', data.pet_profile.name || '');
          localStorage.setItem('petAge', data.pet_profile.age_years?.toString() || '');
          localStorage.setItem('petWeight', data.pet_profile.weight?.toString() || '');
          localStorage.setItem('petWeightUnit', data.pet_profile.weight_unit || 'kg');
          
          // Notify PetContext about the update
          dispatchPetInfoUpdated();
        }
        // Use AuthContext login - it handles redirect
        login(data.token, data.user);
      } else {
        setError(data.error || 'Authentication failed');
      }
    } catch (err) {
      setError('Could not connect to server. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Show loading while checking auth state
  if (authLoading) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-lg p-8 space-y-6 border border-gray-100">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">🐾 Fuzzy Friend</h1>
          <p className="text-gray-500 text-sm">AI-powered pet health assistant</p>
        </div>
        
        <h2 className="text-xl font-semibold text-gray-900 text-center">
          {isSignUp ? "Create Account" : "Welcome Back"}
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {isSignUp && (
            <label className="block">
              <span className="text-sm font-medium text-gray-900">Name</span>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                className="mt-1 w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                placeholder="Your name"
                disabled={loading}
              />
            </label>
          )}
          <label className="block">
            <span className="text-sm font-medium text-gray-900">Email</span>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="mt-1 w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              placeholder="you@email.com"
              disabled={loading}
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-gray-900">Password</span>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="mt-1 w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              placeholder="••••••••"
              disabled={loading}
            />
          </label>
          
          {error && (
            <div className="text-sm text-red-500 text-center bg-red-50 rounded-lg p-2">
              {error}
            </div>
          )}
          
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-2xl bg-blue-600 px-4 py-3 text-center text-white text-base font-semibold shadow-md hover:bg-blue-700 active:scale-[0.99] transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-spin">⏳</span>
                {isSignUp ? 'Creating account...' : 'Signing in...'}
              </span>
            ) : (
              isSignUp ? "Create Account" : "Sign In"
            )}
          </button>
        </form>
        
        <div className="text-center text-sm text-gray-600">
          {isSignUp ? (
            <>
              Already have an account?{' '}
              <button 
                className="text-blue-600 font-bold hover:underline" 
                onClick={() => { setIsSignUp(false); setError(''); }}
                disabled={loading}
              >
                Sign In
              </button>
            </>
          ) : (
            <>
              New here?{' '}
              <button 
                className="text-blue-600 font-bold hover:underline" 
                onClick={() => { setIsSignUp(true); setError(''); }}
                disabled={loading}
              >
                Create an account
              </button>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
