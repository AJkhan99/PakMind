"use client";

import { useState, useMemo } from "react";
import type { GuideResponse } from "@/types/guide";
import { generateChecklistPdf } from "@/lib/api";

interface PrintableChecklistProps {
  data: GuideResponse;
  query: string;
}

const FEE_DATA: Record<string, { keywords: string[]; fees: { label: string; amount: number }[] }> = {
  passport: {
    keywords: ["passport", "pasport", "pass port", "پاسپورٹ"],
    fees: [
      { label: "Normal 5yr (36 pages)", amount: 1750 },
      { label: "Normal 5yr (72 pages)", amount: 2900 },
      { label: "Normal 10yr (36 pages)", amount: 3250 },
      { label: "Normal 10yr (72 pages)", amount: 5400 },
      { label: "Urgent surcharge", amount: 2500 },
    ],
  },
  cnic: {
    keywords: ["cnic", "shanakhti card", "identity card", "شناختی"],
    fees: [
      { label: "Normal CNIC", amount: 115 },
      { label: "Smart NIC (SNIC)", amount: 415 },
      { label: "Urgent SNIC", amount: 760 },
      { label: "Executive SNIC", amount: 1260 },
    ],
  },
  "driving licence": {
    keywords: ["driving licence", "driving license", "drive licence", "driver licence", "ڈرائیونگ لائسنس"],
    fees: [
      { label: "Learner's Licence", amount: 60 },
      { label: "Regular 1 year", amount: 150 },
      { label: "Regular 3 years", amount: 350 },
      { label: "Regular 5 years", amount: 500 },
    ],
  },
  "birth certificate": {
    keywords: ["birth certificate", "birth registration", "پیدائش"],
    fees: [
      { label: "Within 60 days", amount: 75 },
      { label: "Late registration", amount: 350 },
    ],
  },
  "death certificate": {
    keywords: ["death certificate", "death registration", "وفات", "ڈیتھ"],
    fees: [
      { label: "Within 30 days", amount: 50 },
      { label: "Late registration (30 days – 1 year)", amount: 250 },
      { label: "Late registration (1 year+)", amount: 500 },
    ],
  },
  "police character certificate": {
    keywords: ["police character", "character certificate", "police clearance", "کریکٹر"],
    fees: [{ label: "Processing fee", amount: 75 }],
  },
  "marriage certificate": {
    keywords: ["marriage certificate", "nikah nama", "marriage registration", "نکاح", "شادی"],
    fees: [
      { label: "Registration", amount: 150 },
      { label: "Certified copy", amount: 75 },
      { label: "Late penalty", amount: 750 },
    ],
  },
  domicile: {
    keywords: ["domicile", "domisile", "domisail", "ڈومیسائل", "rahayshi"],
    fees: [{ label: "Domicile certificate", amount: 30 }],
  },
  "vehicle registration": {
    keywords: ["vehicle registration", "car registration", "گاڑی کی رجسٹریشن"],
    fees: [
      { label: "New vehicle registration", amount: 5000 },
      { label: "Transfer of ownership", amount: 1500 },
      { label: "Duplicate book", amount: 500 },
    ],
  },
};

function detectService(query: string, answer: string): string | null {
  const q = query.toLowerCase();
  const a = (answer || "").toLowerCase();

  let bestMatch: string | null = null;
  let bestScore = 0;

  for (const [service, data] of Object.entries(FEE_DATA)) {
    for (const kw of data.keywords) {
      if (q.includes(kw.toLowerCase())) {
        const score = kw.length;
        if (score > bestScore) {
          bestScore = score;
          bestMatch = service;
        }
      }
    }
  }

  if (bestMatch) return bestMatch;

  const firstSentence = a.split(/[.!?۔]/)[0] || a;
  for (const [service, data] of Object.entries(FEE_DATA)) {
    for (const kw of data.keywords) {
      if (firstSentence.includes(kw.toLowerCase())) {
        return service;
      }
    }
  }

  for (const service of Object.keys(FEE_DATA)) {
    if (a.includes(service)) return service;
  }

  return null;
}

/** Trigger a browser download from a Blob. */
function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export function PrintableChecklist({ data, query }: PrintableChecklistProps) {
  const [downloading, setDownloading] = useState(false);
  const [selectedFee, setSelectedFee] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const detectedService = useMemo(() => detectService(query, data.answer), [query, data.answer]);

  const serviceFeeOptions = useMemo(() => {
    if (!detectedService) return null;
    const entry = FEE_DATA[detectedService];
    return entry ? { service: detectedService, fees: entry.fees } : null;
  }, [detectedService]);

  const calculatedFee = useMemo(() => {
    if (!selectedFee || !serviceFeeOptions) return null;
    const option = serviceFeeOptions.fees.find((f) => f.label === selectedFee);
    return option ? option.amount : null;
  }, [selectedFee, serviceFeeOptions]);

  async function handleDownload() {
    setDownloading(true);
    setDownloadError(null);
    try {
      const blob = await generateChecklistPdf({
        answer: data.answer,
        requirements: data.requirements,
        steps: data.steps,
        fee: data.fee,
        processing_time: data.processing_time,
        application_method: data.application_method,
        application_url: data.application_url,
        contact_info: data.contact_info || undefined,
        eligibility: data.eligibility,
      });

      // Determine file extension from blob type
      const isPdf = blob.type.includes("pdf");
      const ext = isPdf ? "pdf" : "txt";
      downloadBlob(blob, `pakguide-checklist.${ext}`);
    } catch (err) {
      console.error("PDF download failed:", err);
      setDownloadError("PDF generation failed. Try again or print this page instead.");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="space-y-4 rounded-lg border border-white/10 bg-white/5 p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-300">Printable Checklist</h3>
        <button
          onClick={handleDownload}
          disabled={downloading}
          className="btn-gradient flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs
                     font-medium text-white disabled:opacity-50"
        >
          <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {downloading ? "Generating..." : "Download PDF"}
        </button>
      </div>

      {downloadError && (
        <p className="text-xs text-red-400">{downloadError}</p>
      )}

      {data.requirements.length > 0 && (
        <div className="space-y-2 text-sm">
          <p className="font-medium text-slate-400">Documents to prepare:</p>
          <ul className="space-y-1">
            {data.requirements.map((req, i) => (
              <li key={i} className="flex items-start gap-2">
                <input type="checkbox" className="mt-0.5 h-4 w-4 rounded border-white/20 bg-white/5 text-pakgreen focus:ring-pakgreen/30" />
                <span className="text-slate-400">{req}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {serviceFeeOptions && (
        <div className="rounded-md border border-white/10 bg-white/5 p-3">
          <p className="text-xs font-semibold text-slate-400 mb-2">Fee Calculator</p>
          <select
            value={selectedFee || ""}
            onChange={(e) => setSelectedFee(e.target.value)}
            className="w-full rounded-md border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-slate-300
                       focus:border-pakgreen/50 focus:outline-none focus:ring-1 focus:ring-pakgreen/30"
          >
            <option value="" className="bg-[#0a1a0f]">Select fee category...</option>
            {serviceFeeOptions.fees.map((f) => (
              <option key={f.label} value={f.label} className="bg-[#0a1a0f]">
                {f.label} — Rs. {f.amount.toLocaleString()}
              </option>
            ))}
          </select>
          {calculatedFee !== null && (
            <div className="mt-2 rounded-md bg-pakgreen/10 p-2 text-center ring-1 ring-pakgreen/20">
              <p className="text-xs text-slate-500">Estimated Fee</p>
              <p className="text-lg font-bold text-pakgreen">
                Rs. {calculatedFee.toLocaleString()}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
