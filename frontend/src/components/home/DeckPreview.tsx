'use client'

import Image from 'next/image'

interface DeckPreviewProps {
  deckType: string
  fill?: boolean
  sizes?: string
  className?: string
  priority?: boolean
}

export const DECK_IMAGES: Record<string, { id: string; alt: string }> = {
  strategy_deck: {
    id: '1553877522-43269d4ea984',
    alt: 'Chess board representing strategic thinking',
  },
  executive_update: {
    id: '1600880292203-757bb62b4baf',
    alt: 'Executive team reviewing quarterly update',
  },
  proposal_deck: {
    id: '1517048676732-d65bc937f952',
    alt: 'Team collaborating on a business proposal',
  },
  pitch_deck: {
    id: '1559526324-4b87b5e36e44',
    alt: 'Startup pitch presentation to investors',
  },
  board_presentation: {
    id: '1542744173-8e7e53415bb0',
    alt: 'Formal board of directors meeting',
  },
  research_summary: {
    id: '1551288049-bebda4e38f71',
    alt: 'Data analytics and research on screen',
  },
  project_status: {
    id: '1460925895917-afdab827c52f',
    alt: 'Project management dashboard overview',
  },
  training_deck: {
    id: '1524178232363-1fb2b075b655',
    alt: 'Corporate training and learning session',
  },
}

export function deckImageSrc(deckType: string, width = 900) {
  const img = DECK_IMAGES[deckType]
  if (!img) return ''
  return `https://images.unsplash.com/photo-${img.id}?auto=format&fit=crop&w=${width}&q=80`
}

export default function DeckPreview({
  deckType,
  fill = true,
  sizes = '(max-width: 640px) 100vw, 25vw',
  className = '',
  priority = false,
}: DeckPreviewProps) {
  const img = DECK_IMAGES[deckType]
  if (!img) return null

  return (
    <Image
      src={deckImageSrc(deckType)}
      alt={img.alt}
      fill={fill}
      sizes={sizes}
      priority={priority}
      className={`object-cover ${className}`}
    />
  )
}
