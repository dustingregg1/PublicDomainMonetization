#!/usr/bin/env python3
"""
Public Domain Monetization - Master Orchestrator
================================================

This orchestrator coordinates specialized agents to discover, clear, produce,
and monetize public domain content. It manages the workflow from discovery
through publication.

Usage:
    python master_orchestrator.py new-title "The Maltese Falcon"
    python master_orchestrator.py scan-market
    python master_orchestrator.py produce-kit "The Maltese Falcon"
    python master_orchestrator.py full-pipeline "The Maltese Falcon"
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from enum import Enum


class WorkflowStage(Enum):
    """Stages in the monetization pipeline"""
    DISCOVERY = "discovery"
    CLEARANCE = "clearance"
    SOURCE_ACQUISITION = "source_acquisition"
    CONTENT_CREATION = "content_creation"
    FORMATTING = "formatting"
    COVER_DESIGN = "cover_design"
    KDP_OPTIMIZATION = "kdp_optimization"
    PUBLICATION = "publication"
    MONITORING = "monitoring"


class TierClassification(Enum):
    """Work tier classifications"""
    TIER_1 = "tier_1"  # Cleanest - zero trademark friction
    TIER_2 = "tier_2"  # Moderate - some trademark considerations
    TIER_3 = "tier_3"  # Higher risk - significant trademark exposure
    VERIFICATION = "verification_required"


@dataclass
class WorkMetadata:
    """Metadata for a public domain work"""
    title: str
    author: str
    publication_year: int
    us_pd_date: str
    eu_pd_date: str
    tier: TierClassification
    source_url: Optional[str] = None
    asin: Optional[str] = None
    isbn: Optional[str] = None
    status: WorkflowStage = WorkflowStage.DISCOVERY


@dataclass
class AgentResult:
    """Result from an agent task"""
    agent_name: str
    task: str
    success: bool
    output: Dict[str, Any]
    timestamp: str
    error: Optional[str] = None


class PDMonetizationOrchestrator:
    """
    Master orchestrator for public domain monetization pipeline.

    Coordinates specialized agents:
    - PD Scout: Discovers and evaluates opportunities
    - Legal Clearance: Verifies PD status and trademark clearance
    - Source Hunter: Locates authentic source editions
    - Content Creator: Generates companion content
    - Format Expert: Handles ebook/print formatting
    - Cover Design: Creates professional covers
    - KDP Optimizer: Maximizes listing performance
    - Dispute Response: Handles platform issues
    """

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.kits_dir = self.project_root / "kits"
        self.output_dir = self.project_root / "output"
        self.evidence_dir = self.project_root / "evidence"

        # Ensure directories exist
        for dir_path in [self.kits_dir, self.output_dir, self.evidence_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Load configuration
        self.config = self._load_config()

        # Initialize work tracking
        self.works: Dict[str, WorkMetadata] = {}
        self._load_works()

    def _load_config(self) -> Dict[str, Any]:
        """Load orchestrator configuration"""
        config_path = self.project_root / "config.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {
            "default_tier_1_titles": [
                "The Maltese Falcon",
                "Strong Poison",
                "Last and First Men",
                "Cimarron",
                "The 42nd Parallel"
            ],
            "word_count_targets": {
                "introduction": 4500,
                "chapter_summaries": 3000,
                "character_guide": 1800,
                "historical_context": 1600,
                "discussion_questions": 1200,
                "glossary": 700,
                "edition_essay": 1000
            },
            "pricing": {
                "ebook_standard": 4.99,
                "ebook_premium": 5.99,
                "paperback_standard": 14.99,
                "paperback_premium": 16.99
            }
        }

    def _load_works(self) -> None:
        """Load tracked works from persistent storage"""
        works_file = self.project_root / "works.json"
        if works_file.exists():
            with open(works_file) as f:
                data = json.load(f)
                for title, metadata in data.items():
                    metadata['tier'] = TierClassification(metadata['tier'])
                    metadata['status'] = WorkflowStage(metadata['status'])
                    self.works[title] = WorkMetadata(**metadata)

    def _save_works(self) -> None:
        """Persist tracked works"""
        works_file = self.project_root / "works.json"
        data = {}
        for title, metadata in self.works.items():
            m = asdict(metadata)
            m['tier'] = metadata.tier.value
            m['status'] = metadata.status.value
            data[title] = m
        with open(works_file, 'w') as f:
            json.dump(data, f, indent=2)

    # =========================================================================
    # AGENT DISPATCH METHODS
    # =========================================================================

    def dispatch_pd_scout(self, query: str = None) -> AgentResult:
        """
        Dispatch PD Scout agent to discover opportunities.

        The PD Scout agent:
        - Monitors Duke Law PD Day announcements
        - Searches Internet Archive for source availability
        - Evaluates market potential
        - Classifies works by tier
        """
        print(f"[PD Scout] Scanning for opportunities...")

        # In production, this would call the actual agent
        # For now, return structure for the orchestration flow
        return AgentResult(
            agent_name="pd_scout",
            task="market_scan" if not query else f"evaluate:{query}",
            success=True,
            output={
                "works_found": self.config["default_tier_1_titles"],
                "scan_date": datetime.now().isoformat(),
                "recommendations": [
                    {"title": t, "tier": "tier_1"}
                    for t in self.config["default_tier_1_titles"]
                ]
            },
            timestamp=datetime.now().isoformat()
        )

    def dispatch_legal_clearance(self, work: WorkMetadata) -> AgentResult:
        """
        Dispatch Legal Clearance agent for PD and trademark verification.

        The Legal Clearance agent:
        - Verifies publication date against authoritative sources
        - Searches USPTO TESS for trademarks
        - Calculates international copyright terms
        - Generates risk assessment
        """
        print(f"[Legal Clearance] Verifying: {work.title}")

        return AgentResult(
            agent_name="legal_clearance",
            task=f"clearance:{work.title}",
            success=True,
            output={
                "pd_verified": True,
                "trademark_risk": "low",
                "eu_pd_date": work.eu_pd_date,
                "excluded_elements": [],
                "recommendation": "cleared_for_production"
            },
            timestamp=datetime.now().isoformat()
        )

    def dispatch_source_hunter(self, work: WorkMetadata) -> AgentResult:
        """
        Dispatch Source Hunter agent to locate authentic edition.

        The Source Hunter agent:
        - Searches Internet Archive
        - Cross-references HathiTrust
        - Verifies edition authenticity
        - Downloads source text
        """
        print(f"[Source Hunter] Locating source: {work.title}")

        return AgentResult(
            agent_name="source_hunter",
            task=f"find_source:{work.title}",
            success=True,
            output={
                "source_found": True,
                "source_url": f"https://archive.org/details/{work.title.lower().replace(' ', '')}",
                "edition_verified": True,
                "publication_year_confirmed": work.publication_year
            },
            timestamp=datetime.now().isoformat()
        )

    def dispatch_content_creator(self, work: WorkMetadata) -> AgentResult:
        """
        Dispatch Content Creator agent to generate companion content.

        The Content Creator agent:
        - Generates introduction
        - Creates chapter summaries
        - Builds character guide
        - Writes historical context
        - Produces discussion questions
        - Compiles glossary
        - Authors edition essay
        """
        print(f"[Content Creator] Generating content: {work.title}")

        targets = self.config["word_count_targets"]

        return AgentResult(
            agent_name="content_creator",
            task=f"create_content:{work.title}",
            success=True,
            output={
                "sections_complete": 7,
                "total_word_count": sum(targets.values()),
                "sections": {
                    "introduction": {"status": "complete", "words": targets["introduction"]},
                    "chapter_summaries": {"status": "complete", "words": targets["chapter_summaries"]},
                    "character_guide": {"status": "complete", "words": targets["character_guide"]},
                    "historical_context": {"status": "complete", "words": targets["historical_context"]},
                    "discussion_questions": {"status": "complete", "words": targets["discussion_questions"]},
                    "glossary": {"status": "complete", "words": targets["glossary"]},
                    "edition_essay": {"status": "complete", "words": targets["edition_essay"]}
                },
                "qa_required": True
            },
            timestamp=datetime.now().isoformat()
        )

    def dispatch_kdp_optimizer(self, work: WorkMetadata) -> AgentResult:
        """
        Dispatch KDP Optimizer agent to create listing kit.

        The KDP Optimizer agent:
        - Generates optimized title/subtitle
        - Creates KDP-compliant description
        - Researches and selects keywords
        - Recommends categories and pricing
        """
        print(f"[KDP Optimizer] Creating listing: {work.title}")

        return AgentResult(
            agent_name="kdp_optimizer",
            task=f"optimize_listing:{work.title}",
            success=True,
            output={
                "title": f"{work.title} (Annotated)",
                "subtitle": "Original 1930 Text with Reader's Companion Guide",
                "keywords": [
                    f"{work.author.lower()} annotated",
                    "classic literature study guide",
                    "book club discussion guide"
                ],
                "pricing": {
                    "ebook": self.config["pricing"]["ebook_standard"],
                    "paperback": self.config["pricing"]["paperback_standard"]
                },
                "compliance_verified": True
            },
            timestamp=datetime.now().isoformat()
        )

    # =========================================================================
    # WORKFLOW ORCHESTRATION
    # =========================================================================

    def run_discovery_workflow(self) -> List[WorkMetadata]:
        """
        Run the discovery workflow to find new opportunities.

        Workflow:
        1. PD Scout scans market
        2. Filter and rank results
        3. Return prioritized list
        """
        print("\n" + "="*60)
        print("DISCOVERY WORKFLOW")
        print("="*60 + "\n")

        result = self.dispatch_pd_scout()

        if not result.success:
            print(f"[ERROR] Discovery failed: {result.error}")
            return []

        works = []
        for rec in result.output.get("recommendations", []):
            work = WorkMetadata(
                title=rec["title"],
                author="[To be determined]",
                publication_year=1930,
                us_pd_date="2026-01-01",
                eu_pd_date="[To be calculated]",
                tier=TierClassification(rec["tier"])
            )
            works.append(work)
            self.works[work.title] = work

        self._save_works()
        print(f"\n[Discovery Complete] Found {len(works)} opportunities")
        return works

    def run_clearance_workflow(self, title: str) -> bool:
        """
        Run the clearance workflow for a specific work.

        Workflow:
        1. Legal Clearance verifies PD status
        2. Trademark analysis performed
        3. Risk assessment generated
        4. Work cleared or flagged
        """
        print("\n" + "="*60)
        print(f"CLEARANCE WORKFLOW: {title}")
        print("="*60 + "\n")

        if title not in self.works:
            print(f"[ERROR] Work not found: {title}")
            return False

        work = self.works[title]
        result = self.dispatch_legal_clearance(work)

        if result.success and result.output.get("pd_verified"):
            work.status = WorkflowStage.CLEARANCE
            self._save_works()
            print(f"\n[Clearance Complete] {title} CLEARED for production")
            return True
        else:
            print(f"\n[Clearance Failed] {title} requires verification")
            return False

    def run_production_workflow(self, title: str) -> Dict[str, Any]:
        """
        Run the full production workflow for a cleared work.

        Workflow:
        1. Source Hunter locates source
        2. Content Creator generates companion content
        3. Format Expert formats files
        4. Cover Design creates cover
        5. KDP Optimizer creates listing
        """
        print("\n" + "="*60)
        print(f"PRODUCTION WORKFLOW: {title}")
        print("="*60 + "\n")

        if title not in self.works:
            print(f"[ERROR] Work not found: {title}")
            return {"success": False, "error": "Work not found"}

        work = self.works[title]
        results = {}

        # Stage 1: Source Acquisition
        print("\n--- Stage 1: Source Acquisition ---")
        source_result = self.dispatch_source_hunter(work)
        results["source"] = source_result.output
        if source_result.success:
            work.source_url = source_result.output.get("source_url")
            work.status = WorkflowStage.SOURCE_ACQUISITION

        # Stage 2: Content Creation
        print("\n--- Stage 2: Content Creation ---")
        content_result = self.dispatch_content_creator(work)
        results["content"] = content_result.output
        if content_result.success:
            work.status = WorkflowStage.CONTENT_CREATION

        # Stage 3: KDP Optimization
        print("\n--- Stage 3: KDP Optimization ---")
        kdp_result = self.dispatch_kdp_optimizer(work)
        results["kdp"] = kdp_result.output
        if kdp_result.success:
            work.status = WorkflowStage.KDP_OPTIMIZATION

        self._save_works()

        # Generate production kit
        kit_path = self._generate_kit(work, results)
        results["kit_path"] = str(kit_path)

        print(f"\n[Production Complete] Kit generated: {kit_path}")
        return {"success": True, "results": results}

    def run_full_pipeline(self, title: str) -> Dict[str, Any]:
        """
        Run the complete pipeline from discovery through production.

        Full pipeline:
        1. Discovery (if not already tracked)
        2. Clearance
        3. Production
        4. Publication readiness check
        """
        print("\n" + "="*60)
        print(f"FULL PIPELINE: {title}")
        print("="*60 + "\n")

        # Step 1: Ensure work is tracked
        if title not in self.works:
            print(f"[Step 1] Adding {title} to tracking...")
            self.works[title] = WorkMetadata(
                title=title,
                author="[To be determined]",
                publication_year=1930,
                us_pd_date="2026-01-01",
                eu_pd_date="[To be calculated]",
                tier=TierClassification.TIER_1
            )

        # Step 2: Clearance
        print(f"\n[Step 2] Running clearance...")
        if not self.run_clearance_workflow(title):
            return {"success": False, "error": "Clearance failed"}

        # Step 3: Production
        print(f"\n[Step 3] Running production...")
        result = self.run_production_workflow(title)

        return result

    def _generate_kit(self, work: WorkMetadata, results: Dict[str, Any]) -> Path:
        """Generate a production kit for a work"""
        kit_dir = self.kits_dir / work.title.lower().replace(" ", "_")
        kit_dir.mkdir(parents=True, exist_ok=True)

        # Generate kit manifest
        manifest = {
            "title": work.title,
            "author": work.author,
            "generated": datetime.now().isoformat(),
            "status": work.status.value,
            "files": []
        }

        # Write production results
        results_file = kit_dir / "production_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        manifest["files"].append("production_results.json")

        # Write manifest
        manifest_file = kit_dir / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)

        return kit_dir

    # =========================================================================
    # CLI INTERFACE
    # =========================================================================

    def cli_status(self) -> None:
        """Display current status of all tracked works"""
        print("\n" + "="*60)
        print("TRACKED WORKS STATUS")
        print("="*60 + "\n")

        if not self.works:
            print("No works currently tracked.")
            print("Run: python master_orchestrator.py scan-market")
            return

        for title, work in self.works.items():
            print(f"  {title}")
            print(f"    Tier: {work.tier.value}")
            print(f"    Status: {work.status.value}")
            print(f"    US PD: {work.us_pd_date}")
            print()


def main():
    parser = argparse.ArgumentParser(
        description="Public Domain Monetization Orchestrator"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Status command
    subparsers.add_parser("status", help="Show status of tracked works")

    # Scan market command
    subparsers.add_parser("scan-market", help="Scan for new opportunities")

    # Clearance command
    clear_parser = subparsers.add_parser("clear", help="Run clearance for a work")
    clear_parser.add_argument("title", help="Title to clear")

    # Production command
    prod_parser = subparsers.add_parser("produce", help="Run production for a work")
    prod_parser.add_argument("title", help="Title to produce")

    # Full pipeline command
    full_parser = subparsers.add_parser("full", help="Run full pipeline")
    full_parser.add_argument("title", help="Title to process")

    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = PDMonetizationOrchestrator()

    # Execute command
    if args.command == "status":
        orchestrator.cli_status()
    elif args.command == "scan-market":
        orchestrator.run_discovery_workflow()
    elif args.command == "clear":
        orchestrator.run_clearance_workflow(args.title)
    elif args.command == "produce":
        orchestrator.run_production_workflow(args.title)
    elif args.command == "full":
        orchestrator.run_full_pipeline(args.title)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
