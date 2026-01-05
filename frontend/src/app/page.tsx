import Link from "next/link";

export default function Home() {
  return (
    <main className="p-8">
      <h1 className="text-3xl font-bold mb-4">🎾 Tennis ML Dashboard</h1>

      <Link
        href="/value-bets"
        className="inline-block px-4 py-2 bg-black text-white rounded"
      >
        Vai alle Value Bets →
      </Link>
    </main>
  );
}
