import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'EW Radar & Emitter Simulation Suite',
  description: 'Modular Electronic Warfare Radar & Emitter Simulation Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <main>{children}</main>
      </body>
    </html>
  );
}
