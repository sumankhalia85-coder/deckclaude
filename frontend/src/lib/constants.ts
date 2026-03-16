export const DECK_TYPES = [
  { value: 'strategy_deck', label: 'Strategy Deck', icon: '🎯', description: 'Long-range strategic plans, market entry, positioning' },
  { value: 'executive_update', label: 'Executive Update', icon: '📊', description: 'C-suite briefings, QBRs, board updates' },
  { value: 'proposal_deck', label: 'Proposal Deck', icon: '📋', description: 'Sales proposals, RFP responses, partnerships' },
  { value: 'pitch_deck', label: 'Pitch Deck', icon: '🚀', description: 'Startup investor pitches, fundraising decks' },
  { value: 'board_presentation', label: 'Board Presentation', icon: '🏛️', description: 'Formal board of directors presentations' },
  { value: 'research_summary', label: 'Research Summary', icon: '🔬', description: 'Market research, competitive analysis, insights' },
  { value: 'project_status', label: 'Project Status', icon: '📌', description: 'Progress updates, milestone reviews, risk dashboards' },
  { value: 'training_deck', label: 'Training Deck', icon: '🎓', description: 'Employee training, onboarding, skills development' },
]

export const THEMES = [
  { value: 'mckinsey', label: 'McKinsey', primary: '#002F5F', secondary: '#0070C0', accent: '#D04A02' },
  { value: 'default', label: 'Corporate', primary: '#002060', secondary: '#00B0F0', accent: '#FF6B35' },
  { value: 'bain', label: 'Bain', primary: '#CC0000', secondary: '#990000', accent: '#333333' },
  { value: 'bcg', label: 'BCG', primary: '#00704A', secondary: '#005C3B', accent: '#6D6E71' },
  { value: 'ey', label: 'EY', primary: '#FFE600', secondary: '#2E2E38', accent: '#FFFFFF' },
  { value: 'deloitte_black', label: 'Deloitte', primary: '#000000', secondary: '#86BC25', accent: '#0076A8' },
  { value: 'startup_minimal', label: 'Minimal', primary: '#111111', secondary: '#444444', accent: '#6C63FF' },
  { value: 'dark_tech', label: 'Dark Tech', primary: '#1A1A2E', secondary: '#16213E', accent: '#00D4FF' },
  { value: 'investor_pitch', label: 'Investor', primary: '#0D0D0D', secondary: '#1A1A2E', accent: '#C9A84C' },
  { value: 'consulting_green', label: 'Green', primary: '#006B3C', secondary: '#00A651', accent: '#F7941D' },
]

export const EXAMPLE_PROMPTS = [
  'Generate an executive strategy deck on AI adoption opportunities in retail for a Fortune 500 audience',
  'Create a 12-slide investor pitch deck for a B2B SaaS startup raising Series A',
  'Build a board presentation on Q4 financial performance and FY2026 outlook',
  'Generate a proposal deck for digital transformation services in the healthcare sector',
  'Create a research summary on global supply chain disruption trends and strategic responses',
  'Build a project status update for a cloud migration program with risk register',
]

export const AGENTS = [
  { id: 'intent', label: 'Intent Detection', description: 'Classifying your request' },
  { id: 'blueprint', label: 'Blueprint Design', description: 'Structuring slide outline' },
  { id: 'research', label: 'Data Research', description: 'Extracting insights' },
  { id: 'insights', label: 'Insight Generation', description: 'Crafting narratives' },
  { id: 'design', label: 'Visual Design', description: 'Planning visuals' },
  { id: 'charts', label: 'Chart Generation', description: 'Building data charts' },
  { id: 'images', label: 'Image Selection', description: 'Sourcing imagery' },
  { id: 'builder', label: 'Deck Assembly', description: 'Composing slides' },
  { id: 'critic', label: 'Quality Review', description: 'Refining output' },
]
