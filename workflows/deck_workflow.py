"""
DeckClaude LangGraph Workflow — Orchestrates the full multi-agent PowerPoint generation pipeline.
Graph: intent → research(conditional) → blueprint → insights → design → charts → images → builder → critic → end
Uses TypedDict state, conditional edges, and Rich progress logging.
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Optional, TypedDict, List, Dict

logger = logging.getLogger(__name__)

# ---- LangGraph State Definition ----

class DeckState(TypedDict, total=False):
    # Input fields
    prompt: str
    form_data: Optional[Dict[str, Any]]
    file_path: Optional[str]
    file_name: Optional[str]
    document_text: Optional[str]
    requested_slides: Optional[int]
    requested_theme: Optional[str]
    requested_deck_type: Optional[str]
    output_path: Optional[str]

    # DataSourceRouter outputs
    dataset_key: Optional[str]
    dataset_description: Optional[str]
    chart_ready_data: Optional[Dict[str, Any]]
    data_source: Optional[str]   # "user_upload" | "backend_csv" | "none"

    # Agent outputs — populated as graph executes
    intent_spec: Optional[Dict[str, Any]]
    research_context: Optional[Dict[str, Any]]
    research_summary: Optional[Dict[str, Any]]
    blueprint: Optional[Dict[str, Any]]
    slide_contents: Optional[List[Dict[str, Any]]]
    visual_plan: Optional[List[Dict[str, Any]]]
    diagram_requests: Optional[List[Dict[str, Any]]]
    chart_files: Optional[Dict[int, Dict[str, Any]]]
    image_files: Optional[Dict[int, Dict[str, Any]]]
    quality_report: Optional[Dict[str, Any]]
    slides_requiring_revision: Optional[List[int]]
    approved_slides: Optional[List[int]]
    slide_index_map: Optional[Dict[int, int]]
    final_output_path: Optional[str]

    # User preferences passed from API
    include_images: Optional[bool]
    include_charts: Optional[bool]
    include_diagrams: Optional[bool]

    # Control flags
    has_file: bool
    errors: List[str]
    warnings: List[str]
    agent_timings: Dict[str, float]


# ---- Agent Node Functions ----

def _update_state_from_result(state: DeckState, result, agent_name: str) -> DeckState:
    """Merge AgentResult.data into state and record timing."""
    if not isinstance(state.get("agent_timings"), dict):
        state["agent_timings"] = {}
    if not isinstance(state.get("errors"), list):
        state["errors"] = []
    if not isinstance(state.get("warnings"), list):
        state["warnings"] = []

    state["agent_timings"][agent_name] = result.execution_time

    if result.success and result.data:
        state.update(result.data)
    elif not result.success:
        error_msg = f"{agent_name}: {result.error}"
        state["errors"].append(error_msg)
        logger.error(f"Agent error — {error_msg}")

    return state


def node_intent(state: DeckState) -> DeckState:
    """Classify user intent and presentation requirements."""
    from agents.intent_agent import IntentAgent
    agent = IntentAgent()
    logger.info("[IntentAgent] Classifying presentation intent...")
    result = agent.safe_execute(dict(state))
    return _update_state_from_result(state, result, "IntentAgent")


def node_data_router(state: DeckState) -> DeckState:
    """
    Match the user's prompt to a backend CSV dataset.
    If a user-uploaded file is already present, this node is a no-op.
    Otherwise, it injects file_path into state so ResearchAgent processes real data.
    """
    from agents.data_router import route
    prompt = state.get("prompt", "")
    existing_file = state.get("file_path")
    logger.info("[DataSourceRouter] Routing prompt to data source...")

    result = route(prompt, existing_file_path=existing_file)

    state["dataset_key"] = result.get("dataset_key")
    state["dataset_description"] = result.get("dataset_description")
    state["chart_ready_data"] = result.get("chart_ready_data", {})
    state["data_source"] = result.get("data_source", "none")

    # Only override file_path when a backend CSV was matched (don't clobber uploads)
    if result.get("data_source") == "backend_csv" and result.get("file_path"):
        state["file_path"] = result["file_path"]
        state["has_file"] = True
        logger.info(f"[DataSourceRouter] Injected backend CSV: {result['file_path']}")
    else:
        logger.info(f"[DataSourceRouter] Data source: {result.get('data_source', 'none')}")

    return state


def node_research(state: DeckState) -> DeckState:
    """Extract and summarize data from uploaded file (conditional — only runs if file exists)."""
    from agents.research_agent import ResearchDataAgent
    agent = ResearchDataAgent()
    logger.info("[ResearchDataAgent] Processing uploaded file...")
    result = agent.safe_execute(dict(state))
    return _update_state_from_result(state, result, "ResearchDataAgent")


def node_blueprint(state: DeckState) -> DeckState:
    """Generate slide-by-slide narrative blueprint using SCQA framework."""
    from agents.blueprint_agent import BlueprintAgent
    agent = BlueprintAgent()
    logger.info("[BlueprintAgent] Generating presentation blueprint...")
    result = agent.safe_execute(dict(state))
    return _update_state_from_result(state, result, "BlueprintAgent")


def node_insights(state: DeckState) -> DeckState:
    """Generate consulting-quality insights for each slide."""
    from agents.insight_agent import InsightGeneratorAgent
    agent = InsightGeneratorAgent()
    logger.info("[InsightGeneratorAgent] Generating slide insights...")
    result = agent.safe_execute(dict(state))
    return _update_state_from_result(state, result, "InsightGeneratorAgent")


def node_design(state: DeckState) -> DeckState:
    """Plan visual type and layout for each slide."""
    from agents.design_agent import VisualDesignAgent
    agent = VisualDesignAgent()
    logger.info("[VisualDesignAgent] Planning visual design...")
    result = agent.safe_execute(dict(state))
    return _update_state_from_result(state, result, "VisualDesignAgent")


def node_charts(state: DeckState) -> DeckState:
    """Generate matplotlib charts for chart-type slides."""
    from agents.chart_agent import ChartGeneratorAgent
    agent = ChartGeneratorAgent()
    logger.info("[ChartGeneratorAgent] Generating charts...")
    result = agent.safe_execute(dict(state))
    return _update_state_from_result(state, result, "ChartGeneratorAgent")


def node_images(state: DeckState) -> DeckState:
    """Fetch or generate contextual images for slides."""
    from agents.image_agent import ImageIntelligenceAgent
    agent = ImageIntelligenceAgent()
    logger.info("[ImageIntelligenceAgent] Acquiring slide images...")
    result = agent.safe_execute(dict(state))
    return _update_state_from_result(state, result, "ImageIntelligenceAgent")


def node_builder(state: DeckState) -> DeckState:
    """Assemble the final PowerPoint presentation."""
    from agents.deck_builder_agent import DeckBuilderAgent
    agent = DeckBuilderAgent()
    logger.info("[DeckBuilderAgent] Building PowerPoint presentation...")
    result = agent.safe_execute(dict(state))
    updated = _update_state_from_result(state, result, "DeckBuilderAgent")
    if result.success and result.data:
        updated["final_output_path"] = result.data.get("output_path")
    return updated


def node_critic(state: DeckState) -> DeckState:
    """Review presentation quality; revise weak slides."""
    from agents.critic_agent import SlideCriticAgent
    agent = SlideCriticAgent()
    logger.info("[SlideCriticAgent] Running quality review...")
    result = agent.safe_execute(dict(state))
    return _update_state_from_result(state, result, "SlideCriticAgent")


def node_rebuild_after_critic(state: DeckState) -> DeckState:
    """
    If critic revised slide contents, rebuild the deck with the improved content.
    Only triggered if slides_requiring_revision is non-empty.
    """
    slides_needing_revision = state.get("slides_requiring_revision", [])
    if not slides_needing_revision:
        logger.info("[Rebuild] No revisions needed; using existing deck.")
        return state

    logger.info(f"[Rebuild] Rebuilding deck with {len(slides_needing_revision)} revised slides...")
    from agents.deck_builder_agent import DeckBuilderAgent
    agent = DeckBuilderAgent()

    # Append "_revised" suffix to output path
    original_path = state.get("final_output_path") or state.get("output_path")
    if original_path:
        p = Path(original_path)
        state["output_path"] = str(p.parent / (p.stem + "_revised" + p.suffix))

    result = agent.safe_execute(dict(state))
    updated = _update_state_from_result(state, result, "DeckBuilderAgent_Rebuild")
    if result.success and result.data:
        updated["final_output_path"] = result.data.get("output_path")
    return updated


# ---- Conditional Edge Functions ----

def should_run_research(state: DeckState) -> str:
    """Route to research node only if a file was uploaded."""
    if state.get("file_path") and Path(state["file_path"]).exists():
        return "research"
    return "blueprint"


def should_rebuild_after_critic(state: DeckState) -> str:
    """Route to rebuild only if there are slides requiring revision."""
    revisions = state.get("slides_requiring_revision", [])
    if revisions:
        return "rebuild"
    return "end"


# ---- Graph Builder ----

def build_graph():
    """
    Build and compile the LangGraph StateGraph for deck generation.
    Returns a compiled runnable graph.
    """
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        raise ImportError(
            "langgraph is required. Install with: pip install langgraph>=0.2.0"
        )

    graph = StateGraph(DeckState)

    # Add all agent nodes
    graph.add_node("intent", node_intent)
    graph.add_node("data_router", node_data_router)
    graph.add_node("research", node_research)
    graph.add_node("blueprint", node_blueprint)
    graph.add_node("insights", node_insights)
    graph.add_node("design", node_design)
    graph.add_node("charts", node_charts)
    graph.add_node("images", node_images)
    graph.add_node("builder", node_builder)
    graph.add_node("critic", node_critic)
    graph.add_node("rebuild", node_rebuild_after_critic)

    # Entry point
    graph.set_entry_point("intent")

    # intent → data_router (always — router is a no-op if file already uploaded)
    graph.add_edge("intent", "data_router")

    # data_router → research or blueprint (conditional on whether a file/CSV was matched)
    graph.add_conditional_edges(
        "data_router",
        should_run_research,
        {"research": "research", "blueprint": "blueprint"},
    )

    # research → blueprint (always, after file processing)
    graph.add_edge("research", "blueprint")

    # Linear pipeline: blueprint → insights → design → charts → images → builder → critic
    graph.add_edge("blueprint", "insights")
    graph.add_edge("insights", "design")
    graph.add_edge("design", "charts")
    graph.add_edge("charts", "images")
    graph.add_edge("images", "builder")
    graph.add_edge("builder", "critic")

    # critic → rebuild or END (conditional on revision needs)
    graph.add_conditional_edges(
        "critic",
        should_rebuild_after_critic,
        {"rebuild": "rebuild", "end": END},
    )
    graph.add_edge("rebuild", END)

    return graph.compile()


# ---- Main Entry Point ----

def run_workflow(user_input: dict, show_progress: bool = True) -> dict:
    """
    Execute the full deck generation workflow.

    Args:
        user_input: dict with keys:
            - prompt (str): Free-text presentation request
            - form_data (dict, optional): Structured form fields
            - file_path (str, optional): Path to uploaded file
            - file_name (str, optional): Original filename
            - requested_slides (int, optional): Slide count override
            - requested_theme (str, optional): Theme override
            - output_path (str, optional): Custom output path

        show_progress (bool): Show Rich progress bar

    Returns:
        dict with keys:
            - success (bool)
            - output_path (str): Path to generated .pptx
            - quality_report (dict): Slide quality scores
            - errors (list): Any errors encountered
            - timings (dict): Per-agent execution times
            - total_time (float): End-to-end wall time
    """
    start_time = time.time()

    # Initialize state
    initial_state: DeckState = {
        "prompt": user_input.get("prompt", ""),
        "form_data": user_input.get("form_data"),
        "file_path": user_input.get("file_path"),
        "file_name": user_input.get("file_name"),
        "document_text": user_input.get("document_text"),
        "requested_slides": user_input.get("requested_slides"),
        "requested_theme": user_input.get("requested_theme"),
        "requested_deck_type": user_input.get("deck_type") or user_input.get("requested_deck_type"),
        "output_path": user_input.get("output_path"),
        "has_file": bool(user_input.get("file_path") and Path(user_input.get("file_path", "")).exists()),
        "include_images": user_input.get("include_images", True),
        "include_charts": user_input.get("include_charts", True),
        "include_diagrams": user_input.get("include_diagrams", True),
        "errors": [],
        "warnings": [],
        "agent_timings": {},
    }

    if show_progress:
        try:
            from rich.console import Console
            from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
            console = Console()
            console.print(f"\n[bold blue]DeckClaude[/bold blue] — Generating: [italic]{initial_state['prompt'][:80]}[/italic]\n")
        except ImportError:
            show_progress = False

    try:
        graph = build_graph()

        if show_progress:
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    TimeElapsedColumn(),
                    console=console,
                ) as progress:
                    task = progress.add_task("Running multi-agent pipeline...", total=None)
                    final_state = graph.invoke(initial_state)
                    progress.update(task, description="Pipeline complete.")
            except Exception:
                final_state = graph.invoke(initial_state)
        else:
            final_state = graph.invoke(initial_state)

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}", exc_info=True)
        return {
            "success": False,
            "output_path": None,
            "quality_report": None,
            "errors": [str(e)],
            "timings": {},
            "total_time": time.time() - start_time,
        }

    total_time = time.time() - start_time
    output_path = final_state.get("final_output_path") or final_state.get("output_path")
    errors = final_state.get("errors", [])
    success = bool(output_path and Path(output_path).exists())

    if show_progress and success:
        try:
            score = final_state.get("quality_report", {}).get("overall_deck_score", "N/A")
            console.print(f"\n[bold green]Done![/bold green] Presentation saved to: [cyan]{output_path}[/cyan]")
            console.print(f"Quality score: [yellow]{score}/10[/yellow] | Total time: {total_time:.1f}s")
            if errors:
                console.print(f"[yellow]Warnings:[/yellow] {len(errors)} issues encountered")
        except Exception:
            pass

    return {
        "success": success,
        "output_path": output_path,
        "quality_report": final_state.get("quality_report"),
        "slide_contents": final_state.get("slide_contents"),
        "blueprint": final_state.get("blueprint"),
        "intent_spec": final_state.get("intent_spec"),
        "errors": errors,
        "timings": final_state.get("agent_timings", {}),
        "total_time": total_time,
    }
