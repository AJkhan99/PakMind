/**
 * Smart intent-based query router.
 *
 * Analyzes a user query and determines which PakMind module backend
 * should handle it: PakGuide, PakWatch, or PakScholar.
 */

import type { ModuleName } from "./api";

/* ── Keyword sets for each module ── */

const GUIDE_KEYWORDS = [
  // English
  "passport", "cnic", "nicop", "domicile", "driving licence", "driving license",
  "birth certificate", "death certificate", "marriage certificate", "nikah",
  "police character", "police clearance", "vehicle registration",
  "nadra", "dgip", "fbr", "tax return", "ntn",
  "arms licence", "arms license", "firearm",
  "government job", "css exam", "pms exam",
  "pension", "eoBI", "provident fund",
  "land record", "fard", "inteqal", "mutation",
  "utility bill", "electricity connection", "gas connection", "sui gas",
  // Roman Urdu
  "passport banwane", "passport kaise", "cnic kaise", "shanakhti card",
  "domicile kaise", "domisile", "domisail", "rahayshi",
  "driving licence ka", "licence kaise", "license banwa",
  "birth certificate ke", "paidaish", "pidaish",
  "police character kahan", "character certificate",
  "vehicle registration ka", "gari ki registration",
  "tax return kaise", "ntn kaise",
  // Urdu script
  "پاسپورٹ", "شناختی", "ڈومیسائل", "رائیونگ لائسنس", "ڈرائیونگ لائسنس",
  "پیدائش", "وفات", "نکاح", "گاڑی کی رجسٹریشن", "کریکٹر",
];

const WATCH_KEYWORDS = [
  // English
  "update", "updates", "notification", "notifications", "policy", "policies",
  "regulation", "regulations", "announcement", "announcements",
  "new rule", "new rules", "rule change", "law change",
  "petrol price", "fuel price", "oil price", "gas price",
  "interest rate", "sbp rate", "state bank",
  "budget", "fiscal", "tax rate", "tax change",
  "minimum wage", "salary", "pension increase",
  "circular", "gazette", "ordinance", "bill", "act",
  "scheme", "program launch", "initiative",
  "latest", "recent", "today", "this week", "breaking",
  // Roman Urdu
  "naye rates", "nayi policy", "naya rule", "naye rules",
  "hukoomat ne", "government ne", "notification kya",
  "petrol ke rate", "petrol ke naye", "diesel ke rate",
  "budget kya", "budget mein", "tax ka kya",
  "taza", "taaza", "khabar", "khabrein",
  "notifikeshan", "notifikasi",
  // Urdu script
  "تازہ", "نوٹیفکیشن", "حکومتی", "پالیسی", "ریٹ", "پیٹرول",
  "بجٹ", "ٹیکس", "شرح سود", "اسٹیٹ بینک", "گیس ریٹ",
];

const SCHOLAR_KEYWORDS = [
  // English
  "scholarship", "scholarships", "fellowship", "fellowships",
  "internship", "internships", "trainee", "traineeship",
  "eligibility", "eligible", "merit", "need-based",
  "hec", "fulbright", "chevening", "erasmus",
  "study abroad", "higher education", "masters", "phd", "bs",
  "lums", "iba", "nust", "giki",
  "financial aid", "tuition", "fee waiver",
  "peef", "seef", "beef", "cmeef", "ehsaas",
  "student loan", "education loan",
  // Roman Urdu
  "scholarship kaise", "taleemi wazifa", "wazifa",
  "scholarship chahiye", "muft taleem", "free education",
  " eligibility kya", "ahliyat",
  // Urdu script
  "سکالرشمپ", "وظیفہ", "تعلیمی", "میرٹ", "ہائر ایجوکیشن",
  "تعلیم", "اسکالرشپ",
];

/**
 * Detect the target module for a user query.
 * Returns the module name + confidence score.
 */
export function detectModule(query: string): { module: ModuleName; confidence: number } {
  const q = query.toLowerCase();

  let guideScore = 0;
  let watchScore = 0;
  let scholarScore = 0;

  for (const kw of GUIDE_KEYWORDS) {
    if (q.includes(kw.toLowerCase())) guideScore += kw.length;
  }
  for (const kw of WATCH_KEYWORDS) {
    if (q.includes(kw.toLowerCase())) watchScore += kw.length;
  }
  for (const kw of SCHOLAR_KEYWORDS) {
    if (q.includes(kw.toLowerCase())) scholarScore += kw.length;
  }

  const maxScore = Math.max(guideScore, watchScore, scholarScore);

  if (maxScore === 0) {
    // No clear match — default to guide (most general)
    return { module: "guide", confidence: 0.3 };
  }

  const confidence = maxScore / (guideScore + watchScore + scholarScore);

  if (guideScore === maxScore) return { module: "guide", confidence };
  if (watchScore === maxScore) return { module: "watch", confidence };
  return { module: "scholar", confidence };
}

/**
 * Detect if text contains Urdu script.
 */
export function isUrdu(text: string): boolean {
  const urduChars = text.match(/[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF]/g);
  return (urduChars?.length ?? 0) >= 3;
}
