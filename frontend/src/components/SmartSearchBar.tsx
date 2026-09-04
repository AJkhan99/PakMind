"use client";

import { useState, useRef, useCallback, useEffect, type FormEvent } from "react";
import { motion } from "framer-motion";
import {
  HiOutlineMagnifyingGlass,
  HiOutlineSparkles,
  HiOutlineMicrophone,
} from "react-icons/hi2";
import { detectModule, isUrdu } from "@/lib/smartSearch";
import { queryGuide, queryWatch, queryScholar } from "@/lib/api";
import type { ModuleName, GuideResponse, WatchResponse, ScholarResponse } from "@/lib/api";

interface SmartSearchBarProps {
  onResult: (
    module: ModuleName,
    data: GuideResponse | WatchResponse | ScholarResponse
  ) => void;
  onError: (error: string) => void;
  onLoading: (loading: boolean) => void;
}

const PLACEHOLDERS = [
  "Ask anything about Pakistan... e.g. How do I get a passport?",
  "Sawal poochein... e.g. domicile kaise banwayen?",
  "پاکستان کے بارے میں کچھ بھی پوچھیں...",
];

export default function SmartSearchBar({
  onResult,
  onError,
  onLoading,
}: SmartSearchBarProps) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [placeholderIdx, setPlaceholderIdx] = useState(0);
  const [listening, setListening] = useState(false);
  const [voiceLang, setVoiceLang] = useState<"en-PK" | "ur-PK">("en-PK");
  const recognitionRef = useRef<unknown>(null);

  // Cycle placeholders
  useEffect(() => {
    const interval = setInterval(() => {
      setPlaceholderIdx((prev) => (prev + 1) % PLACEHOLDERS.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = useCallback(
    async (e?: FormEvent) => {
      if (e) e.preventDefault();
      const q = query.trim();
      if (!q || loading) return;

      setLoading(true);
      onLoading(true);
      onError("");

      try {
        const { module } = detectModule(q);
        let data: GuideResponse | WatchResponse | ScholarResponse;

        switch (module) {
          case "guide":
            data = await queryGuide(q);
            break;
          case "watch":
            data = await queryWatch(q);
            break;
          case "scholar":
            data = await queryScholar(q);
            break;
        }

        onResult(module, data);
      } catch (err) {
        onError(
          err instanceof Error
            ? err.message
            : "Something went wrong. Please try again."
        );
      } finally {
        setLoading(false);
        onLoading(false);
      }
    },
    [query, loading, onResult, onError, onLoading]
  );

  // Voice input
  const toggleVoice = useCallback(() => {
    if (listening && recognitionRef.current) {
      (recognitionRef.current as { stop: () => void }).stop();
      return;
    }

    const SpeechRecognition =
      (window as unknown as Record<string, unknown>).SpeechRecognition ||
      (window as unknown as Record<string, unknown>).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      onError("Speech recognition is not supported. Please use Chrome.");
      return;
    }

    const recognition = new (SpeechRecognition as new () => {
      continuous: boolean;
      interimResults: boolean;
      lang: string;
      onstart: (() => void) | null;
      onend: (() => void) | null;
      onerror: (() => void) | null;
      onresult: ((event: { results: { 0: { 0: { transcript: string } } } }) => void) | null;
      start: () => void;
      stop: () => void;
    })();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = voiceLang;

    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (transcript.trim()) {
        setQuery(transcript.trim());
        // Auto-submit after voice input
        setTimeout(() => {
          setQuery(transcript.trim());
        }, 100);
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, [listening, voiceLang, onError]);

  return (
    <motion.form
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4, duration: 0.5 }}
      className="flex w-full flex-col gap-3 sm:flex-row"
    >
      <div className="relative flex-1">
        <HiOutlineMagnifyingGlass className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={PLACEHOLDERS[placeholderIdx]}
          dir="auto"
          disabled={loading}
          className="glow-input w-full rounded-2xl border border-white/10 bg-white/5 py-4 pl-12 pr-24 text-sm text-white placeholder-slate-500 outline-none backdrop-blur transition-shadow focus:border-brand-green/50 disabled:opacity-50"
        />
        {/* Voice controls inside input */}
        <div className="absolute right-3 top-1/2 flex -translate-y-1/2 items-center gap-1">
          <button
            type="button"
            onClick={() => setVoiceLang(voiceLang === "en-PK" ? "ur-PK" : "en-PK")}
            disabled={loading || listening}
            className="rounded-md bg-white/5 px-2 py-1 text-[10px] font-semibold text-slate-400 ring-1 ring-white/10 hover:text-brand-green disabled:opacity-40"
            title={voiceLang === "en-PK" ? "Switch to Urdu" : "Switch to English"}
          >
            {voiceLang === "en-PK" ? "EN" : "UR"}
          </button>
          <button
            type="button"
            onClick={toggleVoice}
            disabled={loading}
            className={`rounded-lg p-1.5 transition-colors disabled:opacity-40 ${
              listening
                ? "bg-red-500/20 text-red-400 animate-pulse"
                : "bg-white/5 text-slate-400 ring-1 ring-white/10 hover:text-brand-green"
            }`}
            title={listening ? "Stop listening" : "Speak your question"}
          >
            <HiOutlineMicrophone className="h-4 w-4" />
          </button>
        </div>
      </div>

      <button
        type="submit"
        disabled={loading || !query.trim()}
        className="btn-gradient flex items-center justify-center gap-2 rounded-2xl px-8 py-4 text-sm font-semibold text-white disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <HiOutlineSparkles className="h-4 w-4" />
        Ask PakMind
      </button>
    </motion.form>
  );
}
