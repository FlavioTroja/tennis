export default function EdgeBadge({ edge }: { edge: number }) {
  const pct = edge * 100;

  let color = "bg-green-100 text-green-700";
  if (pct > 7) color = "bg-green-200 text-green-800";
  if (pct < 3) color = "bg-yellow-100 text-yellow-700";

  return (
    <span className={`px-2 py-1 rounded text-xs font-semibold ${color}`}>
      +{pct.toFixed(2)}%
    </span>
  );
}
