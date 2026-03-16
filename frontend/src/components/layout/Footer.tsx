import Link from 'next/link'

const PRODUCT_LINKS = [
  { label: 'Generate Deck', href: '/generate' },
  { label: 'Gallery', href: '/gallery' },
]

const DECK_TYPE_LINKS = [
  { label: 'Strategy Deck', href: '/generate?type=strategy_deck' },
  { label: 'Pitch Deck', href: '/generate?type=pitch_deck' },
  { label: 'Executive Update', href: '/generate?type=executive_update' },
  { label: 'Board Presentation', href: '/generate?type=board_presentation' },
  { label: 'Proposal Deck', href: '/generate?type=proposal_deck' },
]

export default function Footer() {
  return (
    <footer className="border-t border-white/5 bg-void-900 relative overflow-hidden">
      {/* Gradient top line */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-brand-blue/30 to-transparent" />

      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
          {/* Brand */}
          <div className="md:col-span-1">
            <Link href="/" className="inline-block mb-4">
              <span className="text-xl font-black gradient-text">✦ Deck-star</span>
            </Link>
            <p className="text-void-400 text-sm leading-relaxed">
              Prompt. Generate. Present.
            </p>
            <p className="text-void-400 text-sm mt-3 leading-relaxed">
              AI-powered consulting presentations, on demand.
            </p>
          </div>

          {/* Product */}
          <div>
            <h4 className="text-void-200 font-semibold text-sm mb-4 uppercase tracking-wider">Product</h4>
            <ul className="space-y-3">
              {PRODUCT_LINKS.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-void-400 hover:text-brand-violet text-sm transition-colors duration-200"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Deck Types */}
          <div>
            <h4 className="text-void-200 font-semibold text-sm mb-4 uppercase tracking-wider">Deck Types</h4>
            <ul className="space-y-3">
              {DECK_TYPE_LINKS.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-void-400 hover:text-brand-violet text-sm transition-colors duration-200"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-16 pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-void-500 text-sm">
            &copy; {new Date().getFullYear()} Deck-star. All rights reserved.
          </p>
          <p className="text-void-500 text-sm">
            Built with{' '}
            <span className="gradient-text font-semibold">12 AI agents</span>{' '}
            for consulting excellence.
          </p>
        </div>
      </div>
    </footer>
  )
}
