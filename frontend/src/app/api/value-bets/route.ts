import { NextResponse } from "next/server";

export async function GET() {
  const baseUrl =
    process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!baseUrl) {
    return NextResponse.json(
      { error: "Missing API_BASE_URL (or NEXT_PUBLIC_API_BASE_URL)" },
      { status: 500 }
    );
  }

  const res = await fetch(`${baseUrl}/value-bets`, { cache: "no-store" });

  if (!res.ok) {
    return NextResponse.json(
      { error: "Backend /value-bets failed" },
      { status: 502 }
    );
  }

  const data = await res.json();
  return NextResponse.json(data);
}
