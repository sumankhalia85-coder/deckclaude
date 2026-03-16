import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Toaster } from 'sonner'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })

export const metadata: Metadata = {
  title: 'Deck-star | AI Presentation Generator',
  description: 'Generate consulting-grade PowerPoint presentations with AI. Prompt. Generate. Present.',
  keywords: ['AI presentations', 'PowerPoint generator', 'consulting decks', 'Deck-star'],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans bg-void-900 text-void-50 min-h-screen`}>
        {children}
        <Toaster
          position="bottom-right"
          toastOptions={{
            style: {
              background: '#1A1A2E',
              border: '1px solid rgba(124,58,237,0.3)',
              color: '#F0F0FF',
            },
          }}
        />
      </body>
    </html>
  )
}
