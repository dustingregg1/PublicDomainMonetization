"""
Analytics Dashboard

Generates visual reports and dashboards for revenue tracking.
Supports CLI output, HTML export, and markdown reports.
"""

import os
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional, List, Dict, Any

from .revenue_tracker import (
    RevenueTracker,
    RevenueReport,
    Platform,
    TimeFrame,
)

logger = logging.getLogger(__name__)


@dataclass
class DashboardConfig:
    """Configuration for dashboard generation."""
    output_dir: Path = field(default_factory=lambda: Path("./dashboards"))
    include_projections: bool = True
    projection_months: int = 12
    growth_rate: Decimal = Decimal("0.10")
    currency_symbol: str = "$"
    show_goals: bool = True


class AnalyticsDashboard:
    """
    Generate analytics dashboards and reports.

    Features:
    - CLI summary display
    - Markdown report generation
    - HTML dashboard export
    - Goal tracking visualization
    """

    def __init__(
        self,
        tracker: RevenueTracker,
        config: Optional[DashboardConfig] = None,
    ) -> None:
        """
        Initialize dashboard generator.

        Args:
            tracker: RevenueTracker instance
            config: Dashboard configuration
        """
        self.tracker = tracker
        self.config = config or DashboardConfig()
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def print_summary(self) -> None:
        """Print quick summary to CLI."""
        stats = self.tracker.get_summary_stats()
        cs = self.config.currency_symbol

        print("\n" + "=" * 60)
        print("  PUBLIC DOMAIN MONETIZATION - REVENUE DASHBOARD")
        print("=" * 60)

        if stats["total_records"] == 0:
            print("\n  No sales data yet. Start by adding sales records.")
            print("=" * 60 + "\n")
            return

        print(f"\n  LIFETIME STATS")
        print(f"  ├─ Total Sales: {stats['lifetime_units']} units")
        print(f"  ├─ Gross Revenue: {cs}{stats['lifetime_gross']}")
        print(f"  └─ Net Revenue: {cs}{stats['lifetime_net']}")

        print(f"\n  THIS MONTH")
        print(f"  ├─ Units Sold: {stats['this_month_units']}")
        print(f"  └─ Net Revenue: {cs}{stats['this_month_net']}")

        print(f"\n  TOP PERFORMERS")
        print(f"  ├─ Platform: {stats['top_platform']}")
        print(f"  └─ Book: {stats['top_book']}")

        # Show goals if configured
        if self.config.show_goals and self.tracker.revenue_goals:
            print(f"\n  GOALS")
            for goal_id in self.tracker.revenue_goals:
                progress = self.tracker.check_goal_progress(goal_id)
                status = "ON TRACK" if progress.get("on_track") else "BEHIND"
                print(f"  ├─ {goal_id}: {progress['progress_percent']}% ({status})")
                print(f"  │  └─ {cs}{progress['current']} / {cs}{progress['target']}")

        print("\n" + "=" * 60 + "\n")

    def print_monthly_report(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> None:
        """
        Print detailed monthly report to CLI.

        Args:
            year: Report year (default: current)
            month: Report month (default: current)
        """
        today = date.today()
        year = year or today.year
        month = month or today.month

        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        report = self.tracker.generate_report(start_date, min(end_date, today))
        cs = self.config.currency_symbol

        print("\n" + "=" * 60)
        print(f"  MONTHLY REPORT - {start_date.strftime('%B %Y')}")
        print("=" * 60)

        print(f"\n  SUMMARY")
        print(f"  ├─ Period: {report.start_date} to {report.end_date}")
        print(f"  ├─ Total Units: {report.total_units}")
        print(f"  ├─ Gross Revenue: {cs}{report.total_gross_revenue}")
        print(f"  └─ Net Revenue: {cs}{report.total_net_revenue}")

        if report.revenue_by_platform:
            print(f"\n  BY PLATFORM")
            for platform, revenue in sorted(
                report.revenue_by_platform.items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                units = report.units_by_platform.get(platform, 0)
                print(f"  ├─ {platform}: {units} units = {cs}{revenue}")

        if report.revenue_by_book:
            print(f"\n  BY BOOK")
            for book_id, revenue in sorted(
                report.revenue_by_book.items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                units = report.units_by_book.get(book_id, 0)
                print(f"  ├─ {book_id}: {units} units = {cs}{revenue}")

        if report.units_by_territory:
            print(f"\n  BY TERRITORY")
            for territory, units in sorted(
                report.units_by_territory.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5]:  # Top 5 territories
                print(f"  ├─ {territory}: {units} units")

        print("\n" + "=" * 60 + "\n")

    def generate_markdown_report(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        output_name: Optional[str] = None,
    ) -> Path:
        """
        Generate markdown report file.

        Args:
            start_date: Report start date
            end_date: Report end date
            output_name: Output filename (without extension)

        Returns:
            Path to generated report
        """
        today = date.today()
        end_date = end_date or today
        start_date = start_date or today.replace(day=1)

        report = self.tracker.generate_report(start_date, end_date)
        stats = self.tracker.get_summary_stats()
        cs = self.config.currency_symbol

        output_name = output_name or f"revenue_report_{today.isoformat()}"
        output_path = self.config.output_dir / f"{output_name}.md"

        lines = [
            f"# Revenue Report",
            f"",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**Period:** {report.start_date} to {report.end_date}",
            f"",
            f"---",
            f"",
            f"## Executive Summary",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Units Sold | {report.total_units} |",
            f"| Gross Revenue | {cs}{report.total_gross_revenue} |",
            f"| Net Revenue | {cs}{report.total_net_revenue} |",
            f"| Books in Catalog | {stats['total_books']} |",
            f"",
            f"---",
            f"",
            f"## Revenue by Platform",
            f"",
            f"| Platform | Units | Revenue | % of Total |",
            f"|----------|-------|---------|------------|",
        ]

        total_rev = report.total_net_revenue or Decimal("1")
        for platform, revenue in sorted(
            report.revenue_by_platform.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            units = report.units_by_platform.get(platform, 0)
            pct = (revenue / total_rev * 100).quantize(Decimal("0.1"))
            lines.append(f"| {platform} | {units} | {cs}{revenue} | {pct}% |")

        lines.extend([
            f"",
            f"---",
            f"",
            f"## Revenue by Book",
            f"",
            f"| Book | Units | Revenue | Avg Price |",
            f"|------|-------|---------|-----------|",
        ])

        for book_id, revenue in sorted(
            report.revenue_by_book.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            units = report.units_by_book.get(book_id, 0)
            avg_price = (revenue / units).quantize(Decimal("0.01")) if units > 0 else Decimal("0")
            lines.append(f"| {book_id} | {units} | {cs}{revenue} | {cs}{avg_price} |")

        # Add goals section if applicable
        if self.config.show_goals and self.tracker.revenue_goals:
            lines.extend([
                f"",
                f"---",
                f"",
                f"## Goal Progress",
                f"",
                f"| Goal | Type | Target | Current | Progress |",
                f"|------|------|--------|---------|----------|",
            ])

            for goal_id in self.tracker.revenue_goals:
                progress = self.tracker.check_goal_progress(goal_id)
                status = "ON TRACK" if progress.get("on_track") else "BEHIND"
                lines.append(
                    f"| {goal_id} | {progress['goal_type']} | "
                    f"{cs}{progress['target']} | {cs}{progress['current']} | "
                    f"{progress['progress_percent']}% ({status}) |"
                )

        # Add projections if configured
        if self.config.include_projections:
            projection = self.tracker.get_projection(
                months_ahead=self.config.projection_months,
                growth_rate=self.config.growth_rate,
            )

            lines.extend([
                f"",
                f"---",
                f"",
                f"## Revenue Projections",
                f"",
                f"**Base Monthly Average:** {cs}{projection['base_monthly_average']}",
                f"**Assumed Growth Rate:** {float(self.config.growth_rate) * 100}% monthly",
                f"",
                f"| Month | Projected Revenue |",
                f"|-------|-------------------|",
            ])

            for p in projection["projections"][:6]:  # Next 6 months
                lines.append(f"| {p['month']} | {cs}{p['projected_revenue']} |")

            lines.append(f"")
            lines.append(f"**Total Projected ({self.config.projection_months} months):** {cs}{projection['total_projected']}")

        # Add territory breakdown
        if report.units_by_territory:
            lines.extend([
                f"",
                f"---",
                f"",
                f"## Sales by Territory",
                f"",
                f"| Territory | Units |",
                f"|-----------|-------|",
            ])

            for territory, units in sorted(
                report.units_by_territory.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10]:
                lines.append(f"| {territory} | {units} |")

        lines.extend([
            f"",
            f"---",
            f"",
            f"*Report generated by Public Domain Monetization Analytics System*",
        ])

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"Generated markdown report: {output_path}")
        return output_path

    def generate_html_dashboard(
        self,
        output_name: Optional[str] = None,
    ) -> Path:
        """
        Generate HTML dashboard.

        Args:
            output_name: Output filename (without extension)

        Returns:
            Path to generated dashboard
        """
        today = date.today()
        start_of_month = today.replace(day=1)

        report = self.tracker.generate_report(start_of_month, today)
        stats = self.tracker.get_summary_stats()
        cs = self.config.currency_symbol

        output_name = output_name or f"dashboard_{today.isoformat()}"
        output_path = self.config.output_dir / f"{output_name}.html"

        # Generate platform chart data
        platform_data = json.dumps([
            {"platform": p, "revenue": float(r)}
            for p, r in report.revenue_by_platform.items()
        ])

        # Generate book chart data
        book_data = json.dumps([
            {"book": b[:20], "revenue": float(r)}
            for b, r in list(report.revenue_by_book.items())[:10]
        ])

        # Generate daily trend data
        daily_data = json.dumps([
            {"date": d, "revenue": float(Decimal(data["net"]))}
            for d, data in sorted(report.daily_breakdown.items())
        ])

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Public Domain Monetization Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #1a1a2e;
            color: #eee;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #16213e;
        }}
        header h1 {{
            font-size: 2rem;
            color: #e94560;
            margin-bottom: 10px;
        }}
        header p {{
            color: #888;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: #16213e;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}
        .metric-card h3 {{
            color: #888;
            font-size: 0.9rem;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        .metric-card .value {{
            font-size: 2rem;
            font-weight: bold;
            color: #e94560;
        }}
        .metric-card .subvalue {{
            font-size: 0.9rem;
            color: #aaa;
            margin-top: 5px;
        }}
        .charts {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .chart-card {{
            background: #16213e;
            border-radius: 12px;
            padding: 20px;
        }}
        .chart-card h3 {{
            margin-bottom: 15px;
            color: #e94560;
        }}
        .chart-container {{
            position: relative;
            height: 300px;
        }}
        .table-card {{
            background: #16213e;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .table-card h3 {{
            margin-bottom: 15px;
            color: #e94560;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #1a1a2e;
        }}
        th {{
            color: #888;
            font-weight: 500;
            text-transform: uppercase;
            font-size: 0.8rem;
        }}
        tr:hover {{
            background: #1a1a2e;
        }}
        .positive {{
            color: #4caf50;
        }}
        .negative {{
            color: #f44336;
        }}
        footer {{
            text-align: center;
            padding-top: 20px;
            border-top: 2px solid #16213e;
            color: #666;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Revenue Dashboard</h1>
            <p>Public Domain Monetization - {today.strftime('%B %Y')}</p>
        </header>

        <section class="metrics">
            <div class="metric-card">
                <h3>This Month Revenue</h3>
                <div class="value">{cs}{report.total_net_revenue}</div>
                <div class="subvalue">{report.total_units} units sold</div>
            </div>
            <div class="metric-card">
                <h3>Lifetime Revenue</h3>
                <div class="value">{cs}{stats['lifetime_net']}</div>
                <div class="subvalue">{stats['lifetime_units']} total units</div>
            </div>
            <div class="metric-card">
                <h3>Books in Catalog</h3>
                <div class="value">{stats['total_books']}</div>
                <div class="subvalue">Active titles</div>
            </div>
            <div class="metric-card">
                <h3>Top Platform</h3>
                <div class="value">{stats['top_platform'].replace('_', ' ').title()}</div>
                <div class="subvalue">By revenue</div>
            </div>
        </section>

        <section class="charts">
            <div class="chart-card">
                <h3>Revenue by Platform</h3>
                <div class="chart-container">
                    <canvas id="platformChart"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <h3>Daily Revenue Trend</h3>
                <div class="chart-container">
                    <canvas id="trendChart"></canvas>
                </div>
            </div>
        </section>

        <section class="table-card">
            <h3>Revenue by Book</h3>
            <table>
                <thead>
                    <tr>
                        <th>Book</th>
                        <th>Units</th>
                        <th>Revenue</th>
                        <th>% of Total</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'''
                    <tr>
                        <td>{book_id}</td>
                        <td>{report.units_by_book.get(book_id, 0)}</td>
                        <td>{cs}{revenue}</td>
                        <td>{(revenue / (report.total_net_revenue or Decimal("1")) * 100).quantize(Decimal("0.1"))}%</td>
                    </tr>
                    ''' for book_id, revenue in sorted(report.revenue_by_book.items(), key=lambda x: x[1], reverse=True))}
                </tbody>
            </table>
        </section>

        <footer>
            <p>Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | Public Domain Monetization Analytics</p>
        </footer>
    </div>

    <script>
        // Platform Chart
        const platformData = {platform_data};
        new Chart(document.getElementById('platformChart'), {{
            type: 'doughnut',
            data: {{
                labels: platformData.map(d => d.platform.replace('_', ' ')),
                datasets: [{{
                    data: platformData.map(d => d.revenue),
                    backgroundColor: ['#e94560', '#0f3460', '#16213e', '#533483', '#e94560aa'],
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{ color: '#aaa' }}
                    }}
                }}
            }}
        }});

        // Daily Trend Chart
        const dailyData = {daily_data};
        new Chart(document.getElementById('trendChart'), {{
            type: 'line',
            data: {{
                labels: dailyData.map(d => d.date),
                datasets: [{{
                    label: 'Daily Revenue',
                    data: dailyData.map(d => d.revenue),
                    borderColor: '#e94560',
                    backgroundColor: 'rgba(233, 69, 96, 0.1)',
                    fill: true,
                    tension: 0.3,
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ color: '#888' }},
                        grid: {{ color: '#1a1a2e' }}
                    }},
                    y: {{
                        ticks: {{ color: '#888' }},
                        grid: {{ color: '#1a1a2e' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"Generated HTML dashboard: {output_path}")
        return output_path

    def export_all(self) -> Dict[str, Path]:
        """
        Export all dashboard formats.

        Returns:
            Dictionary of format -> path
        """
        today = date.today()
        name = f"analytics_{today.isoformat()}"

        return {
            "markdown": self.generate_markdown_report(output_name=name),
            "html": self.generate_html_dashboard(output_name=name),
        }


def main() -> None:
    """Example usage of AnalyticsDashboard."""
    from .revenue_tracker import RevenueTracker

    tracker = RevenueTracker()
    dashboard = AnalyticsDashboard(tracker)

    # Print CLI summary
    dashboard.print_summary()

    # Generate reports
    outputs = dashboard.export_all()
    print(f"Generated reports:")
    for fmt, path in outputs.items():
        print(f"  - {fmt}: {path}")


if __name__ == "__main__":
    main()
