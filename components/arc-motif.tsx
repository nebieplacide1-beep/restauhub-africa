import { cn } from "@/lib/utils";

/**
 * Motif d'arcs concentriques repris du logo RestauHub Africa.
 * Purement décoratif — utilisé en fond de section pour ancrer l'identité
 * visuelle sans recourir à une imagerie générique.
 */
export function ArcMotif({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 200 200"
      aria-hidden="true"
      className={cn("pointer-events-none select-none", className)}
    >
      <circle
        cx="100"
        cy="100"
        r="94"
        fill="none"
        stroke="var(--color-accent-500)"
        strokeWidth="3"
        strokeLinecap="round"
        strokeDasharray="410 180"
        transform="rotate(-40 100 100)"
        opacity="0.35"
      />
      <circle
        cx="100"
        cy="100"
        r="76"
        fill="none"
        stroke="var(--color-brand-500)"
        strokeWidth="3"
        strokeLinecap="round"
        strokeDasharray="330 148"
        transform="rotate(60 100 100)"
        opacity="0.4"
      />
      <circle
        cx="100"
        cy="100"
        r="58"
        fill="none"
        stroke="var(--color-gold-500)"
        strokeWidth="3"
        strokeLinecap="round"
        strokeDasharray="250 114"
        transform="rotate(160 100 100)"
        opacity="0.45"
      />
    </svg>
  );
}
