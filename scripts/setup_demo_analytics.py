#!/usr/bin/env python3
"""
Set up demo analytics data for testing the revenue tracking system.
Run this to populate the dashboard with sample data.
"""

import sys
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal
import random

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analytics.revenue_tracker import RevenueTracker, Platform, SaleType


def setup_demo_data():
    """Create demo analytics data."""

    # Initialize tracker
    data_dir = Path(__file__).parent.parent / "revenue_data"
    tracker = RevenueTracker(data_dir)

    print("Setting up demo analytics data...")
    print(f"Data directory: {data_dir}")

    # Register books
    books = [
        {
            "book_id": "maltese_falcon_2026",
            "title": "The Maltese Falcon",
            "author": "Dashiell Hammett",
            "production_cost": Decimal("45"),
            "publish_date": date(2026, 1, 15),
            "platforms": ["findaway_voices", "google_play", "direct_gumroad"],
        },
        {
            "book_id": "strong_poison_2026",
            "title": "Strong Poison",
            "author": "Dorothy L. Sayers",
            "production_cost": Decimal("50"),
            "publish_date": date(2026, 1, 22),
            "platforms": ["findaway_voices", "google_play", "direct_gumroad"],
        },
        {
            "book_id": "last_first_men_2026",
            "title": "Last and First Men",
            "author": "Olaf Stapledon",
            "production_cost": Decimal("55"),
            "publish_date": date(2026, 2, 1),
            "platforms": ["findaway_voices", "google_play", "direct_gumroad"],
        },
    ]

    for book in books:
        tracker.register_book(**book)
        print(f"  Registered: {book['title']}")

    # Platform configurations
    platform_config = {
        Platform.FINDAWAY_VOICES: {
            "prices": {"maltese_falcon_2026": Decimal("9.99"), "strong_poison_2026": Decimal("12.99"), "last_first_men_2026": Decimal("14.99")},
            "royalty": Decimal("0.70"),
            "weight": 0.35,  # 35% of sales
        },
        Platform.GOOGLE_PLAY: {
            "prices": {"maltese_falcon_2026": Decimal("7.99"), "strong_poison_2026": Decimal("9.99"), "last_first_men_2026": Decimal("11.99")},
            "royalty": Decimal("0.70"),
            "weight": 0.45,  # 45% of sales
        },
        Platform.DIRECT_GUMROAD: {
            "prices": {"maltese_falcon_2026": Decimal("4.99"), "strong_poison_2026": Decimal("6.99"), "last_first_men_2026": Decimal("8.99")},
            "royalty": Decimal("0.95"),
            "weight": 0.20,  # 20% of sales
        },
    }

    # Generate sample sales for demo (simulating first month)
    # This is DEMO DATA - represents what sales might look like

    territories = ["US", "US", "US", "US", "GB", "CA", "AU", "DE"]  # Weighted toward US

    start_date = date(2026, 1, 15)
    end_date = date(2026, 1, 27)  # Today

    print("\n  Generating sample sales...")

    total_sales = 0
    current_date = start_date

    while current_date <= end_date:
        # More sales as time goes on (word of mouth)
        days_live = (current_date - start_date).days
        base_daily_sales = 2 + (days_live // 3)  # Gradual increase

        # Random variance
        daily_sales = max(0, base_daily_sales + random.randint(-1, 2))

        for _ in range(daily_sales):
            # Pick platform based on weights
            r = random.random()
            if r < 0.35:
                platform = Platform.FINDAWAY_VOICES
            elif r < 0.80:
                platform = Platform.GOOGLE_PLAY
            else:
                platform = Platform.DIRECT_GUMROAD

            # Pick book (Maltese Falcon most popular initially)
            book_weights = [0.5, 0.3, 0.2]  # MF, SP, LFM
            book_r = random.random()
            if book_r < 0.5:
                book_id = "maltese_falcon_2026"
            elif book_r < 0.8:
                book_id = "strong_poison_2026"
            else:
                book_id = "last_first_men_2026"

            config = platform_config[platform]

            tracker.add_sale(
                sale_date=current_date,
                platform=platform,
                book_id=book_id,
                quantity=1,
                unit_price=config["prices"][book_id],
                royalty_rate=config["royalty"],
                territory=random.choice(territories),
            )
            total_sales += 1

        current_date += timedelta(days=1)

    print(f"  Generated {total_sales} sample sales")

    # Set up goals
    tracker.set_goal(
        goal_id="jan_2026",
        goal_type="monthly",
        target_amount=Decimal("500"),
        notes="First month target - conservative",
    )

    tracker.set_goal(
        goal_id="q1_2026",
        goal_type="quarterly",
        target_amount=Decimal("2000"),
        notes="Q1 2026 target",
    )

    print("  Set revenue goals")

    # Print summary
    print("\n" + "=" * 50)
    stats = tracker.get_summary_stats()
    print(f"  Total Sales Records: {stats['total_records']}")
    print(f"  Total Books: {stats['total_books']}")
    print(f"  Lifetime Net Revenue: ${stats['lifetime_net']}")
    print(f"  This Month Net: ${stats['this_month_net']}")
    print(f"  Top Platform: {stats['top_platform']}")
    print(f"  Top Book: {stats['top_book']}")
    print("=" * 50)

    # Check goal progress
    progress = tracker.check_goal_progress("jan_2026")
    print(f"\n  January Goal Progress: {progress['progress_percent']}%")
    print(f"  ${progress['current']} / ${progress['target']}")

    print("\n✓ Demo data setup complete!")
    print(f"\nTo view dashboard, run:")
    print(f"  python -c \"from src.analytics.analytics_dashboard import *; from src.analytics.revenue_tracker import *; d=AnalyticsDashboard(RevenueTracker()); d.print_summary()\"")

    return tracker


if __name__ == "__main__":
    setup_demo_data()
