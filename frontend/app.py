"""Chief of Staff: Intelligent Meeting Coordinator & Summarizer Dashboard.

CittaAI RISE Problem Statement 2 (Level 4 Agentic Meeting Orchestrator)
Powered exclusively by Google Gemini 2.5 Flash and SQLite Memory.
"""

import os
import sys
from pathlib import Path

# Disable CrewAI telemetry completely to avoid thread signal registration issues in Streamlit
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["CREWAI_DISABLE_TRACKING"] = "true"

try:
    import crewai.telemetry.telemetry as _crewai_tm
    _crewai_tm.Telemetry._register_signal_handler = lambda *args, **kwargs: None
except Exception:
    pass

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import uuid
import json
import time
from datetime import datetime

import config
from database.db import (
    init_db,
    save_meeting_bundle,
    get_all_meetings,
    get_meeting_by_id,
    get_action_items,
    update_action_item_status,
    get_commitments,
    get_email_drafts,
    get_calendar_slots,
)
from audio.recorder import LiveAudioRecorder
from audio.transcriber import MeetingTranscriber
from agents.meeting_crew import ChiefOfStaffMeetingCrew
from memory.memory_manager import MemoryManager
from tools.email_tool import MailerTool
from frontend.styles import CUSTOM_CSS

# Page Configuration
st.set_page_config(
    page_title="AI Chief of Staff | Intelligent Meeting Coordinator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply Styling
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize Database
init_db()

# Seed initial demonstration data if database is empty
def seed_demo_memory_if_empty():
    meetings = get_all_meetings()
    if not meetings:
        seed_id = "seed-001"
        raw_tx = (
            "Speaker A (Sathwik): I will build the initial Streamlit UI mockups by Friday.\n"
            "Speaker B (Alice): Great, I'll take care of the database schema.\n"
            "Speaker C (Bob): I will review the API specifications."
        )
        save_meeting_bundle(
            meeting_id=seed_id,
            title="Initial Sprint Kickoff (Prior Meeting)",
            raw_transcript=raw_tx,
            labeled_transcript=raw_tx,
            summary="Kickoff sync where initial responsibilities were delegated across the team.",
            key_decisions=["Decided on Streamlit for UI", "Decided on SQLite for memory persistence"],
            action_items=[
                {"task": "Build initial Streamlit UI mockups", "owner": "Sathwik", "deadline": "Friday", "priority": "High"},
                {"task": "Prepare database schema", "owner": "Alice", "deadline": "Monday", "priority": "Medium"},
            ],
            email_drafts=[
                {"recipient_name": "Sathwik", "recipient_email": "sathwik@example.com", "subject": "Kickoff Action Items", "body": "Hi Sathwik, thanks for committing to complete the UI by Friday."}
            ],
            calendar_suggestions=[
                {"title": "Sprint Review", "suggested_slot": "Friday 4:00 PM EST", "participants": ["Sathwik", "Alice", "Bob"], "conflict_detected": False, "conflict_details": "No conflicts"}
            ],
            commitments=[
                {"person": "Sathwik", "commitment": "Complete UI mockups by Friday", "deadline": "Friday", "status": "Open"},
                {"person": "Alice", "commitment": "Draft database schema", "deadline": "Monday", "status": "Open"}
            ],
        )

seed_demo_memory_if_empty()

# Sidebar Navigation
with st.sidebar:
    st.markdown("<h2 class='cos-header'>AI Chief of Staff</h2>", unsafe_allow_html=True)
    st.caption("CittaAI RISE Hackathon | PS-2")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Meeting History",
            "Meeting Analysis",
            "Tasks & Action Items",
            "Follow-up Emails",
            "Meeting Memory",
        ],
        index=0,
    )

    st.markdown("---")
    st.markdown("**System Engine**")
    st.markdown("• **LLM**: Google Gemini 2.5 Flash")
    st.markdown("• **Agents**: CrewAI (5 Coordinated Agents)")
    st.markdown("• **STT**: Whisper Base")
    st.markdown("• **Diarization**: Pyannote Audio / Acoustic")
    st.markdown("• **Storage**: SQLite Persistent Memory")

    # API Status Indicator
    api_ready = bool(config.GEMINI_API_KEY)
    if api_ready:
        st.success("🟢 Gemini API Ready")
    else:
        st.warning("🟡 GEMINI_API_KEY Missing in .env")

# ==============================================================================
# 1. DASHBOARD (LIVE INGESTION & PIPELINE TRIGGER)
# ==============================================================================
if page == "Dashboard":
    st.markdown("<h1 class='cos-header'>Meeting Command Center</h1>", unsafe_allow_html=True)
    st.write("Autonomous lifecycle management: Live audio recording, transcription, speaker identification, and multi-agent coordination.")

    # High Level Metrics Row
    all_meetings = get_all_meetings()
    all_tasks = get_action_items()
    all_commitments = get_commitments()
    pending_tasks = [t for t in all_tasks if t.get("status") == "Pending"]

    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.metric("Total Meetings Managed", len(all_meetings))
    with mcol2:
        st.metric("Action Items Extracted", len(all_tasks))
    with mcol3:
        st.metric("Pending Deliverables", len(pending_tasks))
    with mcol4:
        st.metric("Cross-Meeting Commitments", len(all_commitments))

    st.markdown("---")

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("<div class='cos-surface'>", unsafe_allow_html=True)
        st.subheader("1. Ingestion: Live Audio, Upload, or Demo")
        input_source = st.radio(
            "Select Audio Input Method:",
            ["🎙️ Live Browser Audio (Render & Cloud Ready)", "📁 Upload Audio File (MP3, WAV, M4A, WEBM)", "🧪 Load Verified Demo Scenario"],
            horizontal=False,
        )

        audio_file_path = None

        if input_source == "🎙️ Live Browser Audio (Render & Cloud Ready)":
            st.markdown("""
            <div style="background: rgba(6, 182, 212, 0.1); border: 1px solid rgba(6, 182, 212, 0.3); border-radius: 10px; padding: 10px 14px; margin-bottom: 12px;">
                <span style="color: #22d3ee; font-weight: 700; font-size: 0.9rem;">🎧 Capturing Google Meet / Zoom in Another Tab or App:</span><br/>
                <span style="color: #cbd5e1; font-size: 0.83rem;">
                • <b>Laptop / Desktop</b>: Click the mic below to start recording. Switch to your Meet/Zoom tab or app. If on speakerphone, your microphone records both your voice and remote speakers!<br/>
                • <b>Auto-Save</b>: When you click stop, the recording is automatically saved and set as your active meeting.
                </span>
            </div>
            """, unsafe_allow_html=True)

            # Native Web Audio Input (Works in ANY browser on Render, mobile, or local)
            live_audio_blob = st.audio_input("🔴 Click to Start / Stop Live Audio Capture")
            if live_audio_blob:
                now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_name = f"meeting_{now_str}.wav"
                out_p = config.RECORDINGS_DIR / save_name
                with open(out_p, "wb") as f:
                    f.write(live_audio_blob.read())
                st.session_state.current_audio_file = str(out_p)
                st.session_state.default_meeting_title = f"Live Meeting - {datetime.now().strftime('%b %d, %I:%M %p')}"
                st.success(f"✅ Audio automatically captured & saved: `{save_name}`")

            if "current_audio_file" in st.session_state and st.session_state.current_audio_file:
                st.markdown("<p style='color:#34d399; font-weight:600; margin-top:8px;'>🎯 Current Active Recording:</p>", unsafe_allow_html=True)
                st.audio(st.session_state.current_audio_file)
                audio_file_path = Path(st.session_state.current_audio_file)

        elif input_source == "📁 Upload Audio File (MP3, WAV, M4A, WEBM)":
            uploaded_file = st.file_uploader("Drop any meeting recording:", type=["mp3", "wav", "m4a", "webm", "ogg"])
            if uploaded_file:
                save_dest = config.UPLOADS_DIR / uploaded_file.name
                with open(save_dest, "wb") as f:
                    f.write(uploaded_file.read())
                st.session_state.current_audio_file = str(save_dest)
                clean_title = Path(uploaded_file.name).stem.replace("_", " ").title()
                st.session_state.default_meeting_title = clean_title
                st.audio(str(save_dest))
                st.success(f"✅ Uploaded & set as active meeting: `{uploaded_file.name}`")
                audio_file_path = save_dest

        else:
            st.write("Instant Demonstration Transcript (Tests Cross-Meeting Memory & Speaker Separation):")
            sample_preset = st.selectbox(
                "Choose Demo Scenario:",
                [
                    "Scenario A: Sprint Review & UI Delivery Check (References Prior Sathwik Commitment)",
                    "Scenario B: Product Architecture & Security Escalation",
                ],
            )
            if sample_preset.startswith("Scenario A"):
                demo_text = (
                    "Speaker A (Sathwik): Good morning team. In our last meeting, I committed to completing the UI mockups by Friday. "
                    "I am happy to report that the Streamlit frontend with all six pages is fully ready.\n\n"
                    "Speaker B (Alice): That is great news Sathwik! For my part, I am finalizing the SQLite schema. I will deliver the "
                    "migration scripts and ORM models by next Monday at 5:00 PM EST.\n\n"
                    "Speaker C (Bob): Awesome. I will handle the Gemini 2.5 Flash API client integration and implement error fallbacks by Wednesday. "
                    "Let's schedule a follow-up coordination sync next Thursday at 2:00 PM EST to run an end-to-end rehearsal."
                )
            else:
                demo_text = (
                    "Speaker A (Chief Architect): We have decided to migrate all LLM calls exclusively to Google Gemini 2.5 Flash to ensure zero Anthropic dependencies.\n\n"
                    "Speaker B (SecOps Lead): Confirmed. I will revoke the unused third-party API keys by tomorrow afternoon.\n\n"
                    "Speaker C (DevOps Lead): I will configure the containerized environment and update the deployment manifest by Friday."
                )

            st.session_state.demo_text = demo_text
            st.text_area("Demo Transcript Preview", demo_text, height=140, disabled=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("<div class='cos-surface cos-surface-highlight'>", unsafe_allow_html=True)
        st.subheader("2. Autonomous Agent Execution")
        default_title = st.session_state.get("default_meeting_title", f"Meeting Strategy Sync - {datetime.now().strftime('%b %d')}")
        meeting_title = st.text_input("Meeting Subject / Title:", default_title)

        st.markdown("""
        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0 16px 0;">
            <span class="pipeline-step">🎙️ Gemini Native STT</span>
            <span class="pipeline-step">👥 Speaker Diarization</span>
            <span class="pipeline-step">🧠 Memory Cross-Check</span>
            <span class="pipeline-step">📋 Action Items</span>
            <span class="pipeline-step">📅 Scheduler</span>
            <span class="pipeline-step">✉️ Email Drafter</span>
        </div>
        """, unsafe_allow_html=True)

        # Check if an audio file is active
        if "current_audio_file" in st.session_state and st.session_state.current_audio_file:
            st.caption(f"Ready to process active recording: `{Path(st.session_state.current_audio_file).name}`")
            run_btn = st.button("⚡ Auto-Analyze Meeting (Run 5 Agents)", type="primary", use_container_width=True)
        else:
            run_btn = st.button("🚀 Run Chief of Staff Pipeline", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if run_btn:
            meeting_id = f"mtg_{uuid.uuid4().hex[:8]}"

            with st.status("🤖 Chief of Staff agents executing...", expanded=True) as status_box:
                # Step 1: Transcription & Diarization
                st.write("🎙️ **Step 1:** Speech-to-Text (Whisper) & Speaker Diarization (Pyannote)...")
                if audio_file_path and audio_file_path.exists():
                    transcriber = MeetingTranscriber()
                    raw_tx, labeled_tx, _ = transcriber.transcribe_and_diarize(audio_file_path)
                else:
                    labeled_tx = st.session_state.get(
                        "demo_text",
                        "Speaker A (Sathwik): I completed the UI mockups as promised last meeting. Speaker B (Alice): I will finish the database by Monday."
                    )
                    raw_tx = labeled_tx

                # Step 2: Memory Retrieval
                st.write("🧠 **Step 2:** Memory Agent querying past commitments from SQLite...")
                memory_mgr = MemoryManager()
                past_context = memory_mgr.get_past_context()

                # Step 3: Multi-Agent Execution
                st.write("⚡ **Step 3:** Executing CrewAI pipeline with Gemini 2.5 Flash...")
                crew = ChiefOfStaffMeetingCrew()
                agent_results = crew.run_pipeline(labeled_tx)

                # Step 4: Persistence
                st.write("💾 **Step 4:** Storing structured decisions, action items, and new commitments into SQLite...")
                save_meeting_bundle(
                    meeting_id=meeting_id,
                    title=meeting_title,
                    raw_transcript=raw_tx,
                    labeled_transcript=labeled_tx,
                    summary=agent_results.get("summary", "Meeting processed successfully."),
                    key_decisions=agent_results.get("key_decisions", ["All deliverables accepted"]),
                    action_items=agent_results.get("action_items", []),
                    email_drafts=agent_results.get("email_drafts", []),
                    calendar_suggestions=agent_results.get("calendar_suggestions", []),
                    commitments=agent_results.get("new_commitments", []),
                    audio_path=str(audio_file_path) if audio_file_path else None,
                )

                status_box.update(label="🎉 Chief of Staff Pipeline Finished Successfully!", state="complete", expanded=False)

            st.balloons()
            st.success(f"Meeting `{meeting_id}` processed and logged to permanent memory!")
            st.session_state.selected_meeting_id = meeting_id

            # Quick Results Preview
            with st.expander("👀 Instant Meeting Summary Preview", expanded=True):
                st.markdown(agent_results.get("summary", ""))
                st.markdown("#### Key Decisions")
                for d in agent_results.get("key_decisions", []):
                    st.markdown(f"- ✅ {d}")


# ==============================================================================
# 2. MEETING HISTORY
# ==============================================================================
elif page == "Meeting History":
    st.markdown("<h1 class='cos-header'>Meeting History & Archives</h1>", unsafe_allow_html=True)
    st.write("Review all processed meetings, view transcripts, and inspect executive summaries.")

    meetings = get_all_meetings()

    if not meetings:
        st.info("No meetings logged in database. Run a meeting from the Dashboard.")
    else:
        search_term = st.text_input("🔍 Search Meetings by Title or Content:", "")
        filtered = [
            m for m in meetings
            if search_term.lower() in m["title"].lower() or search_term.lower() in (m["summary"] or "").lower()
        ]

        st.write(f"Showing **{len(filtered)}** of {len(meetings)} meetings:")

        for m in filtered:
            with st.container():
                st.markdown(f"""
                <div class='cos-card'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <h3 style='margin:0; color:#818cf8;'>{m['title']}</h3>
                        <span style='color:#94a3b8; font-size:0.85rem;'>📅 {m['created_at']} | ID: <code>{m['id']}</code></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander(f"View Full Brief for '{m['title']}'"):
                    tab_sum, tab_tx, tab_dec = st.tabs(["Executive Summary", "Speaker-Labeled Transcript", "Decisions & Metadata"])
                    with tab_sum:
                        st.markdown(m["summary"] or "No summary recorded.")
                    with tab_tx:
                        st.text_area("Transcript", m["labeled_transcript"], height=250, disabled=True, key=f"tx_{m['id']}")
                    with tab_dec:
                        try:
                            decs = json.loads(m.get("key_decisions") or "[]")
                            for d in decs:
                                st.markdown(f"- 📌 {d}")
                        except Exception:
                            st.write(m.get("key_decisions", ""))
                st.write("")


# ==============================================================================
# 3. MEETING ANALYSIS
# ==============================================================================
elif page == "Meeting Analysis":
    st.markdown("<h1 class='cos-header'>Deep Meeting Intelligence & Diarization</h1>", unsafe_allow_html=True)
    st.write("Speaker breakdown, acoustic segmentation, and simulated calendar slot recommendations.")

    meetings = get_all_meetings()
    if not meetings:
        st.info("No meeting data available.")
    else:
        meeting_options = {f"{m['title']} ({m['id']})": m['id'] for m in meetings}
        selected_label = st.selectbox("Select Meeting to Inspect:", list(meeting_options.keys()))
        selected_id = meeting_options[selected_label]
        meeting_data = get_meeting_by_id(selected_id)

        col_a, col_b = st.columns([1, 1], gap="medium")

        with col_a:
            st.subheader("🗣️ Speaker-Diarized Conversation")
            st.caption("Pyannote Speaker Identification Output:")
            lines = (meeting_data["labeled_transcript"] or "").split("\n\n")
            for line in lines:
                if ":" in line:
                    spk, text = line.split(":", 1)
                    st.markdown(f"<span class='speaker-pill'>{spk.strip()}</span> {text.strip()}", unsafe_allow_html=True)
                else:
                    st.markdown(line)

        with col_b:
            st.subheader("📅 Simulated Calendar & Slot Resolution")
            cal_slots = get_calendar_slots(selected_id)

            if cal_slots:
                for slot in cal_slots:
                    conflict_badge = "⚠️ Conflict Handled" if slot["conflict_detected"] else "✅ Conflict-Free Slot"
                    st.markdown(f"""
                    <div class='cos-card'>
                        <div style='display: flex; justify-content: space-between;'>
                            <h4 style='margin:0;'>{slot['proposed_title']}</h4>
                            <span style='color: {'#f59e0b' if slot['conflict_detected'] else '#10b981'}; font-weight:bold;'>{conflict_badge}</span>
                        </div>
                        <p style='margin: 8px 0 4px 0;'><strong>Recommended Slot:</strong> {slot['suggested_slot']}</p>
                        <p style='margin: 0; color: #94a3b8; font-size: 0.85rem;'>{slot['conflict_details'] or 'Optimal slot based on simulated team availability.'}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No specific calendar follow-up sync registered for this meeting.")


# ==============================================================================
# 4. TASKS & ACTION ITEMS
# ==============================================================================
elif page == "Tasks & Action Items":
    st.markdown("<h1 class='cos-header'>Action Item & Deliverables Board</h1>", unsafe_allow_html=True)
    st.write("Strictly tracked tasks with explicit owners, target deadlines, and priority rankings.")

    items = get_action_items()

    if not items:
        st.info("No action items currently tracked. Process a meeting to extract tasks.")
    else:
        # Filter controls
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            status_filter = st.selectbox("Filter Status", ["All", "Pending", "In Progress", "Completed"])
        with f_col2:
            priority_filter = st.selectbox("Filter Priority", ["All", "High", "Medium", "Low"])

        filtered_items = [
            i for i in items
            if (status_filter == "All" or i["status"] == status_filter)
            and (priority_filter == "All" or i["priority"] == priority_filter)
        ]

        st.write(f"Showing **{len(filtered_items)}** action items:")

        for item in filtered_items:
            p_val = item["priority"].lower()
            badge_class = f"badge-{p_val[:3]}"

            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 1.5, 1.5])
            with c1:
                st.markdown(f"**{item['task']}**")
            with c2:
                st.markdown(f"👤 `{item['owner']}`")
            with c3:
                st.markdown(f"⏰ `{item['deadline']}`")
            with c4:
                st.markdown(f"<span class='{badge_class}'>{item['priority']}</span>", unsafe_allow_html=True)
            with c5:
                current_st = item["status"]
                next_st = "Completed" if current_st == "Pending" else "Pending"
                if st.button(f"{'✅ Mark Done' if current_st == 'Pending' else '↩️ Reopen'}", key=f"status_btn_{item['id']}"):
                    update_action_item_status(item["id"], next_st)
                    st.rerun()

            st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)


# ==============================================================================
# 5. FOLLOW-UP EMAILS
# ==============================================================================
elif page == "Follow-up Emails":
    st.markdown("<h1 class='cos-header'>Personalized Email Dispatcher</h1>", unsafe_allow_html=True)
    st.write("Personalized follow-up drafts generated for each participant. Review, edit, and dispatch.")

    drafts = get_email_drafts()

    if not drafts:
        st.info("No follow-up email drafts available. Process a meeting to generate drafts.")
    else:
        mailer = MailerTool()

        for d in drafts:
            with st.container():
                st.markdown(f"""
                <div class='cos-card'>
                    <h3 style='margin:0; color:#a855f7;'>To: {d['recipient_name']}</h3>
                    <p style='margin:4px 0; color:#cbd5e1;'><strong>Subject:</strong> {d['subject']}</p>
                </div>
                """, unsafe_allow_html=True)

                email_body = st.text_area("Email Content", d["body"], height=160, key=f"draft_{d['id']}")

                b_col1, b_col2 = st.columns([1, 4])
                with b_col1:
                    if st.button("📤 Send via SMTP", key=f"send_email_{d['id']}"):
                        target = d.get("recipient_email") or "participant@example.com"
                        result = mailer._run(
                            recipient_email=target,
                            subject=d["subject"],
                            body=email_body,
                        )
                        st.success(result)
                with b_col2:
                    st.caption(f"Email ID: {d['id']} | Origin Meeting ID: {d['meeting_id']}")
                st.write("")


# ==============================================================================
# 6. MEETING MEMORY (CROSS-MEETING INTELLIGENCE)
# ==============================================================================
elif page == "Meeting Memory":
    st.markdown("<h1 class='cos-header'>Cross-Meeting Memory & Commitments</h1>", unsafe_allow_html=True)
    st.write("The memory engine maintains institutional context across meetings, tracking pledges and verifying delivery.")

    # Memory Scenario Explanation Card
    st.info(
        "💡 **Cross-Meeting Memory Demonstration**:\n\n"
        "1. In **Meeting 1**, Sathwik committed: *'I will complete the UI mockups by Friday.'*\n"
        "2. In **Meeting 2**, the Memory Agent retrieves this commitment. When Sathwik speaks, "
        "the agent notes: *'Last meeting Sathwik committed to UI completion — verified delivered.'*\n"
        "3. New commitments made in Meeting 2 are added to the persistent ledger for Meeting 3."
    )

    commitments = get_commitments()

    col_mem_left, col_mem_right = st.columns([1.5, 1], gap="large")

    with col_mem_left:
        st.subheader("📋 Persistent Commitment Ledger (SQLite)")
        if not commitments:
            st.info("No commitments logged yet.")
        else:
            table_data = [
                {
                    "Person": c["person"],
                    "Commitment / Promise": c["commitment"],
                    "Target Deadline": c["deadline"],
                    "Status": c["status"],
                    "Origin Meeting": c.get("meeting_title", c["origin_meeting_id"]),
                }
                for c in commitments
            ]
            st.dataframe(table_data, use_container_width=True)

    with col_mem_right:
        st.subheader("🔍 Query Agent Memory")
        search_person = st.text_input("Participant Name or Keyword:", "Sathwik")
        if st.button("Audit Previous Commitments", type="secondary"):
            history_report = MemoryManager.get_past_context(search_person)
            st.markdown(history_report)
