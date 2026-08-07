import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArcMotif } from "@/components/arc-motif";
import { hero } from "@/lib/content";

export function Hero() {
  return (
    <section id="top" className="relative overflow-hidden bg-arc-pattern">
      <ArcMotif className="pointer-events-none absolute -right-24 -top-24 h-[420px] w-[420px] sm:-right-16 sm:-top-16" />

      <div className="relative mx-auto flex max-w-4xl flex-col items-center px-4 pt-20 pb-16 text-center sm:px-6 sm:pt-28 sm:pb-24">
        <Badge
          variant="outline"
          className="animate-in fade-in slide-in-from-bottom-2 h-auto rounded-full border-brand-200 bg-brand-50 px-4 py-1.5 text-brand-700 duration-700"
        >
          {hero.eyebrow}
        </Badge>

        <h1 className="animate-in fade-in slide-in-from-bottom-4 mt-6 text-balance font-heading text-4xl font-extrabold tracking-tight text-foreground duration-700 sm:text-6xl">
          {hero.title}
        </h1>

        <p className="animate-in fade-in slide-in-from-bottom-4 mt-6 max-w-2xl text-pretty text-lg leading-relaxed text-muted-foreground duration-700 [animation-delay:100ms]">
          {hero.subtitle}
        </p>

        <div className="animate-in fade-in slide-in-from-bottom-4 mt-9 flex flex-col items-center gap-3 duration-700 [animation-delay:150ms] sm:flex-row">
          <Button variant="accent" size="lg" className="h-12 rounded-full px-7 text-base" asChild>
            <Link href="#comment-ca-marche">
              {hero.primaryCta}
              <ArrowRight className="size-4" data-icon="inline-end" />
            </Link>
          </Button>
          <Button variant="outline" size="lg" className="h-12 rounded-full px-7 text-base" asChild>
            <Link href="#modules">{hero.secondaryCta}</Link>
          </Button>
        </div>

        <dl className="animate-in fade-in slide-in-from-bottom-4 mt-16 grid w-full grid-cols-1 gap-6 border-t border-border/70 pt-10 duration-700 [animation-delay:200ms] sm:grid-cols-3">
          {hero.stats.map((stat) => (
            <div key={stat.label} className="flex flex-col items-center gap-1">
              <dt className="font-heading text-3xl font-extrabold text-brand-600">
                {stat.value}
              </dt>
              <dd className="text-sm text-muted-foreground">{stat.label}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
