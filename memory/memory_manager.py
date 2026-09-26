"""Meeting Memory Manager: Tracks cross-meeting commitments and historical context."""

from typing import List, Dict, Any, Optional
from database.db import get_connection


class MemoryManager:
    @staticmethod
    def get_past_context(query: str = "") -> str:
        """Retrieves past commitments and decisions to inject into current meeting context."""
        with get_connection() as conn:
            cur = conn.cursor()
            if query:
                cur.execute(
                    """SELECT m.title, c.person, c.commitment, c.deadline, c.status, c.timestamp 
                    FROM commitments c 
                    JOIN meetings m ON c.origin_meeting_id = m.id 
                    WHERE c.person LIKE ? OR c.commitment LIKE ? OR m.title LIKE ?
                    ORDER BY c.timestamp DESC LIMIT 10""",
                    (f"%{query}%", f"%{query}%", f"%{query}%"),
                )
            else:
                cur.execute(
                    """SELECT m.title, c.person, c.commitment, c.deadline, c.status, c.timestamp 
                    FROM commitments c 
                    JOIN meetings m ON c.origin_meeting_id = m.id 
                    ORDER BY c.timestamp DESC LIMIT 10"""
                )
            rows = cur.fetchall()

        if not rows:
            return "No prior commitments or past meeting memory found in database."

        lines = ["### Historical Cross-Meeting Commitments:"]
        for r in rows:
            lines.append(
                f"- [Meeting: '{r['title']}']: {r['person']} committed to '{r['commitment']}' "
                f"(Target: {r['deadline']}, Status: {r['status']})"
            )
        return "\n".join(lines)

    @staticmethod
    def audit_commitments_against_transcript(transcript: str) -> Dict[str, Any]:
        """Checks if current transcript mentions fulfillment of open commitments."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, person, commitment FROM commitments WHERE status = 'Open'")
            open_commitments = [dict(r) for r in cur.fetchall()]

        verified = []
        for com in open_commitments:
            person_lower = com["person"].lower()
            if person_lower in transcript.lower() or "completed" in transcript.lower() or "finished" in transcript.lower():
                # Flag potential fulfillment
                verified.append({
                    "id": com["id"],
                    "person": com["person"],
                    "commitment": com["commitment"],
                    "note": f"Referenced in meeting by {com['person']}",
                })

        return {"audited_count": len(open_commitments), "matches": verified}
