"use client";

import Link from "next/link";

export default function AssessmentReportPage() {
  // In a real app, fetch assessment data here (from context, params, or API)
  // For now, show a simple placeholder report
  return (
    <main className="min-h-screen bg-gray-50 flex flex-col items-center justify-center py-12 px-4">
      <div className="bg-white rounded-2xl shadow-lg p-8 max-w-lg w-full">
        <h1 className="text-2xl font-bold mb-4 text-blue-700" style={{ fontFamily: 'Poppins, var(--font-poppins)' }}>
          Assessment Report
        </h1>
        <p className="text-gray-700 mb-6">
          Here is your pet's assessment summary. (This is a placeholder. Integrate with chat data for real results.)
        </p>
        <ul className="mb-6 text-gray-800 list-disc list-inside">
          <li>Symptom: <span className="font-semibold">Vomiting</span></li>
          <li>Urgency: <span className="font-semibold text-red-600">High</span></li>
          <li>Recommendation: <span className="font-semibold">Visit a vet as soon as possible.</span></li>
        </ul>
        <Link href="/" className="inline-block bg-blue-600 text-white px-6 py-2 rounded-xl font-semibold hover:bg-blue-700 transition" style={{ fontFamily: 'Poppins, var(--font-poppins)' }}>
          Back to Home
        </Link>
      </div>
    </main>
  );
}
