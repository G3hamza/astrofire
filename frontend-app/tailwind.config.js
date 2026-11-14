/** AstroFire "mission control" design tokens.
 *  Colors are CSS variables (RGB channels) defined in src/index.css, so Tailwind
 *  opacity modifiers work: bg-surface/80, text-burn, border-line ...
 */
const v = (name) => `rgb(var(--${name}) / <alpha-value>)`;

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // surfaces
        space: v("space"),        // page background
        surface: v("surface"),    // cards
        raised: v("raised"),      // inputs, hover, nested cards
        line: v("line"),          // borders
        // text
        ink: v("ink"),            // primary text
        muted: v("muted"),        // secondary text
        faint: v("faint"),        // captions, disabled
        // brand / UI
        signal: v("signal"),      // primary accent (mission cyan)
        // outcomes (always paired with icon + text, NFR6)
        burn: v("burn"),          // burned
        out: v("out"),            // went out / extinction
        blow: v("blow"),          // blowoff
        unknown: v("unknown"),    // not recorded
        // states / evidence
        danger: v("danger"),      // insufficient evidence, blockers
        caution: v("caution"),    // flags, borderline, inferred
        ok: v("ok"),              // observed
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI Variable", "Segoe UI", "system-ui", "-apple-system", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "Cascadia Code", "Consolas", "ui-monospace", "monospace"],
      },
      fontSize: {
        // type scale (rem, line-height) — tuned for 1366x768 + projector
        label: ["0.75rem", { lineHeight: "1rem", letterSpacing: "0.08em" }],
        sm: ["0.8125rem", { lineHeight: "1.25rem" }],
        base: ["0.9375rem", { lineHeight: "1.5rem" }],
        lg: ["1.125rem", { lineHeight: "1.65rem" }],
        h3: ["1.25rem", { lineHeight: "1.75rem", fontWeight: "600" }],
        h2: ["1.625rem", { lineHeight: "2.1rem", fontWeight: "650" }],
        h1: ["2.25rem", { lineHeight: "2.6rem", fontWeight: "700", letterSpacing: "-0.02em" }],
        display: ["3.5rem", { lineHeight: "1.05", fontWeight: "750", letterSpacing: "-0.03em" }],
      },
      borderRadius: { card: "14px" },
      boxShadow: {
        card: "0 1px 0 0 rgb(255 255 255 / 0.04) inset, 0 8px 24px -12px rgb(0 0 0 / 0.6)",
        glow: "0 0 0 1px rgb(var(--signal) / 0.35), 0 0 24px -4px rgb(var(--signal) / 0.35)",
        danger: "0 0 0 1px rgb(var(--danger) / 0.45), 0 0 28px -6px rgb(var(--danger) / 0.45)",
      },
      keyframes: {
        shimmer: { "0%": { backgroundPosition: "-400px 0" }, "100%": { backgroundPosition: "400px 0" } },
        pulseDot: { "0%,100%": { opacity: "1" }, "50%": { opacity: "0.35" } },
      },
      animation: {
        shimmer: "shimmer 1.4s linear infinite",
        pulseDot: "pulseDot 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
