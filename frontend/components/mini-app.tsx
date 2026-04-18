"use client";

import { useEffect, useState, useTransition } from "react";

import { DashboardCard } from "@/components/dashboard-card";
import { MatchCard } from "@/components/match-card";
import { StockAlertList } from "@/components/stock-alert-list";

type TabKey = "dashboard" | "add" | "scan";

type DashboardSummary = {
  total_daily_profit: number;
  total_sales_today: number;
  total_products: number;
  low_stock_count: number;
  stock_alerts: Array<{
    id: string;
    name: string;
    stock_qty: number;
    severity: "red" | "yellow";
  }>;
};

type OnboardResponse = {
  message: string;
  product: {
    id: string;
    name: string;
    category: string;
    stock_qty: number;
    sale_price: number;
    image_url?: string | null;
  };
  ai_description: {
    name: string;
    category: string;
    fingerprint_text: string;
    confidence_note: string;
  };
};

type MatchResult = {
  id: string;
  name: string;
  category: string;
  sale_price: number;
  stock_qty: number;
  image_url?: string | null;
  similarity: number;
};

type ProductRecord = {
  id: string;
  cost_price: number;
  sale_price: number;
};

type MiniAppProps = {
  apiBaseUrl: string;
};

const emptySummary: DashboardSummary = {
  total_daily_profit: 0,
  total_sales_today: 0,
  total_products: 0,
  low_stock_count: 0,
  stock_alerts: [],
};

export function MiniApp({ apiBaseUrl }: MiniAppProps) {
  const [activeTab, setActiveTab] = useState<TabKey>("dashboard");
  const [summary, setSummary] = useState<DashboardSummary>(emptySummary);
  const [onboardImage, setOnboardImage] = useState<File | null>(null);
  const [costPrice, setCostPrice] = useState("");
  const [salePrice, setSalePrice] = useState("");
  const [stockQty, setStockQty] = useState("");
  const [onboardResult, setOnboardResult] = useState<OnboardResponse | null>(null);
  const [scanImage, setScanImage] = useState<File | null>(null);
  const [matches, setMatches] = useState<MatchResult[]>([]);
  const [selectedMatch, setSelectedMatch] = useState<MatchResult | null>(null);
  const [scanQty, setScanQty] = useState("1");
  const [saleMessage, setSaleMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    fetchSummary();
    const telegram = (window as typeof window & {
      Telegram?: { WebApp?: { ready: () => void; expand: () => void } };
    }).Telegram?.WebApp;
    telegram?.ready();
    telegram?.expand();
  }, []);

  async function fetchSummary() {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/dashboard/summary`, {
        cache: "no-store",
      });
      if (!response.ok) {
        throw new Error("Could not load dashboard summary.");
      }
      const payload = (await response.json()) as DashboardSummary;
      startTransition(() => {
        setSummary(payload);
      });
    } catch {
      startTransition(() => {
        setSummary(emptySummary);
      });
    }
  }

  async function handleOnboardSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");
    setOnboardResult(null);

    if (!onboardImage) {
      setErrorMessage("Choose or capture an image before saving an item.");
      return;
    }

    const formData = new FormData();
    formData.append("image", onboardImage);
    formData.append("cost_price", costPrice);
    formData.append("sale_price", salePrice);
    formData.append("stock_qty", stockQty);

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/products/onboard`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error("The item could not be saved.");
      }
      const payload = (await response.json()) as OnboardResponse;
      startTransition(() => {
        setOnboardResult(payload);
        setCostPrice("");
        setSalePrice("");
        setStockQty("");
        setOnboardImage(null);
        setActiveTab("dashboard");
      });
      await fetchSummary();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "The item could not be saved.");
    }
  }

  async function handleScanSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");
    setSaleMessage("");
    setMatches([]);
    setSelectedMatch(null);

    if (!scanImage) {
      setErrorMessage("Choose or capture an image before scanning.");
      return;
    }

    const formData = new FormData();
    formData.append("image", scanImage);

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/products/match`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error("The item could not be matched.");
      }
      const payload = (await response.json()) as MatchResult[];
      startTransition(() => {
        setMatches(payload);
        setSelectedMatch(payload[0] ?? null);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "The item could not be matched.");
    }
  }

  async function handleLogSale() {
    setErrorMessage("");
    setSaleMessage("");

    if (!selectedMatch) {
      setErrorMessage("Select a match before logging the sale.");
      return;
    }

    try {
      const productResponse = await fetch(
        `${apiBaseUrl}/api/v1/products/${selectedMatch.id}`,
      );
      if (!productResponse.ok) {
        throw new Error("Could not load the selected product.");
      }
      const product = (await productResponse.json()) as ProductRecord;

      const saleResponse = await fetch(`${apiBaseUrl}/api/v1/sales`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_id: selectedMatch.id,
          quantity: Number(scanQty),
          sale_price: product.sale_price,
          cost_price: product.cost_price,
        }),
      });
      if (!saleResponse.ok) {
        throw new Error("The sale could not be logged.");
      }
      const payload = (await saleResponse.json()) as {
        sale: { profit: number };
      };
      startTransition(() => {
        setSaleMessage(
          `Sale logged for ${selectedMatch.name}. Profit: Birr ${payload.sale.profit.toFixed(2)}.`
        );
        setMatches([]);
        setSelectedMatch(null);
        setScanImage(null);
        setScanQty("1");
        setActiveTab("dashboard");
      });
      await fetchSummary();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "The sale could not be logged.");
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-4 py-5 sm:px-6">
      <section className="rounded-[32px] border border-white/70 bg-[var(--card)] p-6 shadow-card backdrop-blur">
        <p className="text-sm uppercase tracking-[0.3em] text-coffee/60">Zembil Vision</p>
        <div className="mt-4 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="font-display text-4xl leading-tight text-coffee sm:text-5xl">
              One mini app for stock, sales, and visual checkout.
            </h1>
            <p className="mt-3 max-w-2xl text-base leading-7 text-coffee/80">
              Add a product with a photo, scan an item when it sells, and keep daily profit
              and stock alerts visible without leaving Telegram.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <TabButton
              active={activeTab === "dashboard"}
              label="Dashboard"
              onClick={() => setActiveTab("dashboard")}
            />
            <TabButton active={activeTab === "add"} label="Add Item" onClick={() => setActiveTab("add")} />
            <TabButton active={activeTab === "scan"} label="Scan Sale" onClick={() => setActiveTab("scan")} />
          </div>
        </div>
      </section>

      {errorMessage ? (
        <div className="mt-5 rounded-3xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {errorMessage}
        </div>
      ) : null}

      {saleMessage ? (
        <div className="mt-5 rounded-3xl border border-basil/30 bg-[rgba(88,107,79,0.14)] px-4 py-3 text-sm text-coffee">
          {saleMessage}
        </div>
      ) : null}

      {activeTab === "dashboard" ? (
        <section className="mt-6 space-y-6">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <DashboardCard
              title="Daily Profit"
              value={`Birr ${summary.total_daily_profit.toFixed(2)}`}
              hint="Today's logged profit."
              tone="accent"
            />
            <DashboardCard
              title="Sales Today"
              value={`${summary.total_sales_today}`}
              hint="Completed scanner checkouts."
            />
            <DashboardCard
              title="Total Products"
              value={`${summary.total_products}`}
              hint="Items known to the visual catalog."
            />
            <DashboardCard
              title="Low Stock"
              value={`${summary.low_stock_count}`}
              hint="Red is 0. Yellow is under 3."
              tone="warning"
            />
          </div>

          <div className="grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
            <StockAlertList alerts={summary.stock_alerts} />
            <div className="rounded-[28px] border border-white/70 bg-white/70 p-6 shadow-card">
              <p className="text-sm uppercase tracking-[0.24em] text-coffee/60">
                Mini App Flow
              </p>
              <div className="mt-4 space-y-3 text-sm leading-7 text-coffee/80">
                <p>Use Add Item to capture a new product with pricing and quantity.</p>
                <p>Use Scan Sale to upload a checkout photo and tap the right match.</p>
                <p>Daily profit and stock alerts stay visible here for quick decisions.</p>
                <button
                  type="button"
                  onClick={fetchSummary}
                  className="rounded-full bg-coffee px-4 py-2 font-semibold text-white"
                >
                  {isPending ? "Refreshing..." : "Refresh Overview"}
                </button>
              </div>
            </div>
          </div>

          {onboardResult ? (
            <div className="rounded-[28px] border border-white/70 bg-white/70 p-6 shadow-card">
              <p className="text-sm uppercase tracking-[0.24em] text-coffee/60">Last Added Item</p>
              <div className="mt-4 grid gap-4 md:grid-cols-[180px_1fr]">
                {onboardResult.product.image_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={onboardResult.product.image_url}
                    alt={onboardResult.product.name}
                    className="aspect-[4/3] w-full rounded-3xl object-cover"
                  />
                ) : null}
                <div className="space-y-2 text-sm text-coffee/80">
                  <p className="font-semibold text-coffee">{onboardResult.product.name}</p>
                  <p>{onboardResult.product.category}</p>
                  <p>{onboardResult.ai_description.fingerprint_text}</p>
                  <p>{onboardResult.ai_description.confidence_note}</p>
                </div>
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      {activeTab === "add" ? (
        <section className="mt-6 grid gap-4 lg:grid-cols-[1fr_0.95fr]">
          <form
            onSubmit={handleOnboardSubmit}
            className="rounded-[28px] border border-white/70 bg-white/70 p-6 shadow-card"
          >
            <p className="text-sm uppercase tracking-[0.24em] text-coffee/60">Add Item</p>
            <div className="mt-5 grid gap-4">
              <label className="grid gap-2 text-sm text-coffee/80">
                Item image
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  onChange={(event) => setOnboardImage(event.target.files?.[0] ?? null)}
                  className="rounded-2xl border border-coffee/20 bg-sand/60 px-4 py-3"
                />
              </label>
              <label className="grid gap-2 text-sm text-coffee/80">
                Purchase price
                <input
                  value={costPrice}
                  onChange={(event) => setCostPrice(event.target.value)}
                  inputMode="decimal"
                  className="rounded-2xl border border-coffee/20 bg-sand/60 px-4 py-3"
                />
              </label>
              <label className="grid gap-2 text-sm text-coffee/80">
                Selling price
                <input
                  value={salePrice}
                  onChange={(event) => setSalePrice(event.target.value)}
                  inputMode="decimal"
                  className="rounded-2xl border border-coffee/20 bg-sand/60 px-4 py-3"
                />
              </label>
              <label className="grid gap-2 text-sm text-coffee/80">
                Quantity
                <input
                  value={stockQty}
                  onChange={(event) => setStockQty(event.target.value)}
                  inputMode="numeric"
                  className="rounded-2xl border border-coffee/20 bg-sand/60 px-4 py-3"
                />
              </label>
              <button
                type="submit"
                className="rounded-full bg-clay px-5 py-3 font-semibold text-white"
              >
                Save Item
              </button>
            </div>
          </form>

          <div className="rounded-[28px] border border-white/70 bg-[rgba(201,111,61,0.12)] p-6 shadow-card">
            <p className="text-sm uppercase tracking-[0.24em] text-coffee/60">What AI Does</p>
            <div className="mt-4 space-y-3 text-sm leading-7 text-coffee/80">
              <p>Gemini names the item and picks a category from the uploaded photo.</p>
              <p>
                The app also creates a visual fingerprint sentence, and that text is embedded for
                similarity search.
              </p>
              <p>
                Inference from Google&apos;s docs: Gemini&apos;s embedding model is text-based, so the app
                first converts the image into structured visual text, then embeds that text at 768
                dimensions for pgvector matching.
              </p>
            </div>
          </div>
        </section>
      ) : null}

      {activeTab === "scan" ? (
        <section className="mt-6 space-y-5">
          <form
            onSubmit={handleScanSubmit}
            className="rounded-[28px] border border-white/70 bg-white/70 p-6 shadow-card"
          >
            <p className="text-sm uppercase tracking-[0.24em] text-coffee/60">Scan Sale</p>
            <div className="mt-5 grid gap-4 md:grid-cols-[1fr_auto] md:items-end">
              <label className="grid gap-2 text-sm text-coffee/80">
                Sold item image
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  onChange={(event) => setScanImage(event.target.files?.[0] ?? null)}
                  className="rounded-2xl border border-coffee/20 bg-sand/60 px-4 py-3"
                />
              </label>
              <button
                type="submit"
                className="rounded-full bg-coffee px-5 py-3 font-semibold text-white"
              >
                Find Matches
              </button>
            </div>
          </form>

          {matches.length > 0 ? (
            <>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {matches.map((match) => (
                  <MatchCard
                    key={match.id}
                    imageUrl={match.image_url}
                    name={match.name}
                    category={match.category}
                    salePrice={match.sale_price}
                    stockQty={match.stock_qty}
                    similarity={match.similarity}
                    selected={selectedMatch?.id === match.id}
                    onSelect={() => setSelectedMatch(match)}
                  />
                ))}
              </div>

              <div className="rounded-[28px] border border-white/70 bg-white/70 p-6 shadow-card">
                <div className="grid gap-4 md:grid-cols-[1fr_auto] md:items-end">
                  <label className="grid gap-2 text-sm text-coffee/80">
                    Quantity sold
                    <input
                      value={scanQty}
                      onChange={(event) => setScanQty(event.target.value)}
                      inputMode="numeric"
                      className="rounded-2xl border border-coffee/20 bg-sand/60 px-4 py-3"
                    />
                  </label>
                  <button
                    type="button"
                    onClick={handleLogSale}
                    className="rounded-full bg-basil px-5 py-3 font-semibold text-white"
                  >
                    Confirm Sale
                  </button>
                </div>
              </div>
            </>
          ) : null}
        </section>
      ) : null}
    </main>
  );
}

type TabButtonProps = {
  active: boolean;
  label: string;
  onClick: () => void;
};

function TabButton({ active, label, onClick }: TabButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
        active ? "bg-coffee text-white" : "bg-white/70 text-coffee"
      }`}
    >
      {label}
    </button>
  );
}
