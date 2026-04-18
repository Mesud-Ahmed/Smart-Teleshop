type DashboardCardProps = {
  title: string;
  value: string;
  hint: string;
  tone?: "default" | "accent" | "warning";
};

const toneStyles: Record<NonNullable<DashboardCardProps["tone"]>, string> = {
  default: "border-white/70 bg-white/70",
  accent: "border-clay/20 bg-[rgba(201,111,61,0.12)]",
  warning: "border-amber-400/30 bg-[rgba(234,211,177,0.55)]",
};

export function DashboardCard({
  title,
  value,
  hint,
  tone = "default",
}: DashboardCardProps) {
  return (
    <div
      className={`rounded-[28px] border p-5 shadow-card backdrop-blur ${toneStyles[tone]}`}
    >
      <p className="text-sm uppercase tracking-[0.24em] text-coffee/60">{title}</p>
      <p className="mt-3 font-display text-3xl text-coffee">{value}</p>
      <p className="mt-2 text-sm text-coffee/70">{hint}</p>
    </div>
  );
}
