import type { Metadata } from 'next';
import { AppShell } from '@/components/layout/app-shell';
import './globals.css';

export const metadata: Metadata = {
  title: {
    default: 'GridMatch GB — Clean power intelligence',
    template: '%s · GridMatch GB'
  },
  description: 'Forecast, match and optimise clean power across Great Britain.'
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en-GB"><body><AppShell>{children}</AppShell></body></html>;
}
