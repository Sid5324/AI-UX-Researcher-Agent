import type { Metadata } from 'next'
import { Manrope } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/providers'
import { Toaster } from '@/components/ui/toaster'
import { ConnectionStatus } from '@/components/ui/ConnectionStatus'

const manrope = Manrope({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Agentic Research AI - Autonomous Product Research',
  description: 'AI-powered autonomous product research platform that generates complete PRDs, designs, and validation in minutes.',
  keywords: ['AI', 'Product Research', 'Automation', 'UX Research', 'Product Management'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={manrope.className}>
        <Providers>
          {children}
          <Toaster />
          <ConnectionStatus />
        </Providers>
      </body>
    </html>
  )
}
