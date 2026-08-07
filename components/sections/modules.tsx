import {
  BarChart3,
  ClipboardList,
  Gift,
  Store,
  Truck,
  UtensilsCrossed,
  type LucideIcon,
} from "lucide-react";
import { modules } from "@/lib/content";

const icons: Record<string, LucideIcon> = {
  UtensilsCrossed,
  ClipboardList,
  Truck,
  Store,
  Gift,
  BarChart3,
};

export function Modules() {
  return (
    <section id="modules" className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="font-heading text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
          Tout ce qu&apos;il faut pour gérer un établissement, réuni au même endroit
        </h2>
        <p className="mt-4 text-pretty text-muted-foreground">
          Plus besoin de multiplier les abonnements et les outils qui ne se parlent pas entre eux.
        </p>
      </div>

      <div className="mt-14 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {modules.map((mod, index) => {
          const Icon = icons[mod.icon];
          const featured = index === 0;
          return (
            <div
              key={mod.title}
              className={`group relative overflow-hidden rounded-2xl border border-border/70 bg-card p-6 transition-colors hover:border-brand-300 ${
                featured ? "sm:col-span-2 lg:col-span-1 lg:row-span-1" : ""
              }`}
            >
              <div className="flex size-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600 transition-colors group-hover:bg-brand-500 group-hover:text-white">
                <Icon className="size-5" />
              </div>
              <h3 className="mt-5 font-heading text-lg font-semibold text-foreground">
                {mod.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {mod.description}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
