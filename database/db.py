"""SQLite Database Layer for Meeting History, Action Items, and Memory."""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import config

DB_PATH = config.DB_PATH


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables and indexes for the Chief of Staff system."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            duration_seconds REAL DEFAULT 0.0,
            audio_file_path TEXT,
            raw_transcript TEXT NOT NULL,
            labeled_transcript TEXT NOT NULL,
            summary TEXT,
            key_decisions TEXT,
            tags TEXT
        );

        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT NOT NULL,
            speaker_label TEXT NOT NULL,
            canonical_name TEXT,
            email TEXT,
            speaking_time_seconds REAL DEFAULT 0.0,
            FOREIGN KEY(meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS speaker_contacts (
            canonical_name TEXT PRIMARY KEY COLLATE NOCASE,
            email TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS action_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT NOT NULL,
            task TEXT NOT NULL,
            owner TEXT NOT NULL,
            deadline TEXT,
            priority TEXT DEFAULT 'Medium' CHECK(priority IN ('High', 'Medium', 'Low')),
            status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'In Progress', 'Completed')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS commitments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin_meeting_id TEXT NOT NULL,
            person TEXT NOT NULL,
            commitment TEXT NOT NULL,
            deadline TEXT,
            resolved_in_meeting_id TEXT,
            status TEXT DEFAULT 'Open' CHECK(status IN ('Open', 'Resolved', 'Carried Over', 'Overdue')),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(origin_meeting_id) REFERENCES meetings(id)
        );

        CREATE TABLE IF NOT EXISTS email_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT NOT NULL,
            recipient_name TEXT NOT NULL,
            recipient_email TEXT,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            sent_status INTEGER DEFAULT 0,
            sent_at TIMESTAMP,
            FOREIGN KEY(meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS calendar_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT NOT NULL,
            proposed_title TEXT NOT NULL,
            suggested_slot TEXT NOT NULL,
            participants TEXT NOT NULL,
            conflict_detected INTEGER DEFAULT 0,
            conflict_details TEXT,
            status TEXT DEFAULT 'Suggested'
        );

        CREATE INDEX IF NOT EXISTS idx_meetings_created ON meetings(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_commitments_person ON commitments(person, status);
        CREATE INDEX IF NOT EXISTS idx_action_items_meeting ON action_items(meeting_id);
        """)
        conn.commit()


def get_speaker_contacts() -> List[Dict[str, Any]]:
    """Return saved speaker email profiles independently of meeting history."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT canonical_name, email FROM speaker_contacts ORDER BY canonical_name COLLATE NOCASE")
        return [dict(row) for row in cur.fetchall()]


def save_speaker_contact(canonical_name: str, email: str) -> None:
    """Insert or update a speaker's reusable email profile."""
    name = (canonical_name or "").strip()
    address = (email or "").strip()
    if not name or not address:
        raise ValueError("Speaker name and email address are required.")

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO speaker_contacts (canonical_name, email)
            VALUES (?, ?)
            ON CONFLICT(canonical_name) DO UPDATE SET
                email = excluded.email,
                updated_at = CURRENT_TIMESTAMP""",
            (name, address),
        )
        conn.commit()


def clear_all_meetings():
    """Delete all meeting records and their related artifacts from SQLite."""
    with get_connection() as conn:
        cur = conn.cursor()
        for table in (
            "participants",
            "action_items",
            "commitments",
            "email_drafts",
            "calendar_slots",
            "meetings",
        ):
            cur.execute(f"DELETE FROM {table}")
        cur.execute(
            "DELETE FROM sqlite_sequence "
            "WHERE name IN ('participants', 'action_items', 'commitments', 'email_drafts', 'calendar_slots')"
        )
        conn.commit()


def save_meeting_bundle(
    meeting_id: str,
    title: str,
    raw_transcript: str,
    labeled_transcript: str,
    summary: str,
    key_decisions: List[str],
    action_items: List[Dict[str, Any]],
    email_drafts: List[Dict[str, Any]],
    calendar_suggestions: List[Dict[str, Any]],
    commitments: List[Dict[str, Any]],
    audio_path: Optional[str] = None,
    duration: float = 0.0,
):
    """Atomically persists all artifacts generated during a meeting."""
    with get_connection() as conn:
        cur = conn.cursor()

        # Save Meeting Row
        cur.execute(
            """INSERT OR REPLACE INTO meetings 
            (id, title, duration_seconds, audio_file_path, raw_transcript, labeled_transcript, summary, key_decisions, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                meeting_id,
                title,
                duration,
                audio_path,
                raw_transcript,
                labeled_transcript,
                summary,
                json.dumps(key_decisions),
                json.dumps(["Product", "Sprint", "Executive"]),
            ),
        )

        # Save Action Items
        for item in action_items:
            cur.execute(
                """INSERT INTO action_items (meeting_id, task, owner, deadline, priority, status)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    meeting_id,
                    item.get("task", ""),
                    item.get("owner", "Unassigned"),
                    item.get("deadline", "TBD"),
                    item.get("priority", "Medium"),
                    "Pending",
                ),
            )

        # Save Email Drafts
        for draft in email_drafts:
            cur.execute(
                """INSERT INTO email_drafts (meeting_id, recipient_name, recipient_email, subject, body)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    meeting_id,
                    draft.get("recipient_name", "Team Member"),
                    draft.get("recipient_email", ""),
                    draft.get("subject", "Meeting Follow-up & Action Items"),
                    draft.get("body", ""),
                ),
            )

        # Save Calendar Suggestions
        for slot in calendar_suggestions:
            cur.execute(
                """INSERT INTO calendar_slots (meeting_id, proposed_title, suggested_slot, participants, conflict_detected, conflict_details)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    meeting_id,
                    slot.get("title", "Project Follow-up Sync"),
                    slot.get("suggested_slot", "Upcoming Business Day"),
                    json.dumps(slot.get("participants", [])),
                    1 if slot.get("conflict_detected") else 0,
                    slot.get("conflict_details", ""),
                ),
            )

        # Save Cross-Meeting Commitments (Memory)
        for com in commitments:
            cur.execute(
                """INSERT INTO commitments (origin_meeting_id, person, commitment, deadline, status)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    meeting_id,
                    com.get("person", "Unknown"),
                    com.get("commitment", ""),
                    com.get("deadline", "TBD"),
                    com.get("status", "Open"),
                ),
            )

        conn.commit()


def get_all_meetings() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM meetings ORDER BY created_at DESC")
        return [dict(row) for row in cur.fetchall()]


def get_meeting_by_id(meeting_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_action_items(meeting_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        if meeting_id:
            cur.execute("SELECT * FROM action_items WHERE meeting_id = ? ORDER BY id DESC", (meeting_id,))
        else:
            cur.execute("SELECT * FROM action_items ORDER BY id DESC")
        return [dict(row) for row in cur.fetchall()]


def update_action_item_status(item_id: int, new_status: str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE action_items SET status = ? WHERE id = ?", (new_status, item_id))
        conn.commit()


def get_commitments(person: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        if person:
            cur.execute(
                """SELECT c.*, m.title as meeting_title 
                FROM commitments c 
                JOIN meetings m ON c.origin_meeting_id = m.id 
                WHERE c.person LIKE ? 
                ORDER BY c.timestamp DESC""",
                (f"%{person}%",),
            )
        else:
            cur.execute(
                """SELECT c.*, m.title as meeting_title 
                FROM commitments c 
                JOIN meetings m ON c.origin_meeting_id = m.id 
                ORDER BY c.timestamp DESC"""
            )
        return [dict(row) for row in cur.fetchall()]


def get_email_drafts(meeting_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        if meeting_id:
            cur.execute("SELECT * FROM email_drafts WHERE meeting_id = ? ORDER BY id DESC", (meeting_id,))
        else:
            cur.execute("SELECT * FROM email_drafts ORDER BY id DESC")
        return [dict(row) for row in cur.fetchall()]


def get_calendar_slots(meeting_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        if meeting_id:
            cur.execute("SELECT * FROM calendar_slots WHERE meeting_id = ? ORDER BY id DESC", (meeting_id,))
        else:
            cur.execute("SELECT * FROM calendar_slots ORDER BY id DESC")
        slots = []
        for row in cur.fetchall():
            d = dict(row)
            parts = d.get("participants")
            if isinstance(parts, str):
                try:
                    d["participants"] = json.loads(parts)
                except Exception:
                    d["participants"] = [parts] if parts else []
            slots.append(d)
        return slots


def get_meeting_bundle_full(meeting_id: str) -> Optional[Dict[str, Any]]:
    """Reconstructs the full meeting report bundle for UI viewing."""
    meeting = get_meeting_by_id(meeting_id)
    if not meeting:
        return None

    summary = meeting.get("summary") or ""
    kd_raw = meeting.get("key_decisions") or "[]"
    try:
        key_decisions = json.loads(kd_raw) if isinstance(kd_raw, str) else kd_raw
    except Exception:
        key_decisions = [line.strip("- *") for line in str(kd_raw).split("\n") if line.strip()]

    if not isinstance(key_decisions, list):
        key_decisions = [str(key_decisions)] if key_decisions else []

    action_items = get_action_items(meeting_id)
    email_drafts = get_email_drafts(meeting_id)
    calendar_suggestions = get_calendar_slots(meeting_id)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM commitments WHERE origin_meeting_id = ? ORDER BY id DESC", (meeting_id,))
        commitments = [dict(r) for r in cur.fetchall()]

    return {
        "meeting_id": meeting["id"],
        "title": meeting["title"],
        "raw_transcript": meeting["raw_transcript"],
        "labeled_transcript": meeting["labeled_transcript"],
        "summary": summary,
        "key_decisions": key_decisions,
        "action_items": action_items,
        "commitments": commitments,
        "email_drafts": email_drafts,
        "calendar_suggestions": calendar_suggestions,
        "audio_path": meeting.get("audio_file_path"),
        "created_at": meeting.get("created_at"),
    }


def get_latest_meeting_bundle() -> Optional[Dict[str, Any]]:
    """Retrieves full bundle for the most recent meeting in the database."""
    meetings = get_all_meetings()
    if not meetings:
        return None
    return get_meeting_bundle_full(meetings[0]["id"])


def get_system_stats() -> Dict[str, Any]:
    """Returns aggregated counts for meetings, pending tasks, and commitments."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM meetings")
        total_meetings = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM action_items WHERE status != 'Completed'")
        pending_tasks = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM action_items")
        total_tasks = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM commitments WHERE status = 'Open'")
        open_commitments = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM commitments")
        total_commitments = cur.fetchone()[0]
        return {
            "total_meetings": total_meetings,
            "pending_tasks": pending_tasks,
            "total_tasks": total_tasks,
            "open_commitments": open_commitments,
            "total_commitments": total_commitments,
        }


