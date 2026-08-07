import { howItWorks } from "@/lib/content";

export function HowItWorks() {
  return (
    <section id="comment-ca-marche" className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="font-heading text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
          Opérationnel en un après-midi, pas en un trimestre
        </h2>
        <p className="mt-4 text-pretty text-muted-foreground">
          Pensé pour être facile à prendre en main, sans formation technique préalable.
        </p>
      </div>

      <ol className="mt-14 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
        {howItWorks.map((item, index) => (
          <li key={item.step} className="relative pl-1">
            <span className="font-heading text-4xl font-extrabold text-brand-100">
              {item.step}
            </span>
            <h3 className="mt-3 font-heading text-lg font-semibold text-foreground">
              {item.title}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              {item.description}
            </p>
            {index < howItWorks.length - 1 && (
              <span
                aria-hidden="true"
                className="absolute top-5 left-full hidden h-px w-8 bg-border lg:block"
              />
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
