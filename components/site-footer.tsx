import Image from "next/image";
import Link from "next/link";
import { footer } from "@/lib/content";

export function SiteFooter() {
  return (
    <footer className="border-t border-border/70 bg-neutral-50/60">
      <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
        <div className="grid gap-10 sm:grid-cols-[1.4fr_1fr_1fr]">
          <div>
            <Image
              src="/logo-full.png"
              alt="RestauHub Africa"
              width={1198}
              height={494}
              className="h-8 w-auto"
            />
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-muted-foreground">
              {footer.description}
            </p>
          </div>

          {footer.columns.map((column) => (
            <div key={column.title}>
              <h3 className="font-heading text-sm font-semibold text-foreground">
                {column.title}
              </h3>
              <ul className="mt-4 space-y-3">
                {column.links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col gap-2 border-t border-border/70 pt-6 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <span>© {new Date().getFullYear()} RestauHub Africa. Tous droits réservés.</span>
          <span>Fait pour la restauration africaine — multi-pays, multi-langues, multi-devises.</span>
        </div>
      </div>
    </footer>
  );
}
