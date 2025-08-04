#!/usr/bin/env python3
"""Fetch all events from AutoPi API and analyze event types."""

import asyncio
import json
import logging
from typing import Any

import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://api.autopi.io"
API_KEY = "APIToken 8a19b2be2e24035904c9ecf28d21f7d67c2895ec"
DEVICE_ID = "2024b19b-affe-4f6a-98e0-e2b6700c981c"
PAGE_SIZE = 200


async def fetch_events_page(session: aiohttp.ClientSession, page_num: int) -> dict[str, Any]:
    """Fetch a single page of events."""
    url = f"{BASE_URL}/logbook/events/"
    params = {
        "device_id": DEVICE_ID,
        "page_num": page_num,
        "page_hits": PAGE_SIZE,
    }
    headers = {
        "Authorization": API_KEY,
        "Accept": "application/json",
    }

    logger.info(f"Fetching page {page_num}...")

    async with session.get(url, params=params, headers=headers) as response:
        if response.status != 200:
            raise Exception(f"API error: {response.status}")
        return await response.json()


async def fetch_all_events() -> list[dict[str, Any]]:
    """Fetch all events from the API."""
    all_events = []
    page_num = 1

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                data = await fetch_events_page(session, page_num)
                results = data.get("results", [])

                if not results:
                    logger.info(f"No more events found. Total pages: {page_num - 1}")
                    break

                all_events.extend(results)
                logger.info(f"Page {page_num}: Found {len(results)} events. Total so far: {len(all_events)}")

                # Check if we've reached the end
                total_count = data.get("count", 0)
                if len(all_events) >= total_count:
                    logger.info(f"Fetched all {total_count} events")
                    break

                page_num += 1

                # Small delay to be nice to the API
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.exception(f"Error fetching page {page_num}: {e}")
                break

    return all_events


def analyze_event_types(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze the event types and areas."""
    event_types: set[str] = set()
    areas: set[str] = set()
    tags: set[str] = set()
    event_type_counts: dict[str, int] = {}
    area_counts: dict[str, int] = {}

    for event in events:
        event_type = event.get("event", "unknown")
        area = event.get("area", "unknown")
        tag = event.get("tag", "unknown")

        event_types.add(event_type)
        areas.add(area)
        tags.add(tag)

        event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        area_counts[area] = area_counts.get(area, 0) + 1

    return {
        "unique_event_types": sorted(event_types),
        "unique_areas": sorted(areas),
        "unique_tags": sorted(tags),
        "event_type_counts": dict(sorted(event_type_counts.items(), key=lambda x: x[1], reverse=True)),
        "area_counts": dict(sorted(area_counts.items(), key=lambda x: x[1], reverse=True)),
        "total_events": len(events),
    }


async def main():
    """Main function."""
    # Fetch all events
    logger.info("Starting to fetch all events...")
    events = await fetch_all_events()

    # Save raw events
    with open("autopi_events_raw.json", "w") as f:
        json.dump(events, f, indent=2)
    logger.info(f"Saved {len(events)} events to autopi_events_raw.json")

    # Analyze event types
    analysis = analyze_event_types(events)

    # Save analysis
    with open("autopi_events_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)
    logger.info("Saved analysis to autopi_events_analysis.json")

    # Print summary
    print("\n=== Event Type Analysis ===")
    print(f"Total events: {analysis['total_events']}")
    print(f"Unique event types: {len(analysis['unique_event_types'])}")
    print(f"Unique areas: {len(analysis['unique_areas'])}")

    print("\n=== Event Types (sorted by frequency) ===")
    for event_type, count in analysis["event_type_counts"].items():
        print(f"  {event_type}: {count}")

    print("\n=== Areas (sorted by frequency) ===")
    for area, count in analysis["area_counts"].items():
        print(f"  {area}: {count}")

    print("\n=== All Unique Event Types ===")
    for event_type in analysis["unique_event_types"]:
        print(f"  - {event_type}")


if __name__ == "__main__":
    asyncio.run(main())
