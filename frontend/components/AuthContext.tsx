"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";

interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  hasCompletedOnboarding: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  completeOnboarding: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Routes that don't require authentication
const PUBLIC_ROUTES = ["/auth"];

// Routes that require authentication but not onboarding
const AUTH_ONLY_ROUTES = ["/onboarding"];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  // Check auth state on mount
  useEffect(() => {
    const checkAuth = () => {
      if (typeof window === "undefined") return;

      const storedToken = localStorage.getItem("authToken");
      const storedUser = localStorage.getItem("user");
      const petSpecies = localStorage.getItem("petSpecies");

      if (storedToken && storedUser) {
        try {
          setToken(storedToken);
          setUser(JSON.parse(storedUser));
        } catch {
          // Invalid stored data, clear it
          localStorage.removeItem("authToken");
          localStorage.removeItem("user");
        }
      }

      // Check if onboarding is complete (has pet info)
      setHasCompletedOnboarding(!!petSpecies);
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  // Handle route protection
  useEffect(() => {
    if (isLoading) return;

    const isPublicRoute = PUBLIC_ROUTES.includes(pathname);
    const isAuthOnlyRoute = AUTH_ONLY_ROUTES.includes(pathname);
    const isAuthenticated = !!token;

    // Not authenticated and trying to access protected route
    if (!isAuthenticated && !isPublicRoute) {
      router.replace("/auth");
      return;
    }

    // Authenticated but on auth page - redirect appropriately
    if (isAuthenticated && isPublicRoute) {
      if (hasCompletedOnboarding) {
        router.replace("/");
      } else {
        router.replace("/onboarding");
      }
      return;
    }

    // Authenticated, completed onboarding, but on onboarding page
    if (isAuthenticated && hasCompletedOnboarding && isAuthOnlyRoute) {
      router.replace("/");
      return;
    }

    // Authenticated, hasn't completed onboarding, trying to access main app
    if (isAuthenticated && !hasCompletedOnboarding && !isAuthOnlyRoute && !isPublicRoute) {
      router.replace("/onboarding");
      return;
    }
  }, [isLoading, token, hasCompletedOnboarding, pathname, router]);

  const login = (newToken: string, newUser: User) => {
    localStorage.setItem("authToken", newToken);
    localStorage.setItem("user", JSON.stringify(newUser));
    if (newUser.name) {
      localStorage.setItem("ownerName", newUser.name);
    }
    setToken(newToken);
    setUser(newUser);
  };

  const logout = () => {
    localStorage.removeItem("authToken");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
    router.replace("/auth");
  };

  const completeOnboarding = () => {
    setHasCompletedOnboarding(true);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!token,
        hasCompletedOnboarding,
        login,
        logout,
        completeOnboarding,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
