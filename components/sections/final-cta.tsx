import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArcMotif } from "@/components/arc-motif";
import { finalCta } from "@/lib/content";

export function FinalCta() {
  return (
    <section className="relative mx-auto max-w-6xl overflow-hidden px-4 py-20 sm:px-6 sm:py-24">
      <ArcMotif className="pointer-events-none absolute -left-20 -bottom-20 h-[360px] w-[360px]" />
      <div className="relative rounded-3xl border border-border/70 bg-card px-6 py-14 text-center sm:px-12">
        <h2 className="text-balance font-heading text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
          {finalCta.title}
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-pretty text-muted-foreground">
          {finalCta.subtitle}
        </p>
        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Button variant="accent" size="lg" className="h-12 rounded-full px-7 text-base" asChild>
            <Link href="#top">{finalCta.primaryCta}</Link>
          </Button>
          <Button variant="outline" size="lg" className="h-12 rounded-full px-7 text-base" asChild>
            <Link href="#faq">{finalCta.secondaryCta}</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
