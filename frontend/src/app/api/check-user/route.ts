import { NextRequest, NextResponse } from 'next/server';

// This endpoint previously relied on Supabase Admin (service role).
// To avoid leaking service keys and failures in public demos, we return a safe default.
// If you need this functionality, implement it on a secure server with a service role key.
export async function GET(_req: NextRequest) {
  return NextResponse.json({ exists: false });
}
