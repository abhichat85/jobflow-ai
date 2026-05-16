"use client";
import { useState, useEffect, useRef } from "react";
import { startLinkedInAuth, getLinkedInAuthStatus } from "@/lib/api";

type AuthStatus = "idle" | "waiting" | "connected" | "timeout" | "error";

interface LinkedInAuthStepProps {
  onComplete: () => void;
}

export function LinkedInAuthStep({ onComplete }: LinkedInAuthStepProps) {
  const [status, setStatus] = useState<AuthStatus>("idle");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  useEffect(() => {
    return () => clearPolling(); // cleanup on unmount
  }, []);

  useEffect(() => {
    if (!sessionId || status !== "waiting") return;

    intervalRef.current = setInterval(async () => {
      try {
        const result = await getLinkedInAuthStatus(sessionId);
        if (result.status !== "waiting") {
          clearPolling();
          setStatus(result.status as AuthStatus);
          if (result.status === "connected") {
            // Small delay so user sees the success state before advancing
            setTimeout(onComplete, 1500);
          }
        }
      } catch {
        clearPolling();
        setStatus("error");
      }
    }, 2000);

    return () => clearPolling();
  }, [sessionId, status, onComplete]);

  const handleStartAuth = async () => {
    setStatus("waiting");
    try {
      const { session_id } = await startLinkedInAuth();
      setSessionId(session_id);
    } catch {
      setStatus("error");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Connect LinkedIn</h2>
        <p className="mt-1 text-sm text-gray-500">
          We need access to LinkedIn to find matching jobs.
        </p>
      </div>

      <div className="flex flex-col items-center gap-6 rounded-xl border border-gray-200 bg-gray-50 py-10 px-8 text-center">
        {/* LinkedIn logo */}
        <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-[#0077b5] text-2xl font-bold text-white">
          in
        </div>

        {status === "idle" && (
          <>
            <div>
              <p className="font-medium text-gray-800">Log into LinkedIn</p>
              <p className="mt-1 text-sm text-gray-500">
                A browser window will open. Log in normally — the app captures
                your session automatically.
              </p>
            </div>
            <button
              onClick={handleStartAuth}
              className="rounded-lg bg-[#0077b5] px-6 py-3 text-sm font-semibold text-white hover:bg-[#005f8f] transition-colors"
            >
              🔗 Open LinkedIn Login Window
            </button>
            <p className="text-xs text-gray-400">
              Works with 2FA · CAPTCHA · SSO · No passwords stored
            </p>
          </>
        )}

        {status === "waiting" && (
          <>
            <div>
              <p className="font-medium text-gray-800">Waiting for login…</p>
              <p className="mt-1 text-sm text-gray-500">
                Complete login in the Chromium window, then come back here.
              </p>
            </div>
            <div className="flex items-center gap-2 text-sm text-amber-600">
              <span className="inline-block h-2.5 w-2.5 animate-pulse rounded-full bg-amber-400" />
              Watching for LinkedIn session…
            </div>
            <p className="text-xs text-gray-400">
              Window will close automatically when done (5-minute timeout)
            </p>
          </>
        )}

        {status === "connected" && (
          <>
            <div className="flex items-center gap-2 text-green-600">
              <span className="text-2xl">✅</span>
              <span className="font-semibold">LinkedIn Connected!</span>
            </div>
            <p className="text-sm text-gray-500">
              Session captured successfully. Moving to next step…
            </p>
          </>
        )}

        {status === "timeout" && (
          <>
            <div className="text-amber-600">
              <p className="font-medium">Login window timed out</p>
              <p className="mt-1 text-sm text-gray-500">
                The 5-minute window expired. Please try again.
              </p>
            </div>
            <button
              onClick={handleStartAuth}
              className="rounded-lg bg-[#0077b5] px-6 py-3 text-sm font-semibold text-white hover:bg-[#005f8f]"
            >
              🔗 Try Again
            </button>
          </>
        )}

        {status === "error" && (
          <>
            <div className="text-red-600">
              <p className="font-medium">Something went wrong</p>
              <p className="mt-1 text-sm text-gray-500">
                The backend may not be running. Check the backend logs.
              </p>
            </div>
            <button
              onClick={handleStartAuth}
              className="rounded-lg bg-gray-700 px-6 py-3 text-sm font-semibold text-white hover:bg-gray-800"
            >
              Retry
            </button>
          </>
        )}
      </div>
    </div>
  );
}
