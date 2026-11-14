import { ArrowRight, Flame, Rocket, Wind } from "lucide-react";
import { Link } from "react-router-dom";
import { SourceChip } from "./SourceChip";
import { Card } from "./ui";

/* Facts below are taken from the official NASA pages linked on each card (Space Apps 2026 challenge resources).
   "What it means for StarryNight" is our interpretation and is labelled as such. */

const CASES = [
  {
    when: "27 Jan 1967 · launch-pad test", title: "Apollo 1", Icon: Flame,
    facts: "The cabin was pressurized with 100% oxygen. A flash fire swept through the spacecraft so quickly there was no time to open the hatches. Air Force pathologists concluded the crew died of carbon monoxide and other toxic gases; their burns were likely survivable.",
    lesson: "NASA restricted and controlled the amount and location of combustible material in the spacecraft, and redesigned the hatch to open in three seconds.",
    ours: "Oxygen-rich air plus cabin materials is the core risk. StarryNight flags every condition above the oxygen NASA tested, and shows smoke data, because the gases killed the crew.",
    link: "/scenario?material=PMMA+%28acrylic%29&mission=exploration&flow=5", linkText: "Check a raised-oxygen scenario",
    url: "https://sma.nasa.gov/sma-disciplines/accllp/apollo-1", label: "NASA · Apollo 1",
    img: "/img/incident-apollo1.jpg", alt: "The fire-scorched exterior of the Apollo 1 command module (Spacecraft 012) on Pad 34 after the fire.", credit: "Apollo 1 command module after the fire · NASA S67-21295",
  },
  {
    when: "24 Feb 1997 · space station Mir", title: "Mir fire", Icon: Wind,
    facts: "A solid-fuel oxygen generator canister ignited, shooting a three-foot flame across the module and filling it with dense smoke. The flame blocked the route to one of two Soyuz escape vehicles. The crew fought it with extinguishers; life support cleared the smoke over several hours.",
    lesson: "Investigators named latex glove material introduced into the canister as the most likely cause. Training, ground response and canister preparation changed, and the lessons went into the design of the ISS.",
    ours: "Fires happen in orbit, inside a crewed station. How a flame behaves at ~0 g and how smoke spreads is exactly what BASS, SAFFIRE and SAME measured.",
    link: "/experiments", linkText: "See the NASA experiments",
    url: "https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/", label: "NASA · Mir fire",
    img: "/img/incident-mir.jpg", alt: "The Mir space station in orbit, photographed by the Space Shuttle crew in 1997.", credit: "Mir in 1997, the year of the fire · NASA STS086-720-007",
  },
  {
    when: "1970 · on the way to the Moon", title: "Apollo 13", Icon: Rocket,
    facts: "On the third day of the mission oxygen tank number two blew up, leading to the failure of tank number one and threatening the loss of all electrical power and water. The Lunar Module Aquarius kept the crew alive and brought them home.",
    lesson: "The review board recommended redesigning the Service Module oxygen storage system and reviewing every Apollo system that uses cryogenic oxygen. The page also notes that Apollo 1's added wiring insulation helped prevent arcing.",
    ours: "Oxygen systems are a hazard in their own right, and fixes from one accident protect the next mission. StarryNight shows where today's evidence stops, so the gaps get tested before a crew depends on them.",
    link: "/gaps", linkText: "See what was never tested",
    url: "https://sma.nasa.gov/sma-disciplines/accllp/apollo-13", label: "NASA · Apollo 13",
    img: "/img/incident-apollo13.jpg", alt: "The damaged Apollo 13 Service Module, photographed by the crew after it was jettisoned.", credit: "Damaged Apollo 13 Service Module · NASA AS13-59-8500",
  },
];

export function WhyItMatters({ bare }: { bare?: boolean } = {}) {
  return (
    <section aria-labelledby={bare ? undefined : "why-h"} aria-label={bare ? "Spacecraft fires NASA learned from" : undefined} className="space-y-4">
      {!bare && <div className="space-y-1">
        <p className="eyebrow">Why it matters</p>
        <h2 id="why-h" className="text-h2">Spacecraft fires NASA learned from</h2>
        <p className="max-w-3xl text-muted">Each lesson below changed how spacecraft are built. Moon and Mars habitats will run at 34% oxygen, a condition no solid material has been fire-tested at in space.</p>
      </div>}
      <div className="grid gap-4 lg:grid-cols-3">
        {CASES.map((c) => (
          <Card key={c.title} as="article" className="flex flex-col overflow-hidden">
            <figure className="relative aspect-[4/3] bg-black">
              <img src={c.img} alt={c.alt} loading="lazy" className="absolute inset-0 h-full w-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-black via-black/25 to-transparent" aria-hidden />
              <span className="absolute left-3 top-3 inline-flex items-center gap-1.5 rounded-full border border-ink/20 bg-black/60 px-2.5 py-1 font-mono text-[0.68rem] text-ink">
                <c.Icon size={12} className="text-burn" aria-hidden /> {c.when}
              </span>
              <h3 className="absolute bottom-9 left-4 text-[1.6rem] font-semibold tracking-tight text-ink">{c.title}</h3>
              <figcaption className="absolute bottom-3 left-4 right-4 truncate font-mono text-[0.64rem] text-ink/70">{c.credit}</figcaption>
            </figure>
            <div className="flex flex-1 flex-col gap-3 p-5">
              <p className="text-ink/90">{c.facts}</p>
              <p className="text-sm text-muted"><b className="text-ink">What NASA changed:</b> {c.lesson}</p>
              <p className="rounded-lg border border-dashed border-signal/50 bg-signal/5 p-3 text-sm text-ink/90">
                <span className="eyebrow mb-1 block text-signal">What it means for StarryNight (our reading)</span>{c.ours}
              </p>
              <div className="mt-auto flex flex-wrap items-center justify-between gap-2 pt-1">
                <SourceChip href={c.url} label={c.label} />
                <Link to={c.link} className="inline-flex items-center gap-1 text-sm">{c.linkText} <ArrowRight size={13} aria-hidden /></Link>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </section>
  );
}

/* Official Space Apps 2026 "Flame in Freefall" resources, as listed on the challenge page. */
export const CHALLENGE_RESOURCES: { title: string; url: string; note: string; used: string }[] = [
  { title: "PSI Data Repository: Combustion Science", url: "https://psi.nasa.gov/physci/repo/search?q=combustion", note: "Source of all experiment data", used: "Core data: all 24 combustion investigations in the pipeline" },
  { title: "NASA Combustion Science", url: "https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/", note: "Background on each investigation", used: "Background" },
  { title: "ScienceCasts: The Power of Studying Combustion on the ISS", url: "https://www.youtube.com/watch?v=W1oXykoz9zg", note: "3.6-minute video (2018)", used: "Intro for viewers" },
  { title: "A Researcher's Guide to ISS Combustion Science", url: "https://www.nasa.gov/missions/station/a-researchers-guide-to-combustion-science/", note: "2015 review, 50+ pages", used: "Background" },
  { title: "Apollo 1", url: "https://sma.nasa.gov/sma-disciplines/accllp/apollo-1", note: "Cabin fire, lessons learned", used: "Why it matters (Home)" },
  { title: "Apollo 13", url: "https://sma.nasa.gov/sma-disciplines/accllp/apollo-13", note: "Oxygen tank explosion", used: "Why it matters (Home)" },
  { title: "25 Years Ago: Fire Aboard Space Station Mir", url: "https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/", note: "1997 oxygen-generator fire", used: "Why it matters (Home)" },
  { title: "Spinoff: Fireman's Air Tanks", url: "https://spinoff.nasa.gov/node/9582", note: "Spacesuit tech for firefighters", used: "Earth benefits" },
  { title: "Spinoff: Fire Detector", url: "https://spinoff.nasa.gov/node/9407", note: "Shuttle smoke detector", used: "Earth benefits (links to SAME smoke data)" },
  { title: "Spinoff: New Technology for the Fire Attire", url: "https://spinoff.nasa.gov/node/9918", note: "Firefighter clothing", used: "Earth benefits" },
];

export function ChallengeResources() {
  return (
    <Card id="resources">
      <div className="space-y-1 border-b border-line/70 px-5 py-4">
        <p className="eyebrow">Space Apps 2026 · Flame in Freefall</p>
        <h3 className="text-h3">Official challenge resources and how StarryNight uses them</h3>
      </div>
      <ul className="divide-y divide-line/50">
        {CHALLENGE_RESOURCES.map((r) => (
          <li key={r.url} className="grid gap-1 px-5 py-3 sm:grid-cols-[1fr_auto] sm:items-center">
            <div>
              <a href={r.url} target="_blank" rel="noopener noreferrer" className="font-medium">{r.title}</a>
              <p className="text-sm text-faint">{r.note}</p>
            </div>
            <span className="text-sm text-muted">{r.used}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
