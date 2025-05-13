'use client';

import { useState, useEffect, useRef } from 'react';
import Orb from '@/components/Orb';
import { Pause } from 'lucide-react';
import HamburgerMenu from '@/components/HamburgerMenu';

export default function LoadingPage() {
  const [loading, setLoading] = useState(true);
  const [playVisible, setPlayVisible] = useState(false);
  const [distortion, setDistortion] = useState(0.5); // exaggerated during loading
  const [isPlaying, setIsPlaying] = useState(false);
  const [showControls, setShowControls] = useState(false);
  const [meditationEnded, setMeditationEnded] = useState(false);
  const [audioPath, setAudioPath] = useState<string | null>(null);
  const didRun = useRef(false);

  useEffect(() => {
    const fetchMeditation = async () => {
      if (didRun.current) return;
      didRun.current = true;

      try {
        const journal_entry = sessionStorage.getItem('journal_entry') || '';
        const duration_minutes = parseInt(sessionStorage.getItem('duration') || '5', 10);
        const meditation_type = sessionStorage.getItem('meditation_type') || 'morning';

        const response = await fetch('http://localhost:8000/meditate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ journal_entry, duration_minutes, meditation_type }),
        });

        if (!response.ok) throw new Error('Meditation generation failed');

        const data = await response.json();
const fullPath = data.final_audio_path;  // e.g. "/app/assets/audio/output/final_20250513_184645.mp3"
const filename = fullPath?.split('/output/').at(-1);  // gives "final_20250513_184645.mp3"
if (filename) setAudioPath(`/output/${filename}`);
      } catch (err) {
        console.error('Failed to fetch meditation:', err);
      }
    };

    fetchMeditation();
  }, []);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (!audioPath) return;

    setLoading(false);
    const duration = 1000;
    const from = 0.5;
    const to = 0.2;
    let start: number | null = null;

    const animate = (timestamp: number) => {
      if (start === null) start = timestamp;
      const elapsed = timestamp - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = from + (to - from) * (1 - Math.pow(1 - progress, 4)); // easeOutQuart
      setDistortion(eased);
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
    setPlayVisible(true);
  }, [audioPath]);

  const handlePlay = () => {
    if (loading) return;
    if (meditationEnded) return;
    if (!audioRef.current) {
      audioRef.current = new Audio(audioPath ?? '/output/final.mp3');
      audioRef.current.addEventListener('ended', () => {
        setIsPlaying(false);
        setShowControls(false);
        setMeditationEnded(true);
      });
    }
    audioRef.current.play();
    setIsPlaying(true);
    setShowControls(true);
  };

  const handleRestart = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.play();
      setIsPlaying(true);
      setShowControls(true);
      setMeditationEnded(false);
    }
  };

  return (
    <main
      style={{
        width: '100vw',
        height: '100vh',
        backgroundColor: '#FDFBEF',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        flexDirection: 'column',
        fontFamily: "'Cutive Mono', monospace",
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {loading && (
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
        whiteSpace: 'pre-line',
      }}
    >
          Creating your{'\n'}meditation...
        </div>
      )}

      <div
        onClick={!showControls ? handlePlay : undefined}
        style={{
          position: 'relative',
          cursor: !showControls ? 'pointer' : 'default',
          width: '100%',
          height: 'auto',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <Orb
          triggerTransition={false}
          distortion={distortion}
        />
        {playVisible && !showControls && !meditationEnded && (
          <div
            style={{
              position: 'absolute',
              color: '#000',
              fontFamily: 'inherit',
              fontSize: '1.2rem',
              userSelect: 'none',
              pointerEvents: 'none',
            }}
          >
            Press to play
          </div>
        )}
      </div>
      {!meditationEnded && (
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
          {showControls
            ? 'Wherever you are, be there totally.'
            : 'You may start making yourself comfortable.'}
        </p>
      )}
      <HamburgerMenu />

      {showControls && (
        <div
          style={{
            position: 'absolute',
            zIndex: 100,
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '3rem',
          }}
        >
          <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="8" width="3" height="20" fill="black" rx="1"/>
            <path d="M27 9C27 8.44772 26.5523 8 26 8C25.8257 8 25.6554 8.04878 25.5 8.14038L9.5 18.1404C9.19002 18.3164 9 18.6454 9 19C9 19.3546 9.19002 19.6836 9.5 19.8596L25.5 29.8596C25.6554 29.9512 25.8257 30 26 30C26.5523 30 27 29.5523 27 29V9Z" fill="black"/>
          </svg>
          <div
            style={{
              cursor: 'pointer',
              width: '60px',
              height: '60px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            onClick={() => {
              if (audioRef.current) {
                if (isPlaying) {
                  audioRef.current.pause();
                } else {
                  audioRef.current.play();
                }
                setIsPlaying(!isPlaying);
              }
            }}
          >
            {isPlaying ? (
              <Pause size={40} strokeWidth={0} color="black" fill="black" />
            ) : (
              <svg
                width="55"
                height="55"
                viewBox="0 0 48 48"
                xmlns="http://www.w3.org/2000/svg"
                style={{ alignSelf: 'center' }}
              >
                <path
                  d="M16 12C16 11.4477 16.4477 11 17 11C17.2985 11 17.5825 11.1054 17.8 11.3L34.8 23.3C35.1685 23.6015 35.1685 24.1685 34.8 24.47L17.8 36.47C17.5825 36.6646 17.2985 36.77 17 36.77C16.4477 36.77 16 36.3223 16 35.77V12Z"
                  fill="black"
                />
              </svg>
            )}
          </div>
          <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="27" y="8" width="3" height="20" fill="black" rx="1"/>
            <path d="M9 27C9 27.5523 9.44772 28 10 28C10.1743 28 10.3446 27.9512 10.5 27.8596L26.5 17.8596C26.81 17.6836 27 17.3546 27 17C27 16.6454 26.81 16.3164 26.5 16.1404L10.5 6.14038C10.3446 6.04878 10.1743 6 10 6C9.44772 6 9 6.44772 9 7V27Z" fill="black"/>
          </svg>
        </div>
      )}
      {meditationEnded && (
        <>
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              color: '#000',
              fontFamily: 'Cutive Mono, monospace',
              fontSize: '1.25rem',
              pointerEvents: 'none',
            }}
          >
            Meditation ended
          </div>
          <button
            onClick={handleRestart}
            style={{
              position: 'absolute',
              top: '85%',
              left: '50%',
              transform: 'translateX(-50%)',
              backgroundColor: '#3A53F7',
              color: 'white',
              border: 'none',
              padding: '0.6rem 2rem',
              borderRadius: '20px',
              fontFamily: 'Cutive Mono, monospace',
              fontSize: '1rem',
              cursor: 'pointer',
              zIndex: 100,
            }}
          >
            Restart
          </button>
        </>
      )}
    </main>
  );
}
