import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { nav } from "@/lib/content";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/70 bg-background/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="#top" className="flex items-center gap-2" aria-label="RestauHub Africa — accueil">
          <Image
            src="/logo-full.png"
            alt="RestauHub Africa"
            width={1198}
            height={494}
            priority
            className="h-8 w-auto sm:h-9"
          />
        </Link>

        <nav className="hidden items-center gap-7 md:flex">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <Button variant="accent" size="lg" className="rounded-full px-5" asChild>
          <Link href="#comment-ca-marche">Essayer gratuitement</Link>
        </Button>
      </div>
    </header>
  );
}
