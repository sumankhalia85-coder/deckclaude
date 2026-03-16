export default function Loading() {
  return (
    <div className="min-h-screen bg-void-900 flex flex-col items-center justify-center gap-4">
      <div className="relative">
        <div
          className="text-6xl font-black gradient-text animate-pulse"
          style={{ animationDuration: '1.5s' }}
        >
          ✦
        </div>
        <div className="absolute inset-0 blur-xl bg-brand-purple/30 -z-10 rounded-full" />
      </div>
      <p className="text-void-400 text-sm font-medium tracking-wide">Deck-star</p>
      <div className="flex gap-1.5 mt-2">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-1.5 h-1.5 rounded-full bg-brand-violet animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  )
}
