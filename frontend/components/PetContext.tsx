"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";

type PetContextType = {
  petName: string;
  setPetName: (name: string) => void;
  petSpecies: string;
  setPetSpecies: (species: string) => void;
  petBreed: string;
  setPetBreed: (breed: string) => void;
  refreshFromStorage: () => void;
};

const PetContext = createContext<PetContextType | undefined>(undefined);

// Custom event name for pet info updates
const PET_INFO_UPDATED_EVENT = "petInfoUpdated";

// Helper to dispatch pet info updated event
export function dispatchPetInfoUpdated() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(PET_INFO_UPDATED_EVENT));
  }
}

export function PetProvider({ children }: { children: ReactNode }) {
  const [petName, setPetNameState] = useState<string>("your pet");
  const [petSpecies, setPetSpeciesState] = useState<string>("dog");
  const [petBreed, setPetBreedState] = useState<string>("");

  // Function to load from localStorage
  const loadFromStorage = useCallback(() => {
    if (typeof window === "undefined") return;
    
    const storedName = localStorage.getItem("petName");
    const storedSpecies = localStorage.getItem("petSpecies");
    const storedBreed = localStorage.getItem("petBreed");
    
    if (storedName) setPetNameState(storedName);
    if (storedSpecies) setPetSpeciesState(storedSpecies);
    if (storedBreed) setPetBreedState(storedBreed);
  }, []);

  // Load on mount
  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  // Listen for custom pet info updated event
  useEffect(() => {
    if (typeof window === "undefined") return;

    const handlePetInfoUpdated = () => {
      loadFromStorage();
    };

    window.addEventListener(PET_INFO_UPDATED_EVENT, handlePetInfoUpdated);
    window.addEventListener("storage", handlePetInfoUpdated);

    return () => {
      window.removeEventListener(PET_INFO_UPDATED_EVENT, handlePetInfoUpdated);
      window.removeEventListener("storage", handlePetInfoUpdated);
    };
  }, [loadFromStorage]);

  // Wrapper to also save to localStorage
  const setPetName = (name: string) => {
    setPetNameState(name);
    if (typeof window !== "undefined") {
      localStorage.setItem("petName", name);
    }
  };

  const setPetSpecies = (species: string) => {
    setPetSpeciesState(species);
    if (typeof window !== "undefined") {
      localStorage.setItem("petSpecies", species);
    }
  };

  const setPetBreed = (breed: string) => {
    setPetBreedState(breed);
    if (typeof window !== "undefined") {
      localStorage.setItem("petBreed", breed);
    }
  };

  return (
    <PetContext.Provider value={{ 
      petName, setPetName, 
      petSpecies, setPetSpecies, 
      petBreed, setPetBreed,
      refreshFromStorage: loadFromStorage
    }}>
      {children}
    </PetContext.Provider>
  );
}

export function usePet() {
  const context = useContext(PetContext);
  if (!context) {
    throw new Error("usePet must be used within a PetProvider");
  }
  return context;
}
