'use client';

import Head from 'next/head';
import React, { useState } from 'react';
import { ChevronLeft } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { supabase } from '@/lib/supabaseClient';



export default function FeedbackEntry() {
  const [text, setText] = useState('');
  const [starRating, setStarRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);


  const handleFeedback = async () => {
    try {
      console.log("Submitting feedback:", { star_rating: starRating, feedback_text: text });
      // Get current Supabase session
      const {
        data: { session },
        error: sessionError,
      } = await supabase.auth.getSession();

      if (sessionError) {
        console.error("Error fetching Supabase session:", sessionError);
        alert("Unable to verify user session.");
        return;
      }

      if (!session) {
        alert("You must be logged in to submit feedback.");
        return;
      }

      // Insert into Supabase 'feedback' table
      const { error: insertError } = await supabase
        .from('feedback')
        .insert({
          user_id: session.user.id,
          message: text,
          star_rating: starRating,
          metadata: {},
        });

      if (insertError) {
        console.error("Failed to insert feedback:", insertError);
        alert("Failed to submit feedback. Please try again.");
      } else {
        console.log("Feedback inserted successfully");
        alert("Thanks for your feedback!");
        // Clear inputs
        setText("");
        setStarRating(0);
      }
    } catch (error) {
      console.error("Feedback submission error:", error);
      alert("Failed to submit feedback. Please try again later.");
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
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <Head>
        <title>Minday – Experience Feedback</title>
        <meta name="description" content="Share your experience using Minday and help us improve your meditation journey." />
        <meta property="og:title" content="Minday – Feedback" />
        <meta property="og:description" content="Share your experience using Minday and help us improve your meditation journey." />
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
        placeholder="Your feedback is always welcome..."
        autoFocus
        className="entry"
      />

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
            <div style={{
        position: 'absolute',
        bottom: '20px',
        right: '20px',
        display: 'flex',
        gap: '12px',
        alignItems: 'center'
      }}>
<div style={{
  position: 'absolute',
  bottom: '20px',
  right: '20px',
  display: 'flex',
  alignItems: 'center',
  gap: '24px'
}}>
  <div style={{ display: 'flex', gap: '8px' }}>
    {[1, 2, 3, 4, 5].map((star) => (
      <div
        key={star}
        onMouseEnter={() => setHoverRating(star)}
        onMouseLeave={() => setHoverRating(0)}
        onClick={() => setStarRating(star)}
        style={{ cursor: 'pointer' }}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill={
            hoverRating >= star
              ? 'rgba(10, 41, 244, 0.3)'
              : starRating >= star
              ? '#0A29F4'
              : 'none'
          }
          stroke="#0A29F4"
          strokeWidth="1.2"
          viewBox="0 0 24 24"
          width="24"
          height="24"
        >
          <path d="M12 17.27L18.18 21 16.54 13.97 22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24 7.46 13.97 5.82 21z" />
        </svg>
      </div>
    ))}
  </div>

  <button
    onClick={handleFeedback}
    style={{
      backgroundColor: '#F9F9F5',
      border: 'none',
      borderRadius: '9999px',
      padding: '0.7rem 1.5rem',
      color: '#3A53F7',
      fontFamily: 'inherit',
      fontSize: '1rem',
      cursor: 'pointer'
    }}
  >
    Submit
  </button>
</div>
      </div>
    </main>
    </ProtectedRoute>
  );
}
