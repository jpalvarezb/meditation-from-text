'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabaseClient';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  // Optimistically assume session exists if stored in localStorage
  const [checking, setChecking] = useState(true);


  useEffect(() => {
    // Wrap logic in an async IIFE for error boundary handling
    (async () => {
      try {
        // If the URL contains access_token and refresh_token (from email link), set the session
        const hash = window.location.hash;
        if (hash && hash.includes('access_token')) {
          const params = new URLSearchParams(hash.replace('#', ''));
          const access_token = params.get('access_token');
          const refresh_token = params.get('refresh_token');
          if (access_token && refresh_token) {
            await supabase.auth.setSession({
              access_token,
              refresh_token,
            });
            // Remove tokens from URL after setting session
            window.location.hash = '';
          }
        }
        // Now read stored session (after processing tokens)
        const { data: { session } } = await supabase.auth.getSession();
        console.log('Session check:', session ? 'Found' : 'Not found');
        if (!session) {
          console.log('No session found, redirecting to login');
          router.replace('/login');
          return;
        }
        // Verify user has a profile (accepted signup)
        const { data: profile, error: profileError } = await supabase
          .from('profiles')
          .select('id')
          .eq('id', session.user.id)
          .single();
        if (profileError || !profile) {
          console.log('Profile verification failed, redirecting to login');
          router.replace('/login');
          return;
        }
        setChecking(false);
      } catch {
        // Improved error handling: fallback to login
        router.replace('/login');
      }
    })();
  }, [router]);

  if (checking)
    return (
      <div
        style={{
          backgroundColor: '#FDFBEF',
          width: '100vw',
          height: '100vh',
        }}
      />
    );

  return <>{children}</>;
}
