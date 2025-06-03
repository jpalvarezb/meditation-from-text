'use client';

import Head from 'next/head';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ChevronLeft } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { supabase } from '@/lib/supabaseClient';



export default function PreparePage() {
  const [duration, setDuration] = useState('5');
  const [type, setType] = useState('morning');
  const router = useRouter();

  const handleSubmit = async () => {
    const journal_entry = sessionStorage.getItem('journal_entry');
    if (!journal_entry) {
      alert("Missing journal entry. Please return and enter your thoughts.");
      return;
    }
    // Persist selections for potential UI use
    sessionStorage.setItem('duration', duration);
    sessionStorage.setItem('meditation_type', type);

    // Get supabase session
    const { data: { session } } = await supabase.auth.getSession();
    if (session) {
      // Find the record just inserted from the journal page
      const { data: inputs, error: fetchError } = await supabase
        .from('user_input')
        .select('id')
        .eq('user_id', session.user.id)
        .eq('entry', journal_entry)
        .order('created_at', { ascending: false })
        .limit(1);

      if (fetchError || !inputs || inputs.length === 0) {
      console.error('Could not find user_input row:', fetchError);
      await supabase.from('bug_reports').insert({
        user_id: session.user.id,
        message: fetchError?.message || 'Missing user_input row',
        stacktrace: fetchError?.stack ?? null,
        page: 'prepare',
        metadata: JSON.stringify({ duration, meditation_type: type, journal_entry }),
      });
    } else {
      const recordId = inputs[0].id;
      console.log("Updating record ID:", recordId);
      console.log("With values:", {
        minutes: parseInt(duration, 10),
        meditation_type: type,
      });

        const { error: updateError } = await supabase
          .from('user_input')
          .update({ minutes: parseInt(duration, 10), meditation_type: type })
          .eq('id', recordId);
        if (updateError) {
        console.error('Failed to update input row:', updateError);
        await supabase.from('bug_reports').insert({
          user_id: session.user.id,
          message: updateError.message,
          stacktrace: updateError.stack ?? null,
          page: 'prepare',
          metadata: JSON.stringify({ recordId, duration, meditation_type: type }),
        });
      }
    }

    router.push('/meditation');
  }
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
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        textAlign: 'center',
        fontWeight: 'lighter',
        fontFamily: 'Helvetica, sans-serif',
      }}
    >
      <Head>
        <title>Minday Session Creation – Tailor-Made Meditations</title>
        <meta name="description" content="Choose your meditation type and duration. Minday lets you create personalized sessions from your own reflections." />
        <meta property="og:title" content="Minday Session Creation – Tailor-Made Meditations" />
        <meta property="og:description" content="Choose your meditation type and duration. Minday lets you create personalized sessions from your own reflections." />
      </Head>
      <button
        onClick={() => (window.history.back())}
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
      <p style={{ fontSize: '1.5rem', marginBottom: '2rem', color: '#333' }}>
        I’d like a{' '}
        <select
          value={duration}
          onChange={(e) => setDuration(e.target.value)}
          style={{
            fontSize: '1.5rem',
            fontWeight: 'lighter',
            background: 'transparent',
            border: 'none',
            borderBottom: '1px solid #333',
            margin: '0 0.5rem',
            color: '#333',
          }}
        >
          <option value="1">1</option>
          <option value="3">3</option>
          <option value="5">5</option>
          <option value="7">7</option>
        </select>{' '}
        minute{' '}
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          style={{
            fontSize: '1.5rem',
            background: 'transparent',
            border: 'none',
            borderBottom: '1px solid #333',
            margin: '0 0.5rem',
            color: '#333',
            padding: '0',
          }}
        >
          <option value="focus reset">focus</option>
          <option value="morning">morning</option>
          <option value="self-love">self care</option>
          <option value="stress release">stress release</option>
          <option value="conflict resolution">post-conflict</option>
          <option value="evening">afternoon</option>
          <option value="sleep">sleep</option>
        </select>{' '}
        meditation, please.
      </p>

      <div style={{ marginTop: '5rem', display: 'flex', gap: '1rem', justifyContent: 'center' }}>
        <button
          onClick={() => router.push('/')} // go back to homepage
          style={{
            backgroundColor: '#FDFBEF',
            color: '#3A53F7',
            border: 'none',
            borderRadius: '9999px',
            padding: '0.5rem 1.5rem',
            fontFamily: "'Cutive Mono', monospace",
            fontSize: '1rem',
            cursor: 'pointer',
          }}
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          style={{
            backgroundColor: '#3A53F7',
            color: '#F9F9F5',
            border: 'none',
            borderRadius: '9999px',
            padding: '0.5rem 1.5rem',
            fontFamily: "'Cutive Mono', monospace",
            fontSize: '1rem',
            cursor: 'pointer',
          }}
        >
          Submit
        </button>
      </div>
    </main>
    </ProtectedRoute>
  );
}
