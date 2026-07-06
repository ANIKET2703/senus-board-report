"use client";
/** Route-segment error boundary: a chart or fetch failure degrades to a
 *  recoverable panel instead of a blank screen. */
export default function DashboardError({ error, reset }: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="panel mx-auto mt-12 max-w-md p-6 text-center">
      <p className="font-medium">Something went wrong rendering this view.</p>
      <p className="subtle mt-2 text-sm">
        The underlying data is unaffected - this is a display error.
        {error.digest ? ` (ref ${error.digest})` : ""}
      </p>
      <button onClick={reset}
        className="mt-4 rounded-lg bg-[var(--accent)] px-4 py-2 text-sm text-white hover:opacity-90">
        Try again
      </button>
    </div>
  );
}
