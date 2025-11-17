'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabaseClient';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [resendVisible, setResendVisible] = useState(false);
  const [resendCountdown, setResendCountdown] = useState(10);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (sent && !resendVisible) {
      timer = setInterval(() => {
        setResendCountdown(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            setResendVisible(true);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [sent, resendVisible]);

  const handleLogin = async () => {
    try {
      setError(null);
      const { error } = await supabase.auth.signInWithOtp({ email });
      if (!error) {
        setSent(true);
        setResendVisible(false);
        setResendCountdown(10);
      } else {
        console.error('Login error:', error);
        if (error.message.includes('10 seconds')) {
          setError('Please wait 10 seconds before requesting another link');
        } else {
          setError('Production halted.');
        }

        const { data: { session } } = await supabase.auth.getSession();
        const user_id = session?.user?.id ?? null;

        await supabase.from('bug_reports').insert({
          user_id,
          message: typeof error === 'object' && error?.message ? error.message : String(error),
          stacktrace: typeof error === 'object' && 'stack' in error ? error.stack ?? null : null,
          page: 'login',
          metadata: JSON.stringify({ email }),
        });
      }
    } catch (err) {
      console.error('Unexpected error:', err);
      setError('An unexpected error occurred. Please try again.');
    }
  };

  return (
    <main
      style={{
        backgroundColor: '#F9E66B',
        height: '100vh',
        width: '100vw',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        fontFamily: 'inherit',
        gap: '3rem',
      }}
    >
      {sent ? (
        <>
          <p style={{
            fontSize: '1.2rem',
            fontFamily: 'Helvetica, sans-serif',
            fontWeight: 'lighter',
            color: '#000',
            textAlign: 'center'
          }}>
            Check your email for the login link.
          </p>
          {!resendVisible && (
            <p style={{
              fontSize: '0.9rem',
              fontFamily: 'Helvetica, sans-serif',
              fontWeight: 'lighter',
              color: '#3A53F7',
              textAlign: 'center',
              padding: '0.5rem 1rem'
            }}>
              Didn&apos;t get an email link? Try resending in {resendCountdown} seconds...
            </p>
          )}
          {resendVisible && (
            <button
              onClick={handleLogin}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#3A53F7',
                color: '#FFF',
                border: 'none',
                borderRadius: '9999px',
                fontSize: '1rem',
                fontFamily: 'inherit',
                cursor: 'pointer',
              }}
            >
              Resend link
            </button>
          )}
        </>
      ) : (
        <>
          <h1 style={{ fontSize: '1.3rem', color: '#000', fontFamily: "Helvetica, sans-serif", fontWeight:'lighter' }}>Take a Minday. </h1>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            style={{
              padding: '0.7rem 1.5rem',
              fontSize: '1rem',
              border: 'none',
              borderRadius: '8px',
              width: '250px',
              textAlign: 'center',
              backgroundColor: '#FFF',
              color: '#3A53F7',
            }}
          />
          <button
            onClick={handleLogin}
            style={{
              padding: '0.7rem 1.5rem',
              backgroundColor: '#3A53F7',
              color: '#FFF',
              border: 'none',
              borderRadius: '9999px',
              fontSize: '1rem',
              fontFamily: 'inherit',
              cursor: 'pointer',
            }}
          >
            Get link
          </button>
          {error && (
            <p style={{
              color: '#FF4444',
              fontSize: '0.9rem',
              textAlign: 'center',
              marginTop: '-2rem'
            }}>
              {error}
            </p>
          )}
        </>
      )}
    </main>
  );
}
