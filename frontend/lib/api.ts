/**
 * Pet Triage API Client
 * =====================
 * 
 * Type-safe API client for communicating with the Python backend.
 * Handles all HTTP requests to the pet triage service.
 */

// =============================================================================
// Configuration
// =============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// =============================================================================
// Types
// =============================================================================

export type RiskLevel = 'ER' | 'TODAY' | 'SOON' | 'MONITOR';

export type SymptomCategory =
  | 'Toxic Ingestion & Poisoning'
  | 'Stomach Upset'
  | 'Itching & Skin Issues'
  | 'Injury & Bleeding'
  | 'Concerning Behaviour Changes'
  | 'Ears, Eyes, and Mouth'
  | 'Breathing Issues'
  | 'Urinary & Genital'
  | 'Something Else';

export interface PetProfile {
  name?: string;
  species: 'dog' | 'cat';
  breed?: string;
  age?: string;
  weight?: string;
  sex?: string;
  known_conditions?: string[];
}

export interface NearbyVet {
  name: string;
  address?: string;
  phone?: string;
  website?: string;
  distance_km?: number;
  is_emergency_clinic: boolean;
  location?: { lat: number; lng: number };
}

export interface TriageResponse {
  risk_level: RiskLevel;
  category: SymptomCategory;
  red_flags: string[];
  reasoning_summary: string[];
  recommended_actions: string[];
  what_to_monitor: string[];
  follow_up_questions: string[];
  nearby_vets?: NearbyVet[];
  disclaimer: string;
}

export interface APIResponse {
  success: boolean;
  trace_id: string;
  timestamp: string;
  processing_time_ms: number;
  data?: TriageResponse;
  error_code?: string;
  error_message?: string;
  warnings: string[];
  is_er: boolean;
}

export interface TriageRequest {
  species: 'dog' | 'cat';
  category: SymptomCategory;
  structured_fields?: Record<string, string | boolean | number>;
  user_description: string;
  pet_profile?: PetProfile;
  image_base64?: string;
  image_type?: string;
  latitude?: number;
  longitude?: number;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  pet_context?: Record<string, unknown>;
  history?: Array<{ role: 'user' | 'assistant'; content: string }>;
}

export interface ChatResponse {
  success: boolean;
  trace_id: string;
  timestamp: string;
  processing_time_ms: number;
  response: string;
  tools_used?: string[];
  error?: string;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Submit a triage assessment request
 */
export async function submitTriage(request: TriageRequest): Promise<APIResponse> {
  const response = await fetch(`${API_BASE_URL}/api/triage`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Send a chat message for general pet health questions
 */
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get supported symptom categories
 */
export async function getCategories(): Promise<{
  categories: SymptomCategory[];
  species: string[];
}> {
  const response = await fetch(`${API_BASE_URL}/api/categories`);

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Check API health
 */
export async function checkHealth(): Promise<{
  status: string;
  service: string;
  timestamp: string;
  version: string;
}> {
  const response = await fetch(`${API_BASE_URL}/api/health`);

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  return response.json();
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Get color class for risk level
 */
export function getRiskLevelColor(riskLevel: RiskLevel): string {
  switch (riskLevel) {
    case 'ER':
      return 'bg-red-600 text-white';
    case 'TODAY':
      return 'bg-orange-500 text-white';
    case 'SOON':
      return 'bg-yellow-500 text-gray-900';
    case 'MONITOR':
      return 'bg-green-500 text-white';
    default:
      return 'bg-gray-500 text-white';
  }
}

/**
 * Get human-readable label for risk level
 */
export function getRiskLevelLabel(riskLevel: RiskLevel): string {
  switch (riskLevel) {
    case 'ER':
      return '🚨 EMERGENCY - Go to vet NOW';
    case 'TODAY':
      return '⚠️ URGENT - See vet today';
    case 'SOON':
      return '📅 Schedule vet visit within 24-48hrs';
    case 'MONITOR':
      return '✅ Monitor at home';
    default:
      return 'Unknown';
  }
}

/**
 * Convert image file to base64
 */
export async function imageToBase64(file: File): Promise<{ base64: string; type: string }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      // Remove the data URL prefix (e.g., "data:image/jpeg;base64,")
      const base64 = result.split(',')[1];
      resolve({ base64, type: file.type });
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

/**
 * Get user's current location
 */
export function getCurrentLocation(): Promise<{ latitude: number; longitude: number }> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not supported'));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
      },
      (error) => {
        reject(error);
      },
      { timeout: 10000, enableHighAccuracy: false }
    );
  });
}

// =============================================================================
// Symptom Categories Data
// =============================================================================

export const SYMPTOM_CATEGORIES: { id: SymptomCategory; label: string; icon: string }[] = [
  { id: 'Toxic Ingestion & Poisoning', label: 'Poisoning / Toxic', icon: '☠️' },
  { id: 'Stomach Upset', label: 'Stomach Issues', icon: '🤢' },
  { id: 'Itching & Skin Issues', label: 'Skin & Itching', icon: '🔴' },
  { id: 'Injury & Bleeding', label: 'Injury / Bleeding', icon: '🩹' },
  { id: 'Concerning Behaviour Changes', label: 'Behavior Changes', icon: '😰' },
  { id: 'Ears, Eyes, and Mouth', label: 'Eyes / Ears / Mouth', icon: '👁️' },
  { id: 'Breathing Issues', label: 'Breathing Problems', icon: '😮‍💨' },
  { id: 'Urinary & Genital', label: 'Urinary Issues', icon: '💧' },
  { id: 'Something Else', label: 'Other Symptoms', icon: '❓' },
];
