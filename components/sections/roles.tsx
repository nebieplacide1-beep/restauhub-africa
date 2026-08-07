"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Check } from "lucide-react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { roles } from "@/lib/content";

export function Roles() {
  const [active, setActive] = useState<(typeof roles)[number]["key"]>(roles[0].key);
  const current = roles.find((role) => role.key === active) ?? roles[0];

  return (
    <section id="roles" className="border-y border-border/70 bg-neutral-50/60 py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-heading text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            Un espace pensé pour chaque rôle
          </h2>
          <p className="mt-4 text-pretty text-muted-foreground">
            12 rôles utilisateurs, chacun avec ses propres permissions, son tableau de bord et ses
            outils — du client au PDG multi-établissements.
          </p>
        </div>

        <Tabs
          value={active}
          onValueChange={(value) => setActive(value as typeof active)}
          className="mt-12 items-center"
        >
          <TabsList className="h-auto flex-wrap gap-1 bg-transparent p-0">
            {roles.map((role) => (
              <TabsTrigger
                key={role.key}
                value={role.key}
                className="h-10 rounded-full border border-border/70 bg-card px-5 text-sm font-medium data-active:border-transparent data-active:bg-brand-500 data-active:text-white data-active:shadow-none"
              >
                {role.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        <div className="relative mt-8 min-h-[220px] overflow-hidden rounded-2xl border border-border/70 bg-card p-8 sm:p-10">
          <AnimatePresence mode="wait">
            <motion.div
              key={current.key}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
            >
              <h3 className="font-heading text-xl font-semibold text-foreground sm:text-2xl">
                {current.headline}
              </h3>
              <ul className="mt-6 grid gap-3 sm:grid-cols-3">
                {current.bullets.map((bullet) => (
                  <li key={bullet} className="flex items-start gap-2.5 text-sm text-muted-foreground">
                    <Check className="mt-0.5 size-4 shrink-0 text-accent-500" />
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}
