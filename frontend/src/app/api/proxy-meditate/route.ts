import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  // Extract the JSON payload from the incoming client request
  const payload = await request.json();

  // Forward that payload to your FastAPI backend, injecting the real API key
  const fastApiRes = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/meditate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": process.env.BACKEND_API_KEY!,
      },
      body: JSON.stringify(payload),
    }
  );

  // Read FastAPI’s response body (as plain text) so we can re‐send it
  const text = await fastApiRes.text();

  // Mirror FastAPI’s status code and Content-Type header back to the client
  return new NextResponse(text, {
    status: fastApiRes.status,
    headers: {
      "Content-Type": fastApiRes.headers.get("Content-Type") || "application/json",
    },
  });
}
