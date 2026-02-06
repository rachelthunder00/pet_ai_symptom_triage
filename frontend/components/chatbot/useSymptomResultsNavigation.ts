// Utility to navigate to the results page after chat submission
import { useRouter } from "next/navigation";

export function useSymptomResultsNavigation() {
  const router = useRouter();
  function goToResults(resultData?: any) {
    // Optionally pass data via query params or state
    router.push("/symptom-assistant/results");
  }
  return { goToResults };
}
