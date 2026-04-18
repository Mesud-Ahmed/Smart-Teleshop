type MatchCardProps = {
  imageUrl?: string | null;
  name: string;
  category: string;
  salePrice: number;
  stockQty: number;
  similarity: number;
  selected?: boolean;
  onSelect: () => void;
};

export function MatchCard({
  imageUrl,
  name,
  category,
  salePrice,
  stockQty,
  similarity,
  selected = false,
  onSelect,
}: MatchCardProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`overflow-hidden rounded-[28px] border text-left shadow-card transition ${
        selected
          ? "border-clay bg-[rgba(201,111,61,0.14)]"
          : "border-white/70 bg-white/75"
      }`}
    >
      <div className="aspect-[4/3] w-full bg-sand">
        {imageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={imageUrl} alt={name} className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-coffee/60">
            No image
          </div>
        )}
      </div>
      <div className="space-y-2 p-4">
        <div>
          <p className="font-semibold text-coffee">{name}</p>
          <p className="text-sm text-coffee/70">{category}</p>
        </div>
        <div className="flex flex-wrap gap-2 text-sm text-coffee/80">
          <span className="rounded-full bg-sand px-3 py-1">Birr {salePrice}</span>
          <span className="rounded-full bg-sand px-3 py-1">Stock {stockQty}</span>
          <span className="rounded-full bg-sand px-3 py-1">
            Match {(similarity * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </button>
  );
}
