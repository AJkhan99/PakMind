"use client";

import { useState, useCallback, useRef } from "react";

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

export function VoiceInput({ onTranscript, disabled }: VoiceInputProps) {
  const [listening, setListening] = useState(false);
  const [lang, setLang] = useState<"en-PK" | "ur-PK">("en-PK");
  const recognitionRef = useRef<unknown>(null);

  const startListening = useCallback(() => {
    const SpeechRecognition =
      (window as unknown as Record<string, unknown>).SpeechRecognition ||
      (window as unknown as Record<string, unknown>).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in your browser. Please use Chrome.");
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
    recognition.lang = lang;

    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (transcript.trim()) {
        onTranscript(transcript.trim());
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, [lang, onTranscript]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      (recognitionRef.current as { stop: () => void }).stop();
    }
  }, []);

  return (
    <div className="flex items-center gap-1">
      {/* Language toggle */}
      <button
        type="button"
        onClick={() => setLang(lang === "en-PK" ? "ur-PK" : "en-PK")}
        disabled={disabled || listening}
        className="rounded-lg border border-white/10 bg-white/5 px-2 py-1.5 text-xs text-slate-400
                   hover:border-pakgreen/30 hover:text-pakgreen transition-colors
                   disabled:opacity-40"
        title={lang === "en-PK" ? "Switch to Urdu" : "Switch to English"}
      >
        {lang === "en-PK" ? "EN" : "UR"}
      </button>

      {/* Mic button */}
      <button
        type="button"
        onClick={listening ? stopListening : startListening}
        disabled={disabled}
        className={`rounded-lg p-2 transition-colors disabled:opacity-40 ${
          listening
            ? "bg-red-500/20 text-red-400 animate-pulse ring-1 ring-red-500/30"
            : "border border-white/10 bg-white/5 text-slate-400 hover:border-pakgreen/30 hover:text-pakgreen"
        }`}
        title={listening ? "Stop listening" : "Speak your question"}
      >
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
          />
        </svg>
      </button>
    </div>
  );
}

export function speakText(text: string, lang: string = "en-US") {
  if (typeof window === "undefined" || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang;
  utterance.rate = 0.9;
  utterance.pitch = 1;
  window.speechSynthesis.speak(utterance);
}
