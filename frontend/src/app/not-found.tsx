import Link from 'next/link'

export default function NotFound() {
  return (
    <main className="min-h-screen bg-void-900 grid-bg flex items-center justify-center px-6 relative overflow-hidden">
      {/* Background orbs */}
      <div className="orb w-[500px] h-[500px] bg-brand-purple/15 top-[-100px] left-[-200px] animate-float" />
      <div className="orb w-[400px] h-[400px] bg-brand-blue/10 bottom-[-100px] right-[-150px]" style={{ animationDelay: '3s' }} />

      <div className="relative z-10 text-center">
        {/* 404 */}
        <div className="text-[120px] md:text-[160px] font-black gradient-text leading-none mb-4">
          404
        </div>

        {/* Icon */}
        <div className="text-6xl mb-6">✦</div>

        <h1 className="text-3xl md:text-4xl font-bold text-white mb-3">
          This slide doesn&apos;t exist
        </h1>
        <p className="text-void-400 text-base mb-8 max-w-sm mx-auto">
          Looks like this page was cut from the deck. Head back to the presentation.
        </p>

        <Link
          href="/"
          className="inline-flex items-center gap-2 btn-gradient text-white px-8 py-4 rounded-full text-base font-semibold shadow-glow-sm hover:shadow-glow-md transition-all duration-200"
        >
          <span>← Back to Deck-star</span>
        </Link>
      </div>
    </main>
  )
}
