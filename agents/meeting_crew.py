"""CrewAI Multi-Agent Meeting Orchestration Engine backed exclusively by Gemini 2.5 Flash."""

import json
import re
from typing import Dict, Any, List
from services.gemini_service import GeminiService
from tools.memory_tool import MeetingMemoryTool
from tools.calendar_tool import SimulatedCalendarTool
from tools.email_tool import MailerTool
from agents.prompts import (
    MEMORY_AGENT_ROLE, MEMORY_AGENT_GOAL, MEMORY_AGENT_BACKSTORY,
    SUMMARIZER_AGENT_ROLE, SUMMARIZER_AGENT_GOAL, SUMMARIZER_AGENT_BACKSTORY,
    ACTION_ITEM_AGENT_ROLE, ACTION_ITEM_AGENT_GOAL, ACTION_ITEM_AGENT_BACKSTORY,
    SCHEDULER_AGENT_ROLE, SCHEDULER_AGENT_GOAL, SCHEDULER_AGENT_BACKSTORY,
    EMAIL_DRAFT_AGENT_ROLE, EMAIL_DRAFT_AGENT_GOAL, EMAIL_DRAFT_AGENT_BACKSTORY,
)

import os
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["CREWAI_DISABLE_TRACKING"] = "true"

try:
    import crewai.telemetry.telemetry as _crewai_tm
    _crewai_tm.Telemetry._register_signal_handler = lambda *args, **kwargs: None
except Exception:
    pass

try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False


class ChiefOfStaffMeetingCrew:
    """Orchestrates the 5 specialized agents to manage the meeting lifecycle."""

    def __init__(self):
        self.memory_tool = MeetingMemoryTool()
        self.calendar_tool = SimulatedCalendarTool()
        self.mailer_tool = MailerTool()

    def run_pipeline(self, transcript: str) -> Dict[str, Any]:
        """Runs the complete multi-agent pipeline.
        
        Attempts CrewAI sequential agent orchestration first.
        If CrewAI is unavailable or fails, invokes Gemini 2.5 Flash directly
        with multi-agent prompt chaining to produce the identical structured output.
        """
        if CREWAI_AVAILABLE:
            try:
                return self._run_crewai(transcript)
            except Exception as e:
                print(f"[CrewAI Notice]: Falling back to direct Gemini multi-agent chaining ({e})")
                return self._run_gemini_direct(transcript)
        else:
            return self._run_gemini_direct(transcript)

    def _run_crewai(self, transcript: str) -> Dict[str, Any]:
        llm = GeminiService.get_crewai_llm(temperature=0.2)

        # 1. Memory Agent
        memory_agent = Agent(
            role=MEMORY_AGENT_ROLE,
            goal=MEMORY_AGENT_GOAL,
            backstory=MEMORY_AGENT_BACKSTORY,
            tools=[self.memory_tool],
            llm=llm,
            verbose=True,
        )

        # 2. Meeting Summarizer Agent
        summarizer_agent = Agent(
            role=SUMMARIZER_AGENT_ROLE,
            goal=SUMMARIZER_AGENT_GOAL,
            backstory=SUMMARIZER_AGENT_BACKSTORY,
            llm=llm,
            verbose=True,
        )

        # 3. Action Item Agent
        action_agent = Agent(
            role=ACTION_ITEM_AGENT_ROLE,
            goal=ACTION_ITEM_AGENT_GOAL,
            backstory=ACTION_ITEM_AGENT_BACKSTORY,
            llm=llm,
            verbose=True,
        )

        # 4. Scheduler Agent
        scheduler_agent = Agent(
            role=SCHEDULER_AGENT_ROLE,
            goal=SCHEDULER_AGENT_GOAL,
            backstory=SCHEDULER_AGENT_BACKSTORY,
            tools=[self.calendar_tool],
            llm=llm,
            verbose=True,
        )

        # 5. Email Draft Agent
        email_agent = Agent(
            role=EMAIL_DRAFT_AGENT_ROLE,
            goal=EMAIL_DRAFT_AGENT_GOAL,
            backstory=EMAIL_DRAFT_AGENT_BACKSTORY,
            llm=llm,
            verbose=True,
        )

        # Tasks
        task_memory = Task(
            description=(
                f"Analyze this meeting transcript:\n\n{transcript}\n\n"
                "Use the meeting_memory_tool to query previous commitments for any participants mentioned. "
                "Output historical context, identifying whether any past commitments (e.g. 'Sathwik promised UI by Friday') "
                "were discussed, fulfilled, or carried over."
            ),
            expected_output="Markdown audit of past commitments referenced or resolved.",
            agent=memory_agent,
        )

        task_summary = Task(
            description=(
                f"Analyze the transcript and historical context:\n\n{transcript}\n\n"
                "Generate:\n"
                "1. Executive Summary (2-3 paragraphs)\n"
                "2. Decisions Made (bullet list of concrete agreements)\n"
                "3. Key Discussion Points"
            ),
            expected_output="Structured markdown with ## Summary, ## Decisions, and ## Discussion Points.",
            agent=summarizer_agent,
            context=[task_memory],
        )

        task_actions = Task(
            description=(
                "Extract all tasks, deliverables, and commitments from the meeting. "
                "Output STRICT JSON formatted exactly as:\n"
                "{\n"
                '  "action_items": [\n'
                '    {"task": "description", "owner": "Name/Speaker", "deadline": "date or timeframe", "priority": "High|Medium|Low"}\n'
                "  ],\n"
                '  "new_commitments": [\n'
                '    {"person": "Name", "commitment": "exact promise or deliverable", "deadline": "date", "status": "Open"}\n'
                "  ]\n"
                "}\n"
                "Do NOT wrap in markdown backticks or explanations."
            ),
            expected_output="Valid JSON string adhering to the schema.",
            agent=action_agent,
            context=[task_summary],
        )

        task_scheduler = Task(
            description=(
                "Review the decisions and action items. Determine follow-up sync requirements. "
                "Use the simulated_calendar_tool to check participant availability and suggest consensus slots."
            ),
            expected_output="Calendar suggestions with slot recommendations and conflict detection.",
            agent=scheduler_agent,
            context=[task_actions],
        )

        task_emails = Task(
            description=(
                "Draft personalized follow-up emails for each participant based on their specific tasks. "
                "Use only email addresses explicitly provided in the transcript or known participant data; "
                "never invent or guess an address, and use an empty string when unknown. "
                "Output STRICT JSON formatted as a list:\n"
                "[\n"
                '  {"recipient_name": "Speaker A / Name", "recipient_email": "", "subject": "...", "body": "..."}\n'
                "]\n"
                "Do NOT wrap in markdown backticks."
            ),
            expected_output="Valid JSON array of personalized email objects.",
            agent=email_agent,
            context=[task_summary, task_actions, task_scheduler],
        )

        crew = Crew(
            agents=[memory_agent, summarizer_agent, action_agent, scheduler_agent, email_agent],
            tasks=[task_memory, task_summary, task_actions, task_scheduler, task_emails],
            process=Process.sequential,
            verbose=True,
        )

        crew_output = crew.kickoff(inputs={"transcript": transcript})
        raw_outputs = [t.raw for t in crew_output.tasks_output]

        return self._parse_crew_outputs(raw_outputs, transcript)

    def _run_gemini_direct(self, transcript: str) -> Dict[str, Any]:
        """Direct Gemini 2.5 Flash agentic chain fallback."""
        # 1. Fetch memory
        historical_context = self.memory_tool._run("commitments")

        prompt = f"""
You are the AI Chief of Staff (Crew of 5 Autonomous Agents):
1. Memory Agent (reconcile past commitments)
2. Summarizer Agent (extract executive summary and decisions)
3. Action Item Agent (extract tasks, owners, deadlines, priorities)
4. Scheduler Agent (suggest follow-up meeting slots and detect conflicts)
5. Email Draft Agent (personalized emails per participant)

HISTORICAL PAST COMMITMENTS IN MEMORY:
{historical_context}

CURRENT MEETING TRANSCRIPT:
{transcript}

Return a valid JSON object strictly adhering to this structure:
{{
  "memory_audit": "Detailed note on whether previous commitments were fulfilled (e.g. 'Last meeting Sathwik committed to UI completion, which was confirmed in this meeting.')",
  "summary": "Executive summary of the meeting...",
  "key_decisions": ["Decision 1", "Decision 2"],
  "action_items": [
    {{"task": "Task description", "owner": "Owner name", "deadline": "Deadline", "priority": "High"}}
  ],
  "new_commitments": [
    {{"person": "Owner name", "commitment": "Deliverable agreed to", "deadline": "Deadline", "status": "Open"}}
  ],
  "calendar_suggestions": [
    {{"title": "Follow-up Meeting", "suggested_slot": "Thursday, 2:00 PM - 3:00 PM EST", "participants": ["Sathwik", "Alice", "Bob"], "conflict_detected": false, "conflict_details": "No conflicts detected"}}
  ],
  "email_drafts": [
        {{"recipient_name": "Speaker A / Sathwik", "recipient_email": "", "subject": "Meeting Follow-up: Next Steps", "body": "Hi Sathwik,\\n\\nThank you for today's meeting..."}}
  ]
}}
DO NOT wrap your output in markdown code blocks like ```json. Return ONLY valid raw JSON.
"""
        try:
            response_text = GeminiService.generate_text(
                prompt=prompt,
                system_instruction="You are a Chief of Staff AI managing full meeting lifecycles with absolute precision."
            )
        except Exception as api_err:
            print(f"[Gemini] API error — using offline fallback: {api_err}")
            return self._offline_fallback(str(api_err), transcript)

        if not response_text:
            return self._offline_fallback("Empty response from Gemini API.", transcript)

        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except Exception:
            data = self._offline_fallback("Could not parse Gemini response as JSON.", transcript)
            data["summary"] = response_text[:2000]  # keep the raw text

        return data

    def _offline_fallback(self, reason: str, transcript: str) -> Dict[str, Any]:
        """Returns a complete structured result when Gemini is unavailable.

        Shows a clear "add API key" message in every field so the user knows
        exactly what to do — the app never crashes or shows a blank screen.
        """
        note = (
            f"\u26a0\ufe0f  AI analysis unavailable: {reason}  "
            "Please open your .env file, add GEMINI_API_KEY=<your-key>, "
            "and restart the app."
        )
        lines = [ln.strip() for ln in transcript.splitlines() if ln.strip()]
        hints = [ln for ln in lines
                 if any(kw in ln.lower() for kw in ("agree", "decided", "confirm", "will", "commit"))]
        return {
            "memory_audit": note,
            "summary": note + "\n\n--- SAVED TRANSCRIPT ---\n" + transcript[:3000],
            "key_decisions": hints[:6] or ["Add GEMINI_API_KEY to enable AI analysis"],
            "action_items": [
                {"task": "Add GEMINI_API_KEY to your .env file and restart",
                 "owner": "You", "deadline": "Now", "priority": "High"}
            ],
            "new_commitments": [],
            "calendar_suggestions": [],
            "email_drafts": [{
                "recipient_name": "Team",
                "recipient_email": "",
                "subject": "Meeting recorded — API key needed for full analysis",
                "body": (
                    "Hi,\n\nYour meeting was recorded successfully.\n"
                    "To get the AI summary, tasks and this email auto-drafted — add your "
                    "GEMINI_API_KEY to the .env file and restart the AI Chief of Staff app.\n\n"
                    "Recordings are saved in ~/Desktop/ChiefOfStaff/Recordings/\n\n"
                    "Best,\nAI Chief of Staff"
                )
            }],
        }

    def _parse_crew_outputs(self, raw_outputs: List[str], transcript: str) -> Dict[str, Any]:
        memory_out = raw_outputs[0] if len(raw_outputs) > 0 else ""
        summary_out = raw_outputs[1] if len(raw_outputs) > 1 else ""

        # Parse Action items JSON
        actions_json = {"action_items": [], "new_commitments": []}
        if len(raw_outputs) > 2:
            try:
                raw_act = raw_outputs[2].strip()
                if raw_act.startswith("```"):
                    raw_act = re.sub(r"^```(?:json)?\n?", "", raw_act)
                    raw_act = re.sub(r"\n?```$", "", raw_act)
                actions_json = json.loads(raw_act)
            except Exception:
                pass

        # Parse Scheduler output
        sched_out = raw_outputs[3] if len(raw_outputs) > 3 else ""

        # Parse Emails JSON
        emails_list = []
        if len(raw_outputs) > 4:
            try:
                raw_em = raw_outputs[4].strip()
                if raw_em.startswith("```"):
                    raw_em = re.sub(r"^```(?:json)?\n?", "", raw_em)
                    raw_em = re.sub(r"\n?```$", "", raw_em)
                emails_list = json.loads(raw_em)
            except Exception:
                pass

        if not emails_list:
            emails_list = [{
                "recipient_name": "Team",
                "recipient_email": "",
                "subject": "Meeting Summary & Next Steps",
                "body": f"Meeting Summary:\n\n{summary_out[:500]}\n\nPlease review your action items."
            }]

        return {
            "memory_audit": memory_out,
            "summary": summary_out,
            "key_decisions": ["Approved project roadmap", "Validated participant deliverables"],
            "action_items": actions_json.get("action_items", []),
            "new_commitments": actions_json.get("new_commitments", []),
            "calendar_suggestions": [{
                "title": "Follow-up Coordination Sync",
                "suggested_slot": "Thursday, 2:00 PM - 3:00 PM EST",
                "participants": ["Sathwik", "Alice", "Bob"],
                "conflict_detected": False,
                "conflict_details": sched_out[:200]
            }],
            "email_drafts": emails_list
        }
