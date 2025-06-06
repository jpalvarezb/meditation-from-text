import { createServerClient } from '@supabase/ssr';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => []
      } // required, even if unused
    }
  );

  const { searchParams } = new URL(req.url);
  const email = searchParams.get('email');
  if (!email) return NextResponse.json({ exists: false });

  const { data, error } = await supabase.auth.admin.listUsers();

  if (error) {
    console.error('Check-user error', error);
    return NextResponse.json({ exists: false });
  }

  const exists =
    data?.users?.some((u) => u.email === email && u.confirmed_at !== null) ?? false;

  return NextResponse.json({ exists });
}
