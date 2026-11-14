import type { ReactNode } from "react";
import { cx } from "./ui";

/* Page header used by every inner page. Two layouts so pages don't all look the same:
   "split" = text left, credited NASA photo card right; "band" = photo banner behind the title. */

export const PHOTOS = {
  iss: { src: "/img/mission-iss.jpg", alt: "The International Space Station above Earth.", credit: "NASA · ISS073E0869068" },
  moon: { src: "/img/mission-moon.jpg", alt: "Apollo 17 rover and astronaut on the Moon.", credit: "NASA · AS17-146-22294" },
  mars: { src: "/img/mission-mars.jpg", alt: "Jezero Crater on Mars, seen by Perseverance.", credit: "NASA/JPL-Caltech · PIA24765" },
  orion: { src: "/img/mission-exploration.jpg", alt: "Orion spacecraft in deep space.", credit: "NASA · art002e012489" },
  acme: { src: "/img/acme-chamber.jpg", alt: "The ACME combustion chamber insert being prepared at NASA Glenn.", credit: "NASA Glenn · GRC-2016-C-05051" },
  saffire: { src: "/img/saffire-cygnus.jpg", alt: "Saffire-II experiment stowed in the Cygnus cargo vehicle.", credit: "NASA · ISS051E039882" },
  candle: { src: "/img/candle-shuttle.jpg", alt: "A spherical candle flame burning in microgravity on the Space Shuttle.", credit: "NASA · STS-50 Candle Flames in Microgravity" },
  earth: { src: "/img/earth-limb-iss.jpg", alt: "Earth's limb photographed from the International Space Station.", credit: "NASA · ISS040-E-062704" },
  flame0g: { src: "/img/flame-0g.jpg", alt: "A candle flame in microgravity, a blue sphere.", credit: "NASA Glenn · C-1998-485" },
} as const;
export type PhotoKey = keyof typeof PHOTOS;

export function PageHero({ children, photo, variant = "split", aside }: { children: ReactNode; photo?: PhotoKey; variant?: "split" | "band"; aside?: ReactNode }) {
  const p = photo ? PHOTOS[photo] : null;
  if (p && variant === "band") {
    return (
      <header className="relative overflow-hidden rounded-[22px] border border-line">
        <img src={p.src} alt={p.alt} className="absolute inset-0 h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-r from-space via-space/90 to-space/30" aria-hidden />
        <div className="relative flex flex-wrap items-end justify-between gap-4 px-6 py-10 sm:px-10 sm:py-14">
          <div className="max-w-3xl space-y-3">{children}</div>
          {aside}
        </div>
        <p className="absolute bottom-2 right-4 font-mono text-[0.62rem] text-ink/60">{p.credit}</p>
      </header>
    );
  }
  return (
    <header className={cx("grid items-center gap-8", p && "lg:grid-cols-[1.25fr_1fr]")}>
      <div className="max-w-3xl space-y-3">{children}{aside && <div className="pt-2">{aside}</div>}</div>
      {p && (
        <figure className="hidden lg:block">
          <div className="relative aspect-[16/10] overflow-hidden rounded-[20px] border border-line bg-black">
            <img src={p.src} alt={p.alt} className="absolute inset-0 h-full w-full object-cover" />
            <span className="hud-cross" style={{ left: "12%", top: "16%" }} /><span className="hud-cross" style={{ left: "88%", top: "84%" }} />
          </div>
          <figcaption className="mt-2 text-right font-mono text-[0.62rem] text-faint">{p.credit}</figcaption>
        </figure>
      )}
    </header>
  );
}

/** Shared heading styles for inside PageHero. */
export const heroTitle = "text-[2.2rem] font-semibold leading-tight tracking-tight text-ink sm:text-[2.6rem]";
