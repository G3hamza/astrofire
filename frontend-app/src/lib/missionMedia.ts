import type { MissionKey } from "./types";

/* Real NASA photos for each mission preset (public domain, credited on screen). */
export const MISSION_MEDIA: Record<MissionKey, { short: string; img: string; alt: string; credit: string }> = {
  iss: { short: "ISS", img: "/img/mission-iss.jpg", alt: "The International Space Station's solar arrays and robotic arm above Earth.", credit: "NASA · ISS073E0869068" },
  exploration: { short: "Exploration", img: "/img/mission-exploration.jpg", alt: "NASA's Orion spacecraft in deep space during Artemis II.", credit: "NASA · Orion, art002e012489" },
  moon: { short: "Moon", img: "/img/mission-moon.jpg", alt: "Apollo 17 lunar rover and an astronaut beside a large boulder on the Moon.", credit: "NASA · Apollo 17, AS17-146-22294" },
  mars: { short: "Mars", img: "/img/mission-mars.jpg", alt: "Rocky surface of Jezero Crater on Mars, seen by the Perseverance rover.", credit: "NASA/JPL-Caltech · PIA24765" },
};
