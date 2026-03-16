"""
ResearchDataAgent — Extracts, processes, and summarizes uploaded data and documents.
Supports: PDF (PyMuPDF), CSV, Excel (pandas), JSON files.
Outputs structured research_context consumed by InsightGeneratorAgent.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Union
from .base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class ResearchDataAgent(BaseAgent):
    """
    Processes uploaded files and extracts structured research context.

    Input state keys:
        file_path (str): Path to uploaded file (PDF/CSV/Excel/JSON)
        file_content (bytes, optional): Raw file bytes (alternative to file_path)
        file_name (str, optional): Original filename for type detection
        prompt (str, optional): User's original prompt for context

    Output (AgentResult.data):
        {
          research_context: {
            file_name, file_type, text_content, tables, statistics,
            key_facts, data_summary, column_profiles, row_count
          },
          research_summary: {
            overview, key_metrics, trends, data_quality_notes
          }
        }
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".csv", ".xlsx", ".xls", ".json", ".txt"}

    def __init__(self):
        super().__init__(
            name="ResearchDataAgent",
            description="Extracts and summarizes data from PDF, CSV, Excel, and JSON files",
        )

    def _detect_file_type(self, file_path: Optional[str], file_name: Optional[str]) -> str:
        """Determine file type from path or filename extension."""
        source = file_path or file_name or ""
        ext = Path(source).suffix.lower()
        if ext in self.SUPPORTED_EXTENSIONS:
            return ext
        return ".txt"  # fallback

    def extract_pdf(self, file_path: str) -> dict:
        """Extract text and metadata from PDF using PyMuPDF (fitz)."""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("PyMuPDF required for PDF processing. Install with: pip install PyMuPDF")

        doc = fitz.open(file_path)
        full_text = []
        page_count = len(doc)

        for page_num in range(page_count):
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                full_text.append(f"[Page {page_num + 1}]\n{text.strip()}")

        doc.close()
        combined_text = "\n\n".join(full_text)

        return {
            "file_type": "pdf",
            "page_count": page_count,
            "text_content": combined_text,
            "char_count": len(combined_text),
            "tables": [],
            "statistics": {},
        }

    def extract_csv(self, file_path: str) -> dict:
        """Load CSV with pandas and compute statistical summary."""
        try:
            import pandas as pd
            import numpy as np
        except ImportError:
            raise ImportError("pandas required for CSV processing. Install with: pip install pandas")

        df = pd.read_csv(file_path)
        return self._dataframe_to_research(df, "csv")

    def extract_excel(self, file_path: str) -> dict:
        """Load Excel file (all sheets) and compute summary."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas+openpyxl required for Excel processing.")

        sheets = pd.read_excel(file_path, sheet_name=None)
        all_data = {}
        for sheet_name, df in sheets.items():
            all_data[sheet_name] = self._dataframe_to_research(df, "excel")

        # Use the largest sheet as primary
        primary_key = max(all_data.keys(), key=lambda k: all_data[k].get("row_count", 0))
        primary = all_data[primary_key]
        primary["sheet_names"] = list(sheets.keys())
        primary["all_sheets"] = all_data
        return primary

    def extract_json(self, file_path: str) -> dict:
        """Load JSON file and extract structure summary."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            try:
                import pandas as pd
                df = pd.json_normalize(data)
                return self._dataframe_to_research(df, "json")
            except Exception:
                pass

        # Flat JSON object
        text_repr = json.dumps(data, indent=2)
        return {
            "file_type": "json",
            "text_content": text_repr[:8000],
            "tables": [],
            "statistics": {},
            "row_count": len(data) if isinstance(data, (list, dict)) else 0,
            "column_profiles": {},
        }

    def extract_text(self, file_path: str) -> dict:
        """Load plain text file."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        return {
            "file_type": "txt",
            "text_content": text,
            "tables": [],
            "statistics": {},
            "row_count": len(text.splitlines()),
            "column_profiles": {},
        }

    def _dataframe_to_research(self, df, file_type: str) -> dict:
        """Convert a pandas DataFrame to a structured research context dict."""
        import numpy as np

        row_count, col_count = df.shape
        column_profiles = {}

        for col in df.columns:
            series = df[col]
            dtype = str(series.dtype)
            profile = {
                "dtype": dtype,
                "null_count": int(series.isna().sum()),
                "unique_count": int(series.nunique()),
            }

            if series.dtype in (float, int) or "int" in dtype or "float" in dtype:
                non_null = series.dropna()
                if len(non_null) > 0:
                    profile.update({
                        "min": float(non_null.min()),
                        "max": float(non_null.max()),
                        "mean": round(float(non_null.mean()), 4),
                        "median": float(non_null.median()),
                        "std": round(float(non_null.std()), 4),
                        "pct_change_overall": round(
                            ((float(non_null.iloc[-1]) - float(non_null.iloc[0])) / float(non_null.iloc[0]) * 100)
                            if float(non_null.iloc[0]) != 0 and len(non_null) > 1 else 0, 2
                        ),
                    })
            else:
                top_values = series.value_counts().head(5).to_dict()
                profile["top_values"] = {str(k): int(v) for k, v in top_values.items()}

            column_profiles[str(col)] = profile

        # Compute descriptive statistics for numeric columns
        try:
            numeric_df = df.select_dtypes(include=[float, int])
            stats_dict = {}
            if not numeric_df.empty:
                desc = numeric_df.describe()
                stats_dict = {col: desc[col].to_dict() for col in desc.columns}
        except Exception:
            stats_dict = {}

        # Build text representation of first 10 rows
        preview_text = df.head(10).to_string(index=False)

        # Sample table for downstream use
        table_records = df.head(20).fillna("").to_dict(orient="records")
        # Convert numeric types for JSON serialization
        for record in table_records:
            for k, v in record.items():
                if hasattr(v, "item"):  # numpy scalar
                    record[k] = v.item()

        return {
            "file_type": file_type,
            "row_count": row_count,
            "col_count": col_count,
            "columns": list(df.columns),
            "text_content": preview_text,
            "tables": [{"headers": list(df.columns), "rows": table_records}],
            "statistics": stats_dict,
            "column_profiles": column_profiles,
        }

    def _generate_research_summary(self, extracted: dict, user_prompt: str) -> dict:
        """Use LLM to generate a high-level research summary from extracted data."""
        # Build compact context for LLM
        context_parts = []

        if extracted.get("text_content"):
            excerpt = extracted["text_content"][:4000]
            context_parts.append(f"DATA EXCERPT:\n{excerpt}")

        if extracted.get("column_profiles"):
            profiles_str = json.dumps(extracted["column_profiles"], indent=2)[:3000]
            context_parts.append(f"COLUMN PROFILES:\n{profiles_str}")

        if extracted.get("statistics"):
            stats_str = json.dumps(extracted["statistics"], indent=2)[:2000]
            context_parts.append(f"STATISTICS:\n{stats_str}")

        context_parts.append(f"\nUSER PROMPT: {user_prompt}")
        context_parts.append(
            "\nBased on this data, provide a JSON summary with fields: "
            "overview (string), key_metrics (list of {metric, value, interpretation}), "
            "trends (list of string), data_quality_notes (list of string), "
            "chart_recommendations (list of {chart_type, x_column, y_column, title})"
        )

        system = (
            "You are a senior data analyst. Analyze the provided data and return a structured "
            "JSON summary. Focus on business insights, not technical descriptions."
        )

        try:
            raw = self.llm.complete(
                system_prompt=system,
                user_message="\n\n".join(context_parts),
                max_tokens=2500,
            )
            summary = self.parse_json(raw)
        except Exception as e:
            self.logger.warning(f"LLM summary generation failed: {e}; using fallback.")
            summary = {
                "overview": f"Dataset with {extracted.get('row_count', '?')} rows and {extracted.get('col_count', '?')} columns.",
                "key_metrics": [],
                "trends": ["Trend analysis unavailable — LLM summary failed."],
                "data_quality_notes": [],
                "chart_recommendations": [],
            }

        return summary

    def process_file(self, file_path: str, file_name: Optional[str] = None, user_prompt: str = "") -> dict:
        """Main entry point: detect file type, extract content, generate LLM summary."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        effective_name = file_name or os.path.basename(file_path)
        file_type = self._detect_file_type(file_path, effective_name)

        self.logger.info(f"Processing file: {effective_name} (type={file_type})")

        extractors = {
            ".pdf": self.extract_pdf,
            ".csv": self.extract_csv,
            ".xlsx": self.extract_excel,
            ".xls": self.extract_excel,
            ".json": self.extract_json,
            ".txt": self.extract_text,
        }

        extractor = extractors.get(file_type, self.extract_text)
        extracted = extractor(file_path)
        extracted["file_name"] = effective_name
        extracted["file_path"] = file_path

        summary = self._generate_research_summary(extracted, user_prompt)

        return {
            "research_context": extracted,
            "research_summary": summary,
        }

    def execute(self, state: dict) -> AgentResult:
        """
        Execute file processing from workflow state.

        State keys consumed: file_path, file_name, prompt
        State keys produced: research_context, research_summary
        """
        try:
            file_path = state.get("file_path")
            if not file_path:
                # No file uploaded — return empty research context
                self.logger.info("No file_path in state; skipping research extraction.")
                return AgentResult(
                    success=True,
                    data={"research_context": None, "research_summary": None},
                    metadata={"skipped": True, "reason": "no_file"},
                )

            file_name = state.get("file_name") or os.path.basename(file_path)
            user_prompt = state.get("prompt", "")

            result_data = self.process_file(file_path, file_name, user_prompt)

            self.logger.info(
                f"Research extraction complete: {file_name} | "
                f"rows={result_data['research_context'].get('row_count', '?')}"
            )

            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "file_name": file_name,
                    "file_type": result_data["research_context"].get("file_type"),
                    "row_count": result_data["research_context"].get("row_count"),
                },
            )

        except Exception as e:
            self.logger.error(f"ResearchDataAgent failed: {e}", exc_info=True)
            return AgentResult(success=False, data=None, error=str(e))
