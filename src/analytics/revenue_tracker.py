"""
Revenue Tracking System

Tracks sales and revenue across multiple distribution platforms.
Supports CSV import from platform reports, manual entry, and analytics.
"""

import os
import json
import csv
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Iterator, Callable
from collections import defaultdict

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported distribution platforms."""
    FINDAWAY_VOICES = "findaway_voices"
    GOOGLE_PLAY = "google_play"
    KOBO = "kobo"
    APPLE_BOOKS = "apple_books"
    SCRIBD = "scribd"
    DIRECT_GUMROAD = "direct_gumroad"
    DIRECT_PAYHIP = "direct_payhip"
    OTHER = "other"


class TimeFrame(Enum):
    """Time frame options for reports."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ALL_TIME = "all_time"


class SaleType(Enum):
    """Type of sale transaction."""
    SALE = "sale"
    REFUND = "refund"
    KENP_READ = "kenp_read"  # Kindle Unlimited page reads
    SUBSCRIPTION = "subscription"


@dataclass
class SalesRecord:
    """Individual sales record."""
    record_id: str
    date: date
    platform: Platform
    book_id: str
    book_title: str
    quantity: int
    unit_price: Decimal
    royalty_rate: Decimal
    currency: str = "USD"
    sale_type: SaleType = SaleType.SALE
    territory: str = "US"
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def gross_revenue(self) -> Decimal:
        """Calculate gross revenue."""
        return self.unit_price * self.quantity

    @property
    def net_revenue(self) -> Decimal:
        """Calculate net revenue after platform fees."""
        return (self.gross_revenue * self.royalty_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "record_id": self.record_id,
            "date": self.date.isoformat(),
            "platform": self.platform.value,
            "book_id": self.book_id,
            "book_title": self.book_title,
            "quantity": self.quantity,
            "unit_price": str(self.unit_price),
            "royalty_rate": str(self.royalty_rate),
            "currency": self.currency,
            "sale_type": self.sale_type.value,
            "territory": self.territory,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "gross_revenue": str(self.gross_revenue),
            "net_revenue": str(self.net_revenue),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SalesRecord":
        """Create from dictionary."""
        return cls(
            record_id=data["record_id"],
            date=date.fromisoformat(data["date"]),
            platform=Platform(data["platform"]),
            book_id=data["book_id"],
            book_title=data["book_title"],
            quantity=data["quantity"],
            unit_price=Decimal(data["unit_price"]),
            royalty_rate=Decimal(data["royalty_rate"]),
            currency=data.get("currency", "USD"),
            sale_type=SaleType(data.get("sale_type", "sale")),
            territory=data.get("territory", "US"),
            notes=data.get("notes", ""),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
        )


@dataclass
class BookSummary:
    """Summary statistics for a single book."""
    book_id: str
    book_title: str
    total_units: int
    total_gross: Decimal
    total_net: Decimal
    units_by_platform: Dict[str, int]
    revenue_by_platform: Dict[str, Decimal]
    first_sale: Optional[date]
    last_sale: Optional[date]
    avg_unit_price: Decimal
    avg_royalty_rate: Decimal


@dataclass
class RevenueReport:
    """Revenue report for a time period."""
    start_date: date
    end_date: date
    total_units: int
    total_gross_revenue: Decimal
    total_net_revenue: Decimal
    units_by_platform: Dict[str, int]
    revenue_by_platform: Dict[str, Decimal]
    units_by_book: Dict[str, int]
    revenue_by_book: Dict[str, Decimal]
    units_by_territory: Dict[str, int]
    daily_breakdown: Dict[str, Dict[str, Any]]
    book_summaries: List[BookSummary]
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_units": self.total_units,
            "total_gross_revenue": str(self.total_gross_revenue),
            "total_net_revenue": str(self.total_net_revenue),
            "units_by_platform": self.units_by_platform,
            "revenue_by_platform": {k: str(v) for k, v in self.revenue_by_platform.items()},
            "units_by_book": self.units_by_book,
            "revenue_by_book": {k: str(v) for k, v in self.revenue_by_book.items()},
            "units_by_territory": self.units_by_territory,
            "daily_breakdown": self.daily_breakdown,
            "generated_at": self.generated_at.isoformat(),
        }


class RevenueTracker:
    """
    Revenue tracking and analytics system.

    Features:
    - Track sales across multiple platforms
    - Import from CSV reports
    - Generate revenue reports
    - Export data for analysis
    - Goal tracking and projections
    """

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        """
        Initialize revenue tracker.

        Args:
            data_dir: Directory for storing data files
        """
        self.data_dir = data_dir or Path.cwd() / "revenue_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.records_file = self.data_dir / "sales_records.json"
        self.books_file = self.data_dir / "books_catalog.json"
        self.goals_file = self.data_dir / "revenue_goals.json"

        self.records: List[SalesRecord] = []
        self.books_catalog: Dict[str, Dict[str, Any]] = {}
        self.revenue_goals: Dict[str, Dict[str, Any]] = {}

        self._load_data()

    def _load_data(self) -> None:
        """Load existing data from files."""
        # Load sales records
        if self.records_file.exists():
            try:
                with open(self.records_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.records = [SalesRecord.from_dict(r) for r in data]
                logger.info(f"Loaded {len(self.records)} sales records")
            except Exception as e:
                logger.error(f"Error loading records: {e}")
                self.records = []

        # Load books catalog
        if self.books_file.exists():
            try:
                with open(self.books_file, "r", encoding="utf-8") as f:
                    self.books_catalog = json.load(f)
            except Exception as e:
                logger.error(f"Error loading books catalog: {e}")
                self.books_catalog = {}

        # Load goals
        if self.goals_file.exists():
            try:
                with open(self.goals_file, "r", encoding="utf-8") as f:
                    self.revenue_goals = json.load(f)
            except Exception as e:
                logger.error(f"Error loading goals: {e}")
                self.revenue_goals = {}

    def _save_data(self) -> None:
        """Save data to files."""
        # Save sales records
        with open(self.records_file, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self.records], f, indent=2)

        # Save books catalog
        with open(self.books_file, "w", encoding="utf-8") as f:
            json.dump(self.books_catalog, f, indent=2)

        # Save goals
        with open(self.goals_file, "w", encoding="utf-8") as f:
            json.dump(self.revenue_goals, f, indent=2)

    def _generate_record_id(self) -> str:
        """Generate unique record ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        count = len(self.records)
        return f"sale_{timestamp}_{count}"

    def register_book(
        self,
        book_id: str,
        title: str,
        author: str,
        production_cost: Decimal = Decimal("0"),
        publish_date: Optional[date] = None,
        platforms: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Register a book in the catalog.

        Args:
            book_id: Unique book identifier
            title: Book title
            author: Author name
            production_cost: Cost to produce
            publish_date: Publication date
            platforms: List of distribution platforms
            metadata: Additional metadata
        """
        self.books_catalog[book_id] = {
            "book_id": book_id,
            "title": title,
            "author": author,
            "production_cost": str(production_cost),
            "publish_date": publish_date.isoformat() if publish_date else None,
            "platforms": platforms or [],
            "metadata": metadata or {},
            "registered_at": datetime.now().isoformat(),
        }
        self._save_data()
        logger.info(f"Registered book: {title} ({book_id})")

    def add_sale(
        self,
        sale_date: date,
        platform: Platform,
        book_id: str,
        quantity: int,
        unit_price: Decimal,
        royalty_rate: Decimal,
        currency: str = "USD",
        sale_type: SaleType = SaleType.SALE,
        territory: str = "US",
        notes: str = "",
    ) -> SalesRecord:
        """
        Add a sales record.

        Args:
            sale_date: Date of sale
            platform: Distribution platform
            book_id: Book identifier
            quantity: Number of units
            unit_price: Price per unit
            royalty_rate: Royalty rate (0.0-1.0)
            currency: Currency code
            sale_type: Type of sale
            territory: Territory code
            notes: Optional notes

        Returns:
            Created SalesRecord
        """
        # Get book title from catalog or use book_id
        book_title = self.books_catalog.get(book_id, {}).get("title", book_id)

        record = SalesRecord(
            record_id=self._generate_record_id(),
            date=sale_date,
            platform=platform,
            book_id=book_id,
            book_title=book_title,
            quantity=quantity,
            unit_price=unit_price,
            royalty_rate=royalty_rate,
            currency=currency,
            sale_type=sale_type,
            territory=territory,
            notes=notes,
        )

        self.records.append(record)
        self._save_data()

        logger.info(
            f"Added sale: {book_title} x{quantity} @ ${unit_price} "
            f"({platform.value}) = ${record.net_revenue} net"
        )

        return record

    def import_findaway_csv(self, csv_path: Path) -> int:
        """
        Import sales from Findaway Voices CSV export.

        Args:
            csv_path: Path to CSV file

        Returns:
            Number of records imported
        """
        imported = 0

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Map Findaway CSV columns
                    sale_date = datetime.strptime(row["Date"], "%Y-%m-%d").date()
                    book_id = row.get("ISBN", row.get("Title", "unknown"))

                    self.add_sale(
                        sale_date=sale_date,
                        platform=Platform.FINDAWAY_VOICES,
                        book_id=book_id,
                        quantity=int(row.get("Quantity", 1)),
                        unit_price=Decimal(row.get("Sale Price", "0")),
                        royalty_rate=Decimal("0.70"),  # Findaway standard
                        territory=row.get("Territory", "US"),
                    )
                    imported += 1
                except Exception as e:
                    logger.warning(f"Error importing row: {e}")

        logger.info(f"Imported {imported} records from Findaway CSV")
        return imported

    def import_google_play_csv(self, csv_path: Path) -> int:
        """
        Import sales from Google Play Books CSV export.

        Args:
            csv_path: Path to CSV file

        Returns:
            Number of records imported
        """
        imported = 0

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    sale_date = datetime.strptime(
                        row["Transaction Date"], "%Y-%m-%d"
                    ).date()

                    self.add_sale(
                        sale_date=sale_date,
                        platform=Platform.GOOGLE_PLAY,
                        book_id=row.get("ISBN", row.get("Title", "unknown")),
                        quantity=int(row.get("Quantity Sold", 1)),
                        unit_price=Decimal(row.get("List Price", "0")),
                        royalty_rate=Decimal(row.get("Revenue Share", "0.70")),
                        currency=row.get("Currency", "USD"),
                        territory=row.get("Country", "US"),
                    )
                    imported += 1
                except Exception as e:
                    logger.warning(f"Error importing row: {e}")

        logger.info(f"Imported {imported} records from Google Play CSV")
        return imported

    def import_gumroad_csv(self, csv_path: Path) -> int:
        """
        Import sales from Gumroad CSV export.

        Args:
            csv_path: Path to CSV file

        Returns:
            Number of records imported
        """
        imported = 0

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    sale_date = datetime.strptime(
                        row["Created At"], "%Y-%m-%d"
                    ).date()

                    # Handle refunds
                    sale_type = SaleType.REFUND if row.get("Refunded") == "true" else SaleType.SALE
                    quantity = -1 if sale_type == SaleType.REFUND else 1

                    self.add_sale(
                        sale_date=sale_date,
                        platform=Platform.DIRECT_GUMROAD,
                        book_id=row.get("Product", "unknown"),
                        quantity=quantity,
                        unit_price=Decimal(row.get("Price", "0")),
                        royalty_rate=Decimal("0.95"),  # Gumroad takes ~5%
                        sale_type=sale_type,
                    )
                    imported += 1
                except Exception as e:
                    logger.warning(f"Error importing row: {e}")

        logger.info(f"Imported {imported} records from Gumroad CSV")
        return imported

    def get_records(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        platform: Optional[Platform] = None,
        book_id: Optional[str] = None,
    ) -> List[SalesRecord]:
        """
        Get filtered sales records.

        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            platform: Filter by platform
            book_id: Filter by book

        Returns:
            List of matching records
        """
        filtered = self.records

        if start_date:
            filtered = [r for r in filtered if r.date >= start_date]
        if end_date:
            filtered = [r for r in filtered if r.date <= end_date]
        if platform:
            filtered = [r for r in filtered if r.platform == platform]
        if book_id:
            filtered = [r for r in filtered if r.book_id == book_id]

        return filtered

    def generate_report(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        time_frame: TimeFrame = TimeFrame.MONTHLY,
    ) -> RevenueReport:
        """
        Generate revenue report.

        Args:
            start_date: Report start date
            end_date: Report end date
            time_frame: Grouping time frame

        Returns:
            RevenueReport with analytics
        """
        # Default to current month
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date.replace(day=1)

        records = self.get_records(start_date, end_date)

        # Aggregate data
        total_units = 0
        total_gross = Decimal("0")
        total_net = Decimal("0")
        units_by_platform: Dict[str, int] = defaultdict(int)
        revenue_by_platform: Dict[str, Decimal] = defaultdict(Decimal)
        units_by_book: Dict[str, int] = defaultdict(int)
        revenue_by_book: Dict[str, Decimal] = defaultdict(Decimal)
        units_by_territory: Dict[str, int] = defaultdict(int)
        daily_data: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"units": 0, "gross": Decimal("0"), "net": Decimal("0")}
        )
        book_records: Dict[str, List[SalesRecord]] = defaultdict(list)

        for record in records:
            total_units += record.quantity
            total_gross += record.gross_revenue
            total_net += record.net_revenue

            units_by_platform[record.platform.value] += record.quantity
            revenue_by_platform[record.platform.value] += record.net_revenue

            units_by_book[record.book_id] += record.quantity
            revenue_by_book[record.book_id] += record.net_revenue

            units_by_territory[record.territory] += record.quantity

            day_key = record.date.isoformat()
            daily_data[day_key]["units"] += record.quantity
            daily_data[day_key]["gross"] += record.gross_revenue
            daily_data[day_key]["net"] += record.net_revenue

            book_records[record.book_id].append(record)

        # Generate book summaries
        book_summaries = []
        for book_id, book_recs in book_records.items():
            if not book_recs:
                continue

            book_units = sum(r.quantity for r in book_recs)
            book_gross = sum(r.gross_revenue for r in book_recs)
            book_net = sum(r.net_revenue for r in book_recs)

            summary = BookSummary(
                book_id=book_id,
                book_title=book_recs[0].book_title,
                total_units=book_units,
                total_gross=book_gross,
                total_net=book_net,
                units_by_platform={
                    p.value: sum(r.quantity for r in book_recs if r.platform == p)
                    for p in Platform
                    if any(r.platform == p for r in book_recs)
                },
                revenue_by_platform={
                    p.value: sum(r.net_revenue for r in book_recs if r.platform == p)
                    for p in Platform
                    if any(r.platform == p for r in book_recs)
                },
                first_sale=min(r.date for r in book_recs),
                last_sale=max(r.date for r in book_recs),
                avg_unit_price=book_gross / book_units if book_units > 0 else Decimal("0"),
                avg_royalty_rate=book_net / book_gross if book_gross > 0 else Decimal("0"),
            )
            book_summaries.append(summary)

        # Convert daily data for JSON
        daily_breakdown = {
            k: {
                "units": v["units"],
                "gross": str(v["gross"]),
                "net": str(v["net"]),
            }
            for k, v in daily_data.items()
        }

        return RevenueReport(
            start_date=start_date,
            end_date=end_date,
            total_units=total_units,
            total_gross_revenue=total_gross,
            total_net_revenue=total_net,
            units_by_platform=dict(units_by_platform),
            revenue_by_platform=dict(revenue_by_platform),
            units_by_book=dict(units_by_book),
            revenue_by_book=dict(revenue_by_book),
            units_by_territory=dict(units_by_territory),
            daily_breakdown=daily_breakdown,
            book_summaries=book_summaries,
        )

    def set_goal(
        self,
        goal_id: str,
        goal_type: str,  # "monthly", "yearly", "per_title"
        target_amount: Decimal,
        target_date: Optional[date] = None,
        notes: str = "",
    ) -> None:
        """
        Set a revenue goal.

        Args:
            goal_id: Unique goal identifier
            goal_type: Type of goal
            target_amount: Target revenue amount
            target_date: Target date
            notes: Optional notes
        """
        self.revenue_goals[goal_id] = {
            "goal_id": goal_id,
            "goal_type": goal_type,
            "target_amount": str(target_amount),
            "target_date": target_date.isoformat() if target_date else None,
            "notes": notes,
            "created_at": datetime.now().isoformat(),
        }
        self._save_data()

    def check_goal_progress(self, goal_id: str) -> Dict[str, Any]:
        """
        Check progress toward a goal.

        Args:
            goal_id: Goal identifier

        Returns:
            Progress information
        """
        goal = self.revenue_goals.get(goal_id)
        if not goal:
            return {"error": "Goal not found"}

        target = Decimal(goal["target_amount"])

        # Determine date range based on goal type
        if goal["goal_type"] == "monthly":
            start = date.today().replace(day=1)
            end = date.today()
        elif goal["goal_type"] == "yearly":
            start = date.today().replace(month=1, day=1)
            end = date.today()
        else:
            start = None
            end = date.today()

        report = self.generate_report(start, end)
        current = report.total_net_revenue

        progress_pct = (current / target * 100) if target > 0 else Decimal("0")

        return {
            "goal_id": goal_id,
            "goal_type": goal["goal_type"],
            "target": str(target),
            "current": str(current),
            "remaining": str(max(Decimal("0"), target - current)),
            "progress_percent": float(progress_pct.quantize(Decimal("0.1"))),
            "on_track": progress_pct >= self._expected_progress_percent(goal),
        }

    def _expected_progress_percent(self, goal: Dict[str, Any]) -> Decimal:
        """Calculate expected progress percentage based on date."""
        today = date.today()

        if goal["goal_type"] == "monthly":
            days_in_month = 30  # Simplified
            return Decimal(today.day) / days_in_month * 100
        elif goal["goal_type"] == "yearly":
            day_of_year = today.timetuple().tm_yday
            return Decimal(day_of_year) / 365 * 100
        else:
            return Decimal("50")  # Default to 50% for custom goals

    def export_report_csv(self, report: RevenueReport, output_path: Path) -> None:
        """
        Export report to CSV.

        Args:
            report: Report to export
            output_path: Output file path
        """
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Summary
            writer.writerow(["Revenue Report"])
            writer.writerow(["Period", f"{report.start_date} to {report.end_date}"])
            writer.writerow([])
            writer.writerow(["Summary"])
            writer.writerow(["Total Units", report.total_units])
            writer.writerow(["Gross Revenue", f"${report.total_gross_revenue}"])
            writer.writerow(["Net Revenue", f"${report.total_net_revenue}"])
            writer.writerow([])

            # By platform
            writer.writerow(["Revenue by Platform"])
            writer.writerow(["Platform", "Units", "Revenue"])
            for platform, units in report.units_by_platform.items():
                revenue = report.revenue_by_platform.get(platform, Decimal("0"))
                writer.writerow([platform, units, f"${revenue}"])
            writer.writerow([])

            # By book
            writer.writerow(["Revenue by Book"])
            writer.writerow(["Book", "Units", "Revenue"])
            for book_id, units in report.units_by_book.items():
                revenue = report.revenue_by_book.get(book_id, Decimal("0"))
                writer.writerow([book_id, units, f"${revenue}"])

        logger.info(f"Exported report to {output_path}")

    def get_projection(
        self,
        months_ahead: int = 12,
        growth_rate: Decimal = Decimal("0.10"),
    ) -> Dict[str, Any]:
        """
        Generate revenue projection.

        Args:
            months_ahead: Number of months to project
            growth_rate: Assumed monthly growth rate

        Returns:
            Projection data
        """
        # Get recent monthly average
        today = date.today()
        three_months_ago = today - timedelta(days=90)

        report = self.generate_report(three_months_ago, today)

        if report.total_net_revenue > 0:
            monthly_avg = report.total_net_revenue / 3
        else:
            monthly_avg = Decimal("0")

        projections = []
        current_revenue = monthly_avg

        for i in range(months_ahead):
            month_date = today + timedelta(days=30 * (i + 1))
            current_revenue = current_revenue * (1 + growth_rate)
            projections.append({
                "month": month_date.strftime("%Y-%m"),
                "projected_revenue": str(current_revenue.quantize(Decimal("0.01"))),
            })

        total_projected = sum(
            Decimal(p["projected_revenue"]) for p in projections
        )

        return {
            "base_monthly_average": str(monthly_avg),
            "growth_rate": str(growth_rate),
            "months_ahead": months_ahead,
            "projections": projections,
            "total_projected": str(total_projected),
            "generated_at": datetime.now().isoformat(),
        }

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get high-level summary statistics.

        Returns:
            Summary statistics
        """
        if not self.records:
            return {
                "total_records": 0,
                "total_books": len(self.books_catalog),
                "lifetime_revenue": "0.00",
                "message": "No sales recorded yet",
            }

        all_time_report = self.generate_report(
            min(r.date for r in self.records),
            date.today()
        )

        # This month
        month_start = date.today().replace(day=1)
        this_month = self.generate_report(month_start, date.today())

        return {
            "total_records": len(self.records),
            "total_books": len(self.books_catalog),
            "lifetime_units": all_time_report.total_units,
            "lifetime_gross": str(all_time_report.total_gross_revenue),
            "lifetime_net": str(all_time_report.total_net_revenue),
            "this_month_units": this_month.total_units,
            "this_month_net": str(this_month.total_net_revenue),
            "top_platform": max(
                all_time_report.revenue_by_platform.items(),
                key=lambda x: x[1],
                default=("none", Decimal("0"))
            )[0] if all_time_report.revenue_by_platform else "none",
            "top_book": max(
                all_time_report.revenue_by_book.items(),
                key=lambda x: x[1],
                default=("none", Decimal("0"))
            )[0] if all_time_report.revenue_by_book else "none",
        }


def main() -> None:
    """Example usage of RevenueTracker."""
    tracker = RevenueTracker()

    # Register books
    tracker.register_book(
        book_id="maltese_falcon_2026",
        title="The Maltese Falcon",
        author="Dashiell Hammett",
        production_cost=Decimal("50"),
        publish_date=date(2026, 1, 15),
        platforms=["findaway_voices", "google_play", "direct_gumroad"],
    )

    tracker.register_book(
        book_id="strong_poison_2026",
        title="Strong Poison",
        author="Dorothy L. Sayers",
        production_cost=Decimal("55"),
        publish_date=date(2026, 1, 22),
    )

    # Add sample sales
    tracker.add_sale(
        sale_date=date(2026, 1, 20),
        platform=Platform.FINDAWAY_VOICES,
        book_id="maltese_falcon_2026",
        quantity=5,
        unit_price=Decimal("9.99"),
        royalty_rate=Decimal("0.70"),
    )

    tracker.add_sale(
        sale_date=date(2026, 1, 21),
        platform=Platform.GOOGLE_PLAY,
        book_id="maltese_falcon_2026",
        quantity=8,
        unit_price=Decimal("7.99"),
        royalty_rate=Decimal("0.70"),
    )

    # Set goal
    tracker.set_goal(
        goal_id="jan_2026",
        goal_type="monthly",
        target_amount=Decimal("500"),
        notes="First month target",
    )

    # Generate report
    report = tracker.generate_report()
    print(f"\n=== Revenue Report ===")
    print(f"Period: {report.start_date} to {report.end_date}")
    print(f"Total Units: {report.total_units}")
    print(f"Gross Revenue: ${report.total_gross_revenue}")
    print(f"Net Revenue: ${report.total_net_revenue}")

    # Check goal
    progress = tracker.check_goal_progress("jan_2026")
    print(f"\n=== Goal Progress ===")
    print(f"Target: ${progress['target']}")
    print(f"Current: ${progress['current']}")
    print(f"Progress: {progress['progress_percent']}%")

    # Summary stats
    stats = tracker.get_summary_stats()
    print(f"\n=== Summary ===")
    print(f"Lifetime Net Revenue: ${stats['lifetime_net']}")
    print(f"This Month: ${stats['this_month_net']}")


if __name__ == "__main__":
    main()
