import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Initialize with your PUBLIC URL and SERVICE ROLE key
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const email = searchParams.get('email');
  if (!email) return NextResponse.json({ exists: false });

  // List all users via Admin API
  const { data, error } = await supabase.auth.admin.listUsers();

  if (error) {
    console.error('Check-user error', error);
    return NextResponse.json({ exists: false });
  }

  // Check for a user whose email matches and is confirmed
  const exists =
    data?.users?.some((u) => u.email === email && u.confirmed_at !== null) ??
    false;

  return NextResponse.json({ exists });
}
