import { Link } from "react-router-dom";
import { Card, CardHeader } from "../components/ui";

/* The project at a glance, organised by the five Space Apps judging criteria, plus the AI-use disclosure.
   Every claim here is checkable in the app (links) or the repo (tests, eval report). */

const REPO = "https://github.com/G3hamza/astrofire";

const CRITERIA: { key: string; title: string; question: string; points: { text: string; to?: string; href?: string }[] }[] = [
  {
    key: "impact", title: "Impact", question: "Why does it matter, and who benefits?",
    points: [
      { text: "Moon and Mars habitats are planned at about 34% oxygen and 56.5 kPa. More oxygen makes cabin materials easier to ignite, and fire in a sealed habitat is one of the most serious crew hazards (Apollo 1, Mir, Apollo 13).", to: "/" },
      { text: "Benefits spacecraft and habitat designers choosing materials, researchers planning the next experiments, safety engineers designing detectors and suppression, and students learning space combustion." },
      { text: "Shows exactly where the evidence stops: NASA's 263 solid-material space tests all ran at 13.6-22.2% oxygen and about 0 g. None at Moon/Mars air or gravity.", to: "/gaps" },
    ],
  },
  {
    key: "creativity", title: "Creativity", question: "What makes it different?",
    points: [
      { text: "Evidence-first, not guess-first: when NASA never tested a case, StarryNight says \"Insufficient validated experimental evidence\" and names the blockers instead of inventing an answer.", to: "/scenario" },
      { text: "Gravity bounds: uses NASA's own 0 g tests and Saffire-II's 1 g comparison as the two ends around Moon/Mars gravity, and says when they do not cover a case.", to: "/scenario" },
      { text: "An AI analyst that can only use NASA evidence: every sentence is cited [E#], numbers are checked against the evidence, verdicts cannot be changed by the AI.", to: "/ask" },
      { text: "Habitat ranking: all 24 investigations scored 0-100 for a spacecraft, the ISS, a Moon base, a rover or a Mars base, with every score part explained.", to: "/rank" },
    ],
  },
  {
    key: "validity", title: "Validity", question: "Does it work, and can we justify it?",
    points: [
      { text: "Verdicts come from fixed, inspectable rules (evidence distance to the closest NASA tests), never from the language model." },
      { text: "Every test row keeps its NASA source file and row number; outcomes are labelled observed, inferred or not recorded; ISS/Cygnus pressure is marked assumed.", to: "/data" },
      { text: "139 automated tests (data rules, API, every screen, user journeys, security, AI guardrails) and a 26-question AI evaluation that never states odds or chances and refuses 100% of off-topic questions.", href: `${REPO}/tree/main/tests` },
      { text: "Data pipeline Bronze → Silver → Gold with a quarantine table: nothing is deleted, every rejected row keeps its reason.", href: `${REPO}/blob/main/docs/PIPELINE_GUIDE.md` },
    ],
  },
  {
    key: "relevance", title: "Relevance", question: "Does it solve the selected challenge with NASA data?",
    points: [
      { text: "Challenge: Flame in Freefall. Built only on NASA's Physical Sciences Informatics (PSI) combustion repository: 24 investigations (BASS, BASS-II, Saffire I-III, SAME, SAME-R, FLEX, CFI, ACME and more).", to: "/experiments" },
      { text: "Summarizes, ranks and interprets investigations (Ask, Rank, Investigations).", to: "/investigations" },
      { text: "Identifies the investigations most relevant to spacecraft, stations, Moon/Mars bases and rovers.", to: "/rank" },
      { text: "Extracts clean datasets for flammability modeling, and what the research means for next-generation fire-safety equipment and fire safety on Earth.", to: "/applications" },
    ],
  },
  {
    key: "presentation", title: "Presentation", question: "Can someone understand it quickly?",
    points: [
      { text: "Ask a question in plain English or Arabic on any page (Ask AI button), or describe a scenario in your own words.", to: "/ask" },
      { text: "Every verdict, color and number links to the NASA record that supports it; colors always come with an icon and text." },
      { text: "Beginner handbook, full technical context and a 2-minute demo script are in the repository.", href: `${REPO}/tree/main/docs` },
    ],
  },
];

function Point({ p }: { p: { text: string; to?: string; href?: string } }) {
  return (
    <li className="list-disc marker:text-faint">
      {p.text}{" "}
      {p.to && <Link to={p.to} className="whitespace-nowrap text-sm">See it →</Link>}
      {p.href && <a href={p.href} target="_blank" rel="noreferrer" className="whitespace-nowrap text-sm">Source →</a>}
    </li>
  );
}

export default function AboutPage() {
  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <p className="eyebrow">NASA Space Apps Cairo 2026 · Flame in Freefall · Team Starry Night</p>
        <h1 className="text-h1 text-ink">About StarryNight</h1>
        <p className="max-w-3xl text-muted">StarryNight turns NASA's space combustion experiments into fire-safety answers for spacecraft, the ISS,
          Moon and Mars bases and rovers. It answers three questions from real NASA tests: will it burn, what proves it, and how sure are we,
          and it says plainly when NASA has no evidence.</p>
      </header>

      <div className="grid gap-4 lg:grid-cols-2">
        {CRITERIA.map((c) => (
          <Card key={c.key} as="article" id={c.key}>
            <CardHeader eyebrow={c.question} title={c.title} />
            <ul className="space-y-2 px-5 py-4 pl-10 text-ink/90">{c.points.map((p) => <Point key={p.text} p={p} />)}</ul>
          </Card>
        ))}

        <Card as="article" id="ai-use">
          <CardHeader eyebrow="Disclosure" title="How AI was used" />
          <ul className="space-y-2 px-5 py-4 pl-10 text-ink/90">
            <li className="list-disc marker:text-faint">In the product: an open-weight language model (openai/gpt-oss-120b on Groq, with smaller fallbacks)
              rewrites answers from NASA evidence that StarryNight's own code selects. It cannot add facts, numbers or verdicts; if it fails the checks,
              a template answer built from the same NASA records is shown, and every answer says which one you got.</li>
            <li className="list-disc marker:text-faint">In development: the team used AI coding assistants (Claude) to help write and review code,
              tests and documentation. Design decisions, data rules and the final review were the team's.</li>
            <li className="list-disc marker:text-faint">Not AI: the data pipeline, the verdict engine, gravity bounds and the ranking are
              deterministic code that anyone can read and re-run.</li>
          </ul>
        </Card>

        <Card as="article" id="data">
          <CardHeader eyebrow="Sources" title="NASA data and resources used" />
          <ul className="space-y-2 px-5 py-4 pl-10 text-ink/90">
            <li className="list-disc marker:text-faint">NASA Physical Sciences Informatics (PSI) combustion investigations, public domain (CC0):{" "}
              <a href="https://psi.nasa.gov" target="_blank" rel="noreferrer">psi.nasa.gov</a></li>
            <li className="list-disc marker:text-faint">The resources listed on the Space Apps challenge page (NASA spinoffs and background).</li>
            <li className="list-disc marker:text-faint">Code and documentation: <a href={REPO} target="_blank" rel="noreferrer">github.com/G3hamza/astrofire</a></li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
