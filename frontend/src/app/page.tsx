'use client';

import Orb from '@/components/Orb';
import HamburgerMenu from '@/components/HamburgerMenu';

export default function HomePage() {
  return (
    <main
      style={{
        position: 'relative',
        width: '100vw',
        height: '100vh',
        margin: 0,
        backgroundColor: '#FDFBEF', // beige
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
      }}
    >
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

      <p
        style={{
          position: 'absolute',
          bottom: '20px',
          width: '100%',
          textAlign: 'center',
          color: '#3A53F7',
          fontFamily: 'Helvetica, sans-serif',
          fontSize: '1.1rem',
          fontWeight: 'lighter',
          margin: 0,
          pointerEvents: 'none',
        }}
      >
        “Choose to be optimistic, it feels better.”
        - Dalai Lama
      </p>
    </main>
  );
}
