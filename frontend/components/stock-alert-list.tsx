type StockAlert = {
  id: string;
  name: string;
  stock_qty: number;
  severity: "red" | "yellow";
};

type StockAlertListProps = {
  alerts: StockAlert[];
};

export function StockAlertList({ alerts }: StockAlertListProps) {
  if (alerts.length === 0) {
    return (
      <div className="rounded-[28px] border border-white/70 bg-white/70 p-6 shadow-card">
        <p className="text-sm uppercase tracking-[0.24em] text-coffee/60">Stock Alerts</p>
        <p className="mt-3 text-lg text-coffee">All products are above the danger zone.</p>
      </div>
    );
  }

  return (
    <div className="rounded-[28px] border border-white/70 bg-white/70 p-6 shadow-card">
      <p className="text-sm uppercase tracking-[0.24em] text-coffee/60">Stock Alerts</p>
      <div className="mt-4 space-y-3">
        {alerts.map((alert) => {
          const badgeClass =
            alert.severity === "red"
              ? "bg-red-500 text-white"
              : "bg-amber-300 text-coffee";
          const label = alert.severity === "red" ? "Out of stock" : "Running low";

          return (
            <div
              key={alert.id}
              className="flex items-center justify-between rounded-2xl border border-coffee/10 bg-sand/70 px-4 py-3"
            >
              <div>
                <p className="font-semibold text-coffee">{alert.name}</p>
                <p className="text-sm text-coffee/70">Remaining: {alert.stock_qty}</p>
              </div>
              <span className={`rounded-full px-3 py-1 text-sm font-semibold ${badgeClass}`}>
                {label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
