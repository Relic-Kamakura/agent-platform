import type { ReactNode } from 'react';

export const metadata = { title: '競合リサーチエージェント' };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ja">
      <body style={{ fontFamily: 'sans-serif', maxWidth: 760, margin: '2rem auto', padding: '0 1rem' }}>
        {children}
      </body>
    </html>
  );
}
