import { commission } from "@/lib/content";

export function Commission() {
  return (
    <section id="commission" className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
      <div className="grid gap-10 rounded-3xl border border-border/70 bg-brand-900 px-6 py-12 text-white sm:px-12 sm:py-16 lg:grid-cols-[1.1fr_1fr] lg:items-center">
        <div>
          <h2 className="text-balance font-heading text-3xl font-bold tracking-tight sm:text-4xl">
            {commission.title}
          </h2>
          <p className="mt-5 max-w-xl text-pretty leading-relaxed text-brand-100">
            {commission.description}
          </p>
        </div>

        <div className="grid grid-cols-3 gap-4 lg:gap-6">
          {commission.points.map((point) => (
            <div
              key={point.label}
              className="rounded-2xl border border-white/10 bg-white/5 p-4 text-center sm:p-6"
            >
              <div className="font-heading text-2xl font-extrabold text-gold-400 sm:text-3xl">
                {point.value}
              </div>
              <div className="mt-2 text-xs leading-snug text-brand-100 sm:text-sm">
                {point.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
