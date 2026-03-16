"""
DeckClaude Multi-Agent System — Agents Package

This package contains all specialized agents for the PowerPoint generation pipeline:
- BaseAgent: Abstract base class and LLM client
- IntentAgent: Classifies user intent and presentation requirements
- BlueprintAgent: Generates slide-by-slide structural blueprint
- ResearchDataAgent: Extracts and processes uploaded data/documents
- InsightGeneratorAgent: Produces consulting-quality insights per slide
- ChartGeneratorAgent: Creates matplotlib charts with brand styling
- SmartArtAgent: Draws SmartArt-style diagrams using python-pptx shapes
- ImageIntelligenceAgent: Fetches or generates contextual slide images
- VisualDesignAgent: Decides visual type and layout for each slide
- SlideCriticAgent: Reviews and scores slides against consulting standards
- DeckBuilderAgent: Assembles final PowerPoint file using python-pptx
"""
