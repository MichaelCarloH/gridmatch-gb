import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'GridMatch GB',
  description: 'Clean power forecasting and matching prototype.'
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en-GB"><body>{children}</body></html>;
}
