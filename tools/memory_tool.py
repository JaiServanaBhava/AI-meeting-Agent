"""CrewAI Tool: SQLite Meeting Memory & Commitments Retrieval."""

from typing import Type
try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    def Field(*args, **kwargs):
        return kwargs.get("default", None)

from database.db import get_connection

try:
    from crewai.tools import BaseTool
except ImportError:
    # Minimal BaseTool shim if crewai is not installed yet
    class BaseTool:
        def __init__(self, **kwargs):
            pass



class MemoryToolSchema(BaseModel):
    query: str = Field(..., description="Name of participant, deliverable, or topic to query historical memory for.")


class MeetingMemoryTool(BaseTool):
    name: str = "meeting_memory_tool"
    description: str = (
        "Retrieves previous meeting context, historical decisions, and past commitments from the SQLite database. "
        "Use this tool to verify what participants promised in earlier meetings."
    )
    args_schema: Type[BaseModel] = MemoryToolSchema

    def _run(self, query: str) -> str:
        query = (query or "").strip()
        with get_connection() as conn:
            cur = conn.cursor()
            if query:
                cur.execute(
                    """SELECT m.title, c.person, c.commitment, c.deadline, c.status, c.timestamp 
                    FROM commitments c 
                    JOIN meetings m ON c.origin_meeting_id = m.id 
                    WHERE c.person LIKE ? OR c.commitment LIKE ? OR m.title LIKE ?
                    ORDER BY c.timestamp DESC LIMIT 8""",
                    (f"%{query}%", f"%{query}%", f"%{query}%"),
                )
            else:
                cur.execute(
                    """SELECT m.title, c.person, c.commitment, c.deadline, c.status, c.timestamp 
                    FROM commitments c 
                    JOIN meetings m ON c.origin_meeting_id = m.id 
                    ORDER BY c.timestamp DESC LIMIT 8"""
                )
            rows = cur.fetchall()

        if not rows:
            return "No previous commitments or past meeting memory found for this query."

        output = ["### Historical Cross-Meeting Commitments Retrieved:"]
        for r in rows:
            output.append(
                f"- [Meeting: '{r['title']}']: {r['person']} committed: '{r['commitment']}' "
                f"| Deadline: {r['deadline']} | Status: {r['status']}"
            )
        return "\n".join(output)
