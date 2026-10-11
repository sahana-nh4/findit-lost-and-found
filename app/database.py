import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "findit.db")


def get_db_connection() -> sqlite3.Connection:
    """Creates and returns a connection to the SQLite database with Row factory."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Initializes the database schema and seeds initial sample records if empty."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                type TEXT NOT NULL,             -- 'lost' or 'found'
                category TEXT NOT NULL,         -- Electronics, Wallets & Bags, Keys, etc.
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                date_event TEXT NOT NULL,       -- YYYY-MM-DD
                contact_name TEXT NOT NULL,
                contact_info TEXT NOT NULL,
                image_url TEXT,
                is_returned INTEGER NOT NULL DEFAULT 0, -- 0 = active, 1 = returned/resolved
                created_at TEXT NOT NULL
            );
        """)
        conn.commit()

        # Check if table has records, seed initial demo items if empty
        cursor.execute("SELECT COUNT(*) AS count FROM items")
        count = cursor.fetchone()["count"]

        if count == 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sample_items = [
                (
                    "Black Leather Fossil Wallet",
                    "lost",
                    "Wallets & Bags",
                    "Lost dark brown/black bifold wallet containing student ID, library card, and bus pass. Lost during afternoon study session.",
                    "Main Campus Library, 2nd Floor Quiet Zone",
                    "2026-10-09",
                    "Alex Morgan",
                    "alex.morgan@campus.edu",
                    None,
                    0,
                    now
                ),
                (
                    "Set of Keys with Honda Fob",
                    "found",
                    "Keys",
                    "Found a set of 3 keys with a Honda remote key fob and a miniature blue flashlight carabiner.",
                    "Student Cafeteria near Vending Machines",
                    "2026-10-10",
                    "Samira Patel (Campus Security)",
                    "security-desk@campus.edu",
                    None,
                    0,
                    now
                ),
                (
                    "Apple AirPods Pro (2nd Gen)",
                    "lost",
                    "Electronics",
                    "AirPods Pro in white charging case. Case has a small cartoon astronaut sticker on the back lid.",
                    "Gymnasium Locker Room / Bench Area",
                    "2026-10-08",
                    "David Chen",
                    "+1 (555) 234-5678",
                    None,
                    0,
                    now
                ),
                (
                    "Friendly Orange Tabby Cat",
                    "found",
                    "Pets",
                    "Small young domestic shorthair cat with orange/white stripes and a yellow collar with a small bell. Very gentle and affectionate.",
                    "Oak Street Community Park, near the fountain",
                    "2026-10-10",
                    "Elena Rostova",
                    "elena.r@communitymail.org",
                    None,
                    0,
                    now
                ),
                (
                    "Calculus III Textbook & Blue Notebook",
                    "found",
                    "Documents & Books",
                    "Hardcover Thomas' Calculus 14th edition and a blue spiral notebook with handwritten lecture notes.",
                    "Lecture Hall B, Row 4",
                    "2026-10-07",
                    "Prof. Rivera",
                    "mrivera@university.edu",
                    None,
                    1,  # marked as returned already for demo
                    now
                )
            ]

            cursor.executemany("""
                INSERT INTO items (
                    title, type, category, description, location,
                    date_event, contact_name, contact_info, image_url,
                    is_returned, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_items)
            conn.commit()


def mask_contact(contact: str) -> str:
    """
    Masks sensitive contact details for public listing views to prevent scraping/spam.
    e.g., 'alex.morgan@campus.edu' -> 'a***n@campus.edu'
    or '+1 (555) 234-5678' -> '+1 (555) ***-**78'
    """
    if not contact:
        return "Protected"
    contact = contact.strip()
    if "@" in contact:
        parts = contact.split("@", 1)
        name, domain = parts[0], parts[1]
        if len(name) <= 2:
            masked_name = name[0] + "***"
        else:
            masked_name = name[0] + "***" + name[-1]
        return f"{masked_name}@{domain}"
    else:
        if len(contact) <= 4:
            return "****"
        return contact[:3] + " ***-**" + contact[-2:]


def get_all_items(
    search: Optional[str] = None,
    item_type: Optional[str] = None,
    category: Optional[str] = None,
    status_filter: Optional[str] = None,
    reveal_contacts: bool = False
) -> List[Dict[str, Any]]:
    """Retrieves items with filtering, search query, and conditional contact masking."""
    query = "SELECT * FROM items WHERE 1=1"
    params: List[Any] = []

    if search:
        search_pattern = f"%{search.strip()}%"
        query += " AND (title LIKE ? OR description LIKE ? OR location LIKE ?)"
        params.extend([search_pattern, search_pattern, search_pattern])

    if item_type and item_type.lower() in ["lost", "found"]:
        query += " AND type = ?"
        params.append(item_type.lower())

    if category and category != "all":
        query += " AND category = ?"
        params.append(category)

    if status_filter == "active":
        query += " AND is_returned = 0"
    elif status_filter == "returned":
        query += " AND is_returned = 1"

    query += " ORDER BY is_returned ASC, id DESC"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        items = []
        for row in rows:
            item = dict(row)
            if not reveal_contacts:
                item["contact_info_masked"] = mask_contact(item["contact_info"])
                # Remove raw contact_info from public bulk listings
                del item["contact_info"]
            items.append(item)
        return items


def get_item_by_id(item_id: int, reveal_contacts: bool = False) -> Optional[Dict[str, Any]]:
    """Fetches a single item by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if not row:
            return None
        item = dict(row)
        if not reveal_contacts:
            item["contact_info_masked"] = mask_contact(item["contact_info"])
            del item["contact_info"]
        return item


def create_item(
    title: str,
    item_type: str,
    category: str,
    description: str,
    location: str,
    date_event: str,
    contact_name: str,
    contact_info: str,
    image_url: Optional[str] = None
) -> int:
    """Inserts a new lost or found item into the database."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO items (
                title, type, category, description, location,
                date_event, contact_name, contact_info, image_url,
                is_returned, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
        """, (
            title.strip(),
            item_type.strip().lower(),
            category.strip(),
            description.strip(),
            location.strip(),
            date_event.strip(),
            contact_name.strip(),
            contact_info.strip(),
            image_url,
            now
        ))
        conn.commit()
        return cursor.lastrowid


def toggle_returned_status(item_id: int) -> Optional[Dict[str, Any]]:
    """Toggles or sets the returned/resolved status of an item."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_returned FROM items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if not row:
            return None
        new_status = 1 if row["is_returned"] == 0 else 0
        cursor.execute("UPDATE items SET is_returned = ? WHERE id = ?", (new_status, item_id))
        conn.commit()

        cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        updated = dict(cursor.fetchone())
        return updated


def delete_item(item_id: int) -> bool:
    """Deletes an item from the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_portal_stats() -> Dict[str, int]:
    """Returns portal statistics for the dashboard hero counters."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM items")
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS lost_count FROM items WHERE type = 'lost' AND is_returned = 0")
        lost_count = cursor.fetchone()["lost_count"]

        cursor.execute("SELECT COUNT(*) AS found_count FROM items WHERE type = 'found' AND is_returned = 0")
        found_count = cursor.fetchone()["found_count"]

        cursor.execute("SELECT COUNT(*) AS returned_count FROM items WHERE is_returned = 1")
        returned_count = cursor.fetchone()["returned_count"]

        return {
            "total": total,
            "lost": lost_count,
            "found": found_count,
            "returned": returned_count
        }


# Ensure tables and seed data exist immediately upon import
init_db()
