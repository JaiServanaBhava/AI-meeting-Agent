"""Pydantic Models and Schemas for Data Transfer Objects."""

from typing import List, Optional
try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def dict(self):
            return self.__dict__
    def Field(*args, **kwargs):
        return kwargs.get("default", None)



class ActionItemSchema(BaseModel):
    task: str = Field(..., description="Action item description")
    owner: str = Field(..., description="Responsible person or speaker label")
    deadline: Optional[str] = Field("TBD", description="Target completion date or timeframe")
    priority: str = Field("Medium", description="Priority: High, Medium, or Low")


class CommitmentSchema(BaseModel):
    person: str = Field(..., description="Person who made the commitment")
    commitment: str = Field(..., description="Promise, pledge, or deliverable agreed upon")
    deadline: Optional[str] = Field("TBD", description="Expected deadline")
    status: str = Field("Open", description="Status: Open, Resolved, Overdue")


class EmailDraftSchema(BaseModel):
    recipient_name: str = Field(..., description="Participant name or speaker label")
    recipient_email: Optional[str] = Field("", description="Email address if known")
    subject: str = Field(..., description="Subject line for the follow-up email")
    body: str = Field(..., description="Personalized email body text")


class CalendarSlotSchema(BaseModel):
    title: str = Field(..., description="Meeting title or purpose")
    suggested_slot: str = Field(..., description="Recommended date and time slot")
    participants: List[str] = Field(default_factory=list, description="Participants needed")
    conflict_detected: bool = Field(False, description="Whether any conflicts were found")
    conflict_details: Optional[str] = Field("", description="Description of any detected conflict")


class MeetingAnalysisResult(BaseModel):
    summary: str = Field(..., description="Executive summary in markdown")
    key_decisions: List[str] = Field(default_factory=list, description="List of decisions agreed upon")
    action_items: List[ActionItemSchema] = Field(default_factory=list, description="Action items")
    new_commitments: List[CommitmentSchema] = Field(default_factory=list, description="Commitments made")
    email_drafts: List[EmailDraftSchema] = Field(default_factory=list, description="Personalized emails")
    calendar_suggestions: List[CalendarSlotSchema] = Field(default_factory=list, description="Suggested meeting slots")
    historical_notes: Optional[str] = Field("", description="Cross-meeting memory observations")
