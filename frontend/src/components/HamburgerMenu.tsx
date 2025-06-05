'use client';

import { useState } from 'react';
import { Menu } from 'lucide-react';
import Link from 'next/link';

export default function HamburgerMenu() {
  const [menuOpen, setMenuOpen] = useState(false);


  return (
    <>
      {/* Hamburger button */}
      <button
        aria-label="Open navigation menu"
        onClick={() => setMenuOpen(!menuOpen)}
        style={{
          position: 'absolute',
          top: '20px',
          left: '20px',
          zIndex: 200,
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
        }}
      >
        <Menu size={24} color="#3A53F7" />
      </button>

      {/* Sliding menu */}
      <nav
        style={{
          position: 'fixed',
          top: 0,
          left: menuOpen ? 0 : '-250px',
          width: '250px',
          height: '100vh',
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          borderRight: '1px solid rgba(255, 255, 255, 0.2)',
          transition: 'left 0.3s ease-in-out',
          zIndex: 150,
          padding: '5rem 1rem 1rem 1rem',
          color: '#000',
        }}
      >
        <ul style={{ listStyle: 'none', padding: 0, margin: 0, lineHeight: '4rem' }}>
          <li>
            <Link
              href="/"
              style={{
                color: '#000',
                textDecoration: 'none',
                fontSize: '1.4rem'
              }}
            >
              Home
            </Link>
          </li>
          <li>
            <Link
              href="/feedback"
              style={{
                color: '#000',
                textDecoration: 'none',
                fontSize: '1.4rem'
              }}
            >
              Feedback
            </Link>
          </li>
        </ul>
      </nav>
    </>
  );
}
