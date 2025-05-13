'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ChevronLeft } from 'lucide-react';


export default function PreparePage() {
  const [duration, setDuration] = useState('5');
  const [type, setType] = useState('morning');
  const router = useRouter();

  const handleNext = () => {
    router.push('/meditation'); // replace with your actual next route
  };

  return (
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
      <h2
        style={{
          fontFamily: "'Cutive Mono', monospace",
          fontSize: '1.25rem',
          fontWeight: 'lighter',
          color: '#B0B0B0',
          marginBottom: '3rem',
        }}
      >
        Your experience is almost ready:
      </h2>
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
          <option value="1">3</option>
          <option value="3">5</option>
          <option value="8">10</option>
          <option value="13">15</option>
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
          <option value="self-love">self-love</option>
          <option value="stress release">stress release</option>
          <option value="conflict resolution">post-conflict</option>
          <option value="afternoon">evening</option>
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
          onClick={handleNext}
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
  );
}
