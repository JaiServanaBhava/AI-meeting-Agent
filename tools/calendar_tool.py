"""CrewAI Tool: Simulated Calendar Availability, Conflict Detection, and Slot Suggester."""

from typing import Type
import random
from datetime import datetime, timedelta

try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    def Field(*args, **kwargs):
        return kwargs.get("default", None)

try:
    from crewai.tools import BaseTool
except ImportError:
    class BaseTool:
        def __init__(self, **kwargs):
            pass



class CalendarToolSchema(BaseModel):
    participants: str = Field(..., description="Comma-separated participant names or speaker labels.")
    purpose: str = Field(..., description="Objective or subject of the proposed follow-up sync.")


class SimulatedCalendarTool(BaseTool):
    name: str = "simulated_calendar_tool"
    description: str = (
        "Simulates team member calendar availability, runs conflict detection, and suggests consensus meeting slots."
    )
    args_schema: Type[BaseModel] = CalendarToolSchema

    def _run(self, participants: str, purpose: str) -> str:
        names = [p.strip() for p in participants.split(",") if p.strip()]
        
        # Calculate target business dates
        now = datetime.now()
        target_day_1 = now + timedelta(days=2)
        target_day_2 = now + timedelta(days=3)

        slot_options = [
            f"{target_day_1.strftime('%A, %b %d')} at 10:00 AM - 10:45 AM EST",
            f"{target_day_1.strftime('%A, %b %d')} at 2:00 PM - 3:00 PM EST",
            f"{target_day_2.strftime('%A, %b %d')} at 3:30 PM - 4:15 PM EST",
        ]

        # Simulate intelligent conflict detection
        conflict_detected = len(names) > 2
        selected_slot = slot_options[1] if conflict_detected else slot_options[0]
        conflict_msg = (
            f"Conflict detected for {names[-1] if names else 'participant'} on Option 1 (10:00 AM). "
            f"Resolved by shifting to Option 2."
            if conflict_detected
            else "All participants have open availability on the primary slot."
        )

        result = (
            f"### Calendar Simulation Report: {purpose}\n"
            f"- **Attendees Checked:** {', '.join(names) if names else 'Full Team'}\n"
            f"- **Conflict Status:** {conflict_msg}\n"
            f"- **Recommended Consensus Slot:** {selected_slot}\n"
            f"- **Backup Available Slot:** {slot_options[2]}"
        )
        return result
