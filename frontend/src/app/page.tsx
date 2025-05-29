'use client';

import Head from 'next/head';
import dynamic from 'next/dynamic';
import HamburgerMenu from '@/components/HamburgerMenu';
import ProtectedRoute from '@/components/ProtectedRoute';
const Orb = dynamic(() => import('@/components/Orb'), { ssr: false });

export default function HomePage() {
  return (
    <ProtectedRoute>
    <main
      style={{
        position: 'relative',
        width: '100vw',
        height: '100vh',
        margin: 0,
        backgroundColor: '#FDFBEF', // beige
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
      }}
    >
      <Head>
        <title>Minday – Personalized AI Meditations</title>
        <meta name="description" content="Create tailor made experiences from your day-to-day life. Minday is your private meditation guide." />
        <meta property="og:title" content="Minday – AI Personalized Meditations" />
        <meta property="og:description" content="Create tailor made experiences from your day-to-day life. Minday is your private meditation guide." />
      </Head>

      <HamburgerMenu />

      {/* Overlay text */}
      <div
        style={{
          position: 'absolute',
          zIndex: 100,
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center',
          fontFamily: 'inherit',
          fontSize: '1.25rem',
          color: '#333',
          pointerEvents: 'none',
        }}
      >
        Welcome. <br/>
        Press here to begin
      </div>

      {/* Orb */}
      <Orb triggerTransition />
      <div className="quote-container">
        <p className="quote-text">
          “Choose to be optimistic, it feels better.” – Dalai Lama
        </p>
      </div>
      <style jsx>{`
        .quote-container {
          position: absolute;
          left: 0;
          right: 0;
          padding-inline: 1.5vw;
          box-sizing: border-box;
          pointer-events: none;
        }
        .quote-text {
          text-align: center;
          color: #3A53F7;
          font-family: Helvetica, sans-serif;
          font-size: 1.4rem;
          font-weight: lighter;
          margin: 0;
          pointer-events: none;
        }
        @media (max-width: 600px) {
          .quote-container { bottom: 12vh; }
        }
        @media (min-width: 601px) and (max-width: 1200px) {
          .quote-container { bottom: 10vh; }
        }
        @media (min-width: 1201px) {
          .quote-container { bottom: 6vh; }
        }
      `}</style>
    </main>
    </ProtectedRoute>
  );
}
