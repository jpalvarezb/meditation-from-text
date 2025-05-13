// /src/app/layout.tsx
import './globals.css';
import React from 'react';
import { Cutive_Mono } from 'next/font/google';

const cutiveMono = Cutive_Mono({
  subsets: ['latin'],
  weight: ['400'],
  display: 'swap',
});

export const metadata = {
  title: 'Minday',
  description: 'AI-powered meditation app',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head />
      <body className={cutiveMono.className}>{children}</body>
    </html>
  );
}
