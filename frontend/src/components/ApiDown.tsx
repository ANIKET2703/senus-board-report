"use client";
import { CloudOff } from "lucide-react";

/** Shown when the reporting API can't be reached (network drop, instance waking). */
export default function ApiDown() {
  return (
    <div className="panel mx-auto mt-12 max-w-md p-6 text-center">
      <CloudOff className="mx-auto h-6 w-6 text-[var(--warn)]" />
      <p className="mt-3 font-medium">The reporting service is unreachable</p>
      <p className="subtle mt-2 text-sm">
        The underlying data and validations are unaffected - the connection may
        just need a moment.
      </p>
      <button onClick={() => window.location.reload()}
        className="mt-4 rounded-lg bg-[var(--accent)] px-4 py-2 text-sm text-white hover:opacity-90">
        Retry
      </button>
    </div>
  );
}
