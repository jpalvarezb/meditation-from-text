'use client';

import Head from 'next/head';
import React, { useState } from 'react';
import { ChevronLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import { supabase } from '@/lib/supabaseClient';


export default function JournalEntry() {
  const [text, setText] = useState('');
  const router = useRouter();

  const handleNext = async () => {
  console.log("handleNext triggered");

  sessionStorage.setItem("journal_entry", text);

  const { data: { session }, error: sessionError } = await supabase.auth.getSession();
  if (sessionError) console.error("Session fetch error:", sessionError);

  if (session) {

    const { error: upsertError } = await supabase
      .from('profiles')
      .upsert({ id: session.user.id, email: session.user.email });

    if (upsertError) {
      console.error("Profile upsert failed:", upsertError);
      await supabase.from('bug_reports').insert({
        user_id: session.user.id,
        message: upsertError.message,
        stacktrace: upsertError.stack ?? null,
        page: 'journal',
        metadata: JSON.stringify({ action: 'upsert profile', entry: text }),
      });
    } else {
      console.log("Profile upserted");
    }


    const { error } = await supabase
      .from('user_input')
      .insert({ user_id: session.user.id, entry: text });

    if (error) {
      console.error("Insert failed:", error);
      await supabase.from('bug_reports').insert({
        user_id: session.user.id,
        message: error.message,
        stacktrace: error.stack ?? null,
        page: 'journal',
        metadata: JSON.stringify({ action: 'insert user_input', entry: text }),
      });
    } else {
      console.log("Insert succeeded");
    }
  } else {
    console.warn("No session found, skipping insert");
  }

  router.push("/prepare");
};

  return (
    <ProtectedRoute>
    <main
      style={{
        backgroundColor: '#F9E66B',
        width: '100vw',
        height: '100vh',
        margin: 0,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <Head>
        <meta name="robots" content="noindex, nofollow" />
        <title>Minday Journal – Tailor Your Meditation</title>
        <meta name="description" content="Write freely about your day or feelings. Minday uses your reflections to generate a personalized meditation experience. Your thoughts stay private." />
        <meta property="og:title" content="Minday – AI Personalized Meditations" />
        <meta property="og:description" content="Create tailor made experiences from your day-to-day life. Minday is your private meditation guide." />
      </Head>
      <button
        onClick={() => (window.location.href = '/')}
        style={{
          position: 'absolute',
          background: 'transparent',
          top: '20px',
          left: '20px',
          zIndex: 100,
          border: 'none',
          cursor: 'pointer',
          color: '#333',
        }}
      >
      <ChevronLeft size={24} color="#3A53F7" />
      </button>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="What would you like to meditate on today? (e.g. I'm excited but anxious to be going on a trip next month)"
        autoFocus
        className="entry"
      />

            <div style={{
        position: 'absolute',
        bottom: '20px',
        right: '20px',
        display: 'flex',
        gap: '12px',
        alignItems: 'center'
      }}>
        <button
          style={{
            backgroundColor: '#F9F9F5',
            border: 'none',
            borderRadius: '50%',
            width: '40px',
            height: '40px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer'
          }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" height="20" viewBox="0 0 24 24" width="20" fill="#3A53F7">
          <path d="M12 14c1.66 0 3-1.34 3-3V5a3 3 0 00-6 0v6c0 1.66 1.34 3 3 3z"/>
          <path d="M17.3 11c-.49 2.54-2.69 4.5-5.3 4.5s-4.81-1.96-5.3-4.5H5c.53 3.12 3.07 5.45 6.3 5.91V20h1.4v-3.09c3.23-.46 5.77-2.79 6.3-5.91h-1.7z"/>
          </svg>
        </button>
        <button
          onClick={handleNext}
          style={{
            backgroundColor: '#3A53F7',
            border: 'none',
            borderRadius: '9999px',
            padding: '0.7rem 1.5rem',
            color: '#F9F9F5',
            fontFamily: 'inherit',
            fontSize: '1rem',
            cursor: 'pointer'
          }}
        >
          Next
        </button>
      </div>
      <style jsx>{`
        .entry {
          width: 80%;
          height: 60%;
          background: transparent;
          border: none;
          outline: none;
          resize: none;
          font-family: Helvetica, sans-serif;
          font-weight: lighter;
          font-size: 1.25rem;
          color: #333;
          caret-color: #0A29F4;
        }
        .entry::placeholder {
          color: #B0B0B0; /* light grey */
        }
      `}</style>
    </main>
    </ProtectedRoute>
  );
}
