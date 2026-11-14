import * as RSlider from "@radix-ui/react-slider";
import { cx } from "./ui";

/* Instrument-style slider: value readout in mono, a shaded band for the range NASA actually tested (when known),
   labelled reference markers (ISS, habitat, Moon, Mars) and min / max ticks. Built on Radix Slider (keyboard + ARIA). */

export type Marker = { at: number; label: string; tone?: "ink" | "flare" };

export function InstrumentSlider({ label, unit, min, max, step, value, onChange, tested, testedLabel, markers = [], format }: {
  label: string; unit: string; min: number; max: number; step: number; value: number; onChange: (v: number) => void;
  tested?: [number, number] | null; testedLabel?: string; markers?: Marker[]; format?: (v: number) => string;
}) {
  const pct = (v: number) => ((Math.min(max, Math.max(min, v)) - min) / (max - min)) * 100;
  const fmt = format ?? ((v: number) => String(v));
  const inside = tested ? value >= tested[0] - 1e-9 && value <= tested[1] + 1e-9 : null;
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between gap-2">
        <span className="font-mono text-[0.68rem] uppercase tracking-[0.16em] text-faint" id={`lbl-${label}`}>{label}</span>
        <span className="readout text-lg text-ink">{fmt(value)}<span className="ml-1 font-sans text-sm text-muted">{unit}</span></span>
      </div>
      <div className="relative pt-1">
        <RSlider.Root min={min} max={max} step={step} value={[value]} onValueChange={([v]) => onChange(Number(v.toFixed(3)))}
          aria-labelledby={`lbl-${label}`} className="relative flex h-6 w-full touch-none select-none items-center">
          <RSlider.Track className="relative h-[6px] w-full grow rounded-full bg-raised ring-1 ring-line/80">
            {tested && (
              <span className="absolute -top-[3px] h-[12px] rounded-full bg-ok/45 ring-1 ring-ok/70" aria-hidden
                style={{ left: `calc(${pct(tested[0])}% - ${tested[0] === tested[1] ? 3 : 0}px)`, width: `max(6px, ${pct(tested[1]) - pct(tested[0])}%)` }} />
            )}
            <RSlider.Range className="absolute h-full rounded-full bg-signal/20" />
          </RSlider.Track>
          <RSlider.Thumb aria-label={label}
            className={cx("block h-5 w-5 rounded-full border-2 bg-space shadow-card outline-none transition-colors focus-visible:ring-2 focus-visible:ring-signal",
              inside === false ? "border-flare" : "border-signal")} />
        </RSlider.Root>
        <div className="relative mt-1 h-7">
          {markers.map((mk) => (
            <button key={mk.label} type="button" onClick={() => onChange(mk.at)} title={`Set to ${mk.label}: ${fmt(mk.at)} ${unit}`}
              className={cx("absolute", pct(mk.at) < 6 ? "text-left" : pct(mk.at) > 94 ? "-translate-x-full text-right" : "-translate-x-1/2 text-center")} style={{ left: `${pct(mk.at)}%` }}>
              <span className={cx("block h-2 w-px", pct(mk.at) < 6 ? "" : pct(mk.at) > 94 ? "ml-auto" : "mx-auto", mk.tone === "flare" ? "bg-flare" : "bg-ink/50")} aria-hidden />
              <span className={cx("block whitespace-nowrap font-mono text-[0.6rem] leading-tight", mk.tone === "flare" ? "text-flare" : "text-muted")}>{mk.label}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="flex items-center justify-between font-mono text-[0.62rem] text-faint">
        <span>{fmt(min)}</span>
        {tested && <span className={cx(inside ? "text-ok" : "text-flare")}>{inside ? "inside" : "outside"} {testedLabel ?? "NASA-tested range"}</span>}
        <span>{fmt(max)}</span>
      </div>
    </div>
  );
}
