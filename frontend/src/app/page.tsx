import Navbar from '@/components/layout/Navbar'
import HeroSection from '@/components/home/HeroSection'
import FeaturesSection from '@/components/home/FeaturesSection'
import HowItWorksSection from '@/components/home/HowItWorksSection'
import DeckTypesSection from '@/components/home/DeckTypesSection'
import ThemesSection from '@/components/home/ThemesSection'
import Footer from '@/components/layout/Footer'

export default function HomePage() {
  return (
    <main className="min-h-screen bg-void-900 grid-bg">
      <Navbar />
      <HeroSection />
      <FeaturesSection />
      <HowItWorksSection />
      <DeckTypesSection />
      <ThemesSection />
      <Footer />
    </main>
  )
}
