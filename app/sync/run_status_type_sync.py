"""
Action Builder Membership Synchronization Script - Parallel Version

This module synchronizes membership status and type information between Action Builder
and unit-based organizational data. It identifies people whose membership information
has changed, generates reports, and cleans up outdated tags.

Workflow:
1. Query for recently modified people from Action Builder
2. Process people in parallel batches to retrieve unit connections and current tags
3. Compare unit membership data with person's current tags
4. Collect people with mismatched membership information
5. Generate CSV report excluding inactive members and sensitive fields
6. Delete outdated membership tags in parallel to prevent data inconsistencies
7. Email the report to configured recipients

"""

import csv
import io
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from time import sleep
from typing import Dict, List, Optional, Tuple

from app.api.delete_taggings import delete_tagging
from app.api.fetch_people import (
    fetch_connections_from_person,
    fetch_taggings_from_connection,
    fetch_unit_from_connection,
    get_person,
)
from app.api.list_people import search_people_modified_by
from app.api.list_tags import get_all_tags
from app.services.send_email import send_email
from app.services.utils import run_today

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger()


@dataclass
class PersonUnitInfo:
    """Information about a person's unit membership status and type."""

    uuid: str
    unit_name: str
    membership_status_tag_id: str
    membership_type_tag_id: str
    membership_status: str
    membership_type: str
    inactive: bool


def dict_to_csv(data: Dict[str, PersonUnitInfo]) -> tuple[str, int]:
    """
    Convert a dictionary of PersonUnitInfo objects to CSV string.

    Filters out inactive records and excludes specified fields from the output.

    Args:
        data: Dictionary mapping keys to PersonUnitInfo objects

    Returns:
        CSV string with headers, containing only active records with filtered fields.
        Also returns row count
        Returns empty string if no data provided or no active records found.

    Excluded fields:
        - membership_status_tag_id
        - membership_type_tag_id
        - membership_status
        - inactive
    """
    if not data:
        return "", 0

    rows = [asdict(person) for person in data.values()]

    # Exclude unwanted fields
    exclude_fields = {
        "membership_status_tag_id",
        "membership_type_tag_id",
        "membership_status",
        "inactive",
    }
    active_rows = [row for row in rows if not row.get("inactive", False)]
    filtered_rows = [
        {k: v for k, v in row.items() if k not in exclude_fields} for row in active_rows
    ]
    cnt_rows = len(filtered_rows)
    if not filtered_rows:
        return "", 0

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=filtered_rows[0].keys())
    writer.writeheader()
    writer.writerows(filtered_rows)
    output.seek(0)
    return output.getvalue(), cnt_rows


def get_person_current_tags(person_id: str) -> Dict[str, Dict[str, str]]:
    """
    Fetch current Membership Status and Type tags for a person.

    Returns:
        Dict with 'status' and 'type' keys, each containing 'tag_id' and 'tag_name'
    """
    current_tags = {}

    for tagging in get_all_tags(person_id):
        field_name = tagging.get("action_builder:field")
        tag_name = tagging.get("action_builder:name")

        # Extract tag ID from identifiers
        tag_id = None
        if tagging.get("identifiers"):
            tag_id = tagging["identifiers"][0].split(":")[-1]

        if field_name == "Membership Status":
            current_tags["status"] = {"tag_id": tag_id, "tag_name": tag_name or ""}
        elif field_name == "Membership Type":
            current_tags["type"] = {"tag_id": tag_id, "tag_name": tag_name or ""}

    return current_tags


def extract_connection_membership_info(taggings: list) -> tuple:
    """
    Extract membership status and type information from connection taggings.

    Returns:
        Tuple of (status_value, status_id, type_value, type_id)
    """
    status_value = status_id = type_value = type_id = None

    for tagging in taggings:
        field_name = tagging.get("action_builder:field")
        tag_value = tagging.get("action_builder:name")

        # Extract tag ID
        tag_id = None
        if tagging.get("identifiers"):
            tag_id = tagging["identifiers"][0].split(":")[-1]

        if field_name == "Membership Status":
            status_value = tag_value
            status_id = tag_id
        elif field_name == "Membership Type":
            type_value = tag_value
            type_id = tag_id

    return status_value, status_id, type_value, type_id


def process_person(person: dict, verbose: bool = True) -> Optional[PersonUnitInfo]:
    """
    Process a single person and return PersonUnitInfo if membership differs.
    Returns None if any API call fails or no differences found.
    """
    try:
        person_id_full = person.get("identifiers", [None])[0]
        if not person_id_full:
            logger.warning("Person missing UUID, skipping")
            return None

        person_uuid = person_id_full.split(":")[-1]

        person_data = get_person(person_uuid)
        sleep(0.2)  # Increased sleep for conservative API usage
        if not person_data:
            logger.warning(f"Could not fetch data for person {person_uuid}")
            return None
        browser_url = person_data.get("browser_url", "URL")

        connections = fetch_connections_from_person(person_data)
        sleep(0.2)  # Increased sleep for conservative API usage
        if not connections:
            logger.warning(f"No connections for person {person_uuid}")
            return None

        unit_data = fetch_unit_from_connection(connections)
        sleep(0.2)  # Increased sleep for conservative API usage
        unit_name = (
            unit_data.get("action_builder:name", "Unknown Unit")
            if unit_data
            else "Unknown Unit"
        )
        taggings = fetch_taggings_from_connection(connections)
        sleep(0.2)  # Increased sleep for conservative API usage
        status_value, status_id, type_value, type_id = (
            extract_connection_membership_info(taggings)
        )

        if (type_value == "Non-Member") and (status_id is None):
            logger.info(
                f"Non Member, {person_uuid}, {unit_name}, {status_value}, {type_value}\n{browser_url}"
            )
        elif not (status_id and type_id):
            logger.warning(
                f"Missing membership info for person {person_uuid}, {unit_name}, {status_value}, {type_value}\n{person_data.get('browser_url', 'URL')}"
            )
            # include return None here to prevent these taggings from being deleted from the person
            # With or without return None the tagging will not make it to the csv

        current_tags = get_person_current_tags(person_uuid)
        sleep(0.2)  # Increased sleep for conservative API usage
        current_status = current_tags.get("status", {}).get("tag_name")
        current_type = current_tags.get("type", {}).get("tag_name")
        if verbose:
            logger.info(
                f"unit connection:person status;type {unit_name} {status_value}:{current_status}; {type_value}:{current_type}\n{browser_url}"
            )

        if status_value != current_status or type_value != current_type:
            return PersonUnitInfo(
                uuid=person_uuid,
                unit_name=unit_name,
                membership_status_tag_id=current_tags.get("status", {}).get("tag_id"),
                membership_type_tag_id=current_tags.get("type", {}).get("tag_id"),
                membership_status=status_value or "",
                membership_type=type_value or "",
                inactive=status_value != "Active",
            )
        return None

    except Exception as e:
        logger.error(f"Error processing person {person.get('identifiers')}: {e}")
        return None


def process_people_batch(
    people_batch: List[dict], verbose: bool = True
) -> List[Tuple[int, Optional[PersonUnitInfo]]]:
    """
    Process a batch of people and return results with their original indices.

    Args:
        people_batch: List of tuples (index, person_dict)
        verbose: Whether to log verbose output

    Returns:
        List of tuples (original_index, PersonUnitInfo or None)
    """
    results = []
    for original_index, person in people_batch:
        person_info = process_person(person, verbose=verbose)
        results.append((original_index, person_info))
    return results


def build_people_unit_map(
    modified_after: Optional[str] = None,
    verbose: Optional[bool] = True,
    max_workers: int = 4,
    batch_size: int = 10,
) -> Dict[str, PersonUnitInfo]:
    """
    Build a dictionary of person_id → PersonUnitInfo for people with membership differences.
    Uses parallel processing with streaming to minimize memory usage.

    Args:
        modified_after: ISO timestamp string. If None, defaults to yesterday.
        verbose: Whether to log verbose output
        max_workers: Maximum number of parallel worker threads
        batch_size: Number of people to process in each batch

    Returns:
        Dictionary mapping person UUIDs to PersonUnitInfo objects
    """
    if not modified_after:
        yesterday = datetime.utcnow() - timedelta(days=1)
        modified_after = yesterday.strftime("%Y-%m-%dT%H:%M:%SZ")

    people_unit_map: Dict[str, PersonUnitInfo] = {}

    logger.info("Starting streaming parallel processing of people...")

    processed_count = 0
    current_batch = []
    batch_index = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Dictionary to track submitted futures
        future_to_batch_info = {}

        # Stream people from the generator
        people_generator = search_people_modified_by(
            modified_after=modified_after, per_page=50
        )

        for person_index, person in enumerate(people_generator):
            # Add person to current batch with original index
            current_batch.append((person_index, person))

            # When batch is full, submit it for processing
            if len(current_batch) >= batch_size:
                future = executor.submit(process_people_batch, current_batch, verbose)
                future_to_batch_info[future] = {
                    "batch_index": batch_index,
                    "batch_size": len(current_batch),
                }
                batch_index += 1
                current_batch = []

            # Process any completed futures
            completed_futures = []
            for future in list(future_to_batch_info.keys()):
                if future.done():
                    completed_futures.append(future)

            for future in completed_futures:
                batch_info = future_to_batch_info.pop(future)
                try:
                    batch_results = future.result()
                    for original_index, person_info in batch_results:
                        processed_count += 1
                        if person_info:
                            people_unit_map[person_info.uuid] = person_info

                        # Log progress
                        if processed_count % 50 == 0:
                            logger.info(f"Processed {processed_count} people")

                except Exception as e:
                    logger.error(
                        f"Batch {batch_info['batch_index']} processing failed: {e}"
                    )

        # Submit final partial batch if it exists
        if current_batch:
            future = executor.submit(process_people_batch, current_batch, verbose)
            future_to_batch_info[future] = {
                "batch_index": batch_index,
                "batch_size": len(current_batch),
            }

        # Wait for all remaining futures to complete
        for future in as_completed(future_to_batch_info.keys()):
            batch_info = future_to_batch_info[future]
            try:
                batch_results = future.result()
                for original_index, person_info in batch_results:
                    processed_count += 1
                    if person_info:
                        people_unit_map[person_info.uuid] = person_info

                    # Log progress
                    if processed_count % 50 == 0:
                        logger.info(f"Processed {processed_count} people")

            except Exception as e:
                logger.error(
                    f"Final batch {batch_info['batch_index']} processing failed: {e}"
                )

    logger.info(f"Completed processing {processed_count} people")
    return people_unit_map


def delete_tag_for_person(person_id: str, tag_id: str, tag_type: str) -> bool:
    """
    Delete a single tag for a person.

    Args:
        person_id: The person's UUID
        tag_id: The tag ID to delete
        tag_type: Type description for logging (e.g., 'status', 'type')

    Returns:
        True if successful, False otherwise
    """
    try:
        delete_tagging(person_id, tag_id)
        sleep(0.2)  # Increased sleep for conservative API usage
        return True
    except Exception as e:
        logger.info(f"Failed to delete {tag_type} tag for {person_id}: {e}")
        return False


def delete_outdated_tags(
    people_map: Dict[str, PersonUnitInfo], max_workers: int = 4
) -> None:
    """
    Delete outdated membership tags for all people in the map using parallel processing.

    Args:
        people_map: Dictionary of person UUIDs to PersonUnitInfo objects
        max_workers: Maximum number of parallel worker threads
    """
    # Collect all deletion tasks
    deletion_tasks = []
    for person_id, info in people_map.items():
        if info.membership_status_tag_id:
            deletion_tasks.append((person_id, info.membership_status_tag_id, "status"))
        if info.membership_type_tag_id:
            deletion_tasks.append((person_id, info.membership_type_tag_id, "type"))

    if not deletion_tasks:
        logger.info("No tags to delete")
        return

    logger.info(
        f"Deleting {len(deletion_tasks)} outdated tags using {max_workers} workers"
    )

    successful_deletions = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all deletion tasks
        future_to_task = {
            executor.submit(delete_tag_for_person, person_id, tag_id, tag_type): (
                person_id,
                tag_id,
                tag_type,
            )
            for person_id, tag_id, tag_type in deletion_tasks
        }

        # Process completed deletions
        for future in as_completed(future_to_task):
            person_id, tag_id, tag_type = future_to_task[future]
            try:
                success = future.result()
                if success:
                    successful_deletions += 1
            except Exception as e:
                logger.error(f"Deletion task failed for {person_id} ({tag_type}): {e}")

    logger.info(
        f"Successfully deleted {successful_deletions}/{len(deletion_tasks)} tags"
    )


def save_csv_to_file(
    csv_content: str, filename: str = "actionbuilder_sync.csv"
) -> None:
    """Save CSV string content to a local file."""
    with open(filename, "w", encoding="utf-8", newline="") as f:
        f.write(csv_content)
    logger.info(f"CSV saved to {filename}")


def main(scheduled: bool = True, max_workers: int = 4, batch_size: int = 10) -> None:
    """
    Main execution function.

    Args:
        scheduled: Whether to check if today is the scheduled run day
        max_workers: Maximum number of parallel worker threads
        batch_size: Number of people to process in each batch
    """
    if not run_today(1) and scheduled:  # Only run on the first of the month
        return

    # Build map of people with membership differences
    modified_after = "2025-07-01T00:00:00Z"
    people_map = build_people_unit_map(
        modified_after, max_workers=max_workers, batch_size=batch_size
    )

    if not people_map:
        logger.info("No membership differences found.")
        return

    logger.info(f"Found {len(people_map)} people with membership differences.")

    # Clean up outdated tags in parallel
    delete_outdated_tags(people_map, max_workers=max_workers)
    logger.info("Outdated tags deletion completed.")

    # Generate and send CSV report
    csv_content, row_count = dict_to_csv(people_map)
    # save_csv_to_file(csv_content)  # for testing
    if csv_content:
        subj = f"WBNG ActionBuilder API Sync ran, {row_count} rows attached"
        send_email(subject=subj, csv_content=csv_content)
        logger.info(f"CSV report sent via email with {row_count} rows.")
    else:
        send_email(
            subject="WBNG ActionBuilder API Sync ran, no entries synced",
            html_content="No data to send",
        )
        logger.info("No entries to email")


if __name__ == "__main__":
    # Conservative settings for API usage
    main(scheduled=True, max_workers=1, batch_size=1)
