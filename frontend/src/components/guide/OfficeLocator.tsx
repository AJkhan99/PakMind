"use client";

import { useMemo } from "react";

interface OfficeLocatorProps {
  contactInfo: Record<string, unknown> | {
    phone?: string;
    email?: string;
    address?: string;
    website?: string;
  } | null;
  answer: string;
  query: string;
}

/** Safely extract a string from a possibly-untyped record. */
function str(val: unknown): string | undefined {
  return typeof val === "string" ? val : undefined;
}

const OFFICE_DIRECTORY: Record<string, { offices: { city: string; name: string; address: string; phone?: string }[] }> = {
  passport: {
    offices: [
      { city: "Islamabad", name: "Regional Passport Office Islamabad", address: "DGIP Complex, G-5/2, Islamabad", phone: "051-111-786-100" },
      { city: "Lahore", name: "Regional Passport Office Lahore", address: "Queens Road, Lahore", phone: "042-99211501" },
      { city: "Karachi", name: "Regional Passport Office Karachi", address: "Shahrah-e-Faisal, Karachi", phone: "021-99210041" },
      { city: "Peshawar", name: "Regional Passport Office Peshawar", address: "University Road, Peshawar", phone: "091-9211330" },
      { city: "Quetta", name: "Regional Passport Office Quetta", address: "Jinnah Road, Quetta", phone: "081-9201236" },
    ],
  },
  cnic: {
    offices: [
      { city: "Islamabad", name: "NADRA Mega Center Islamabad", address: "9th Mauve Area, G-9/4, Islamabad", phone: "111-786-100" },
      { city: "Lahore", name: "NADRA Mega Center Lahore", address: "44-A, Jail Road, Lahore", phone: "111-786-100" },
      { city: "Karachi", name: "NADRA Mega Center Karachi", address: "Shahrah-e-Faisal, Karachi", phone: "111-786-100" },
      { city: "Peshawar", name: "NADRA Regional Office Peshawar", address: "University Road, Peshawar", phone: "111-786-100" },
      { city: "Quetta", name: "NADRA Regional Office Quetta", address: "Jinnah Road, Quetta", phone: "111-786-100" },
    ],
  },
  "driving licence": {
    offices: [
      { city: "Lahore", name: "Excise & Taxation Lahore", address: "Qurban Lines, Lahore", phone: "080-02345" },
      { city: "Rawalpindi", name: "Excise & Taxation Rawalpindi", address: "Kachehri Road, Rawalpindi", phone: "051-9290116" },
      { city: "Faisalabad", name: "Excise & Taxation Faisalabad", address: "Civil Secretariat, Faisalabad" },
      { city: "Multan", name: "Excise & Taxation Multan", address: "District Courts Complex, Multan" },
    ],
  },
  domicile: {
    offices: [
      { city: "Lahore", name: "DC Office Lahore", address: "Deputy Commissioner Office, Lahore" },
      { city: "Rawalpindi", name: "DC Office Rawalpindi", address: "Deputy Commissioner Office, Rawalpindi", phone: "051-9290116" },
      { city: "Karachi", name: "DC Office Karachi (South)", address: "DC Complex, Saddar, Karachi" },
      { city: "Peshawar", name: "DC Office Peshawar", address: "Deputy Commissioner Office, Peshawar" },
    ],
  },
  "birth certificate": {
    offices: [
      { city: "Your Area", name: "Local Union Council", address: "Visit your nearest Union Council office" },
    ],
  },
  "marriage certificate": {
    offices: [
      { city: "Your Area", name: "Local Union Council", address: "Visit your nearest Union Council office (Nikah Khawan handles submission)" },
    ],
  },
  "police character certificate": {
    offices: [
      { city: "Lahore", name: "Khidmat Markaz Lahore", address: "Multiple locations across Lahore", phone: "15" },
      { city: "Rawalpindi", name: "Khidmat Markaz Rawalpindi", address: "Near District Courts, Rawalpindi", phone: "15" },
      { city: "Faisalabad", name: "Khidmat Markaz Faisalabad", address: "Near District Courts, Faisalabad", phone: "15" },
    ],
  },
};

export function OfficeLocator({ contactInfo, answer, query }: OfficeLocatorProps) {
  const offices = useMemo(() => {
    const text = (answer + " " + query).toLowerCase();
    for (const [service, data] of Object.entries(OFFICE_DIRECTORY)) {
      if (text.includes(service)) return { service, ...data };
    }
    return null;
  }, [answer, query]);

  const ciPhone = str(contactInfo?.phone);
  const ciAddress = str(contactInfo?.address);

  if (!offices && !contactInfo) return null;

  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3">
      <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
        <svg className="h-4 w-4 text-pakgreen" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        Nearest Offices
      </h3>

      {offices?.offices && (
        <div className="space-y-2">
          {offices.offices.slice(0, 4).map((office, i) => (
            <div key={i} className="rounded-md border border-white/10 bg-white/5 p-3">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-300">{office.name}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{office.address}</p>
                </div>
                <span className="flex-shrink-0 rounded-full bg-blue-500/10 px-2 py-0.5 text-xs text-blue-400 ring-1 ring-blue-500/20">
                  {office.city}
                </span>
              </div>
              {office.phone && (
                <a
                  href={`tel:${office.phone}`}
                  className="mt-1 inline-flex items-center gap-1 text-xs text-pakgreen hover:underline"
                >
                  <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                  </svg>
                  {office.phone}
                </a>
              )}
            </div>
          ))}
        </div>
      )}

      {contactInfo && (
        <div className="rounded-md border border-white/10 bg-white/5 p-3">
          <p className="text-xs font-semibold text-slate-400 mb-1">Direct Contact</p>
          {ciPhone && (
            <p className="text-sm text-slate-300">
              Phone: <a href={`tel:${ciPhone}`} className="text-pakgreen hover:underline">{ciPhone}</a>
            </p>
          )}
          {ciAddress && (
            <p className="text-sm text-slate-300">Address: {ciAddress}</p>
          )}
        </div>
      )}
    </div>
  );
}
