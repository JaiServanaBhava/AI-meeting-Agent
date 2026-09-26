"""AI Chief of Staff — Beautiful, Modern Production Desktop Interface.

Includes:
  - Professional SaaS Sidebar with multi-view navigation (Live Studio, Archives, Tasks, Memory, Co-Pilot, Settings)
  - Seamless Light & Dark view toggle with smooth CSS variable transitions and persistent localStorage state
  - Real-time Audio VU volume visualizer with dynamic equalizer wave animation & microphone activity detection
  - Dedicated threaded Gemini Co-Pilot chat drawer for non-blocking Q&A on meeting transcripts & cross-meeting memory
  - Interactive Action Items checklist with live SQLite status toggling
  - 100% self-contained offline CSS & JS — zero external CDN dependencies
"""

DESKTOP_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Chief of Staff</title>
  <style>
    /* ── RESET & TOKENS ────────────────────────────────── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      /* Dark Theme (Default) */
      --bg-app:        #070c18;
      --bg-sidebar:    #0b1122;
      --bg-card:       rgba(15, 23, 42, 0.75);
      --bg-card-hover: rgba(30, 41, 59, 0.7);
      --bg-input:      #0e172a;
      --border:        rgba(255, 255, 255, 0.08);
      --border-focus:  #6366f1;
      --txt-main:      #f8fafc;
      --txt-sub:       #94a3b8;
      --txt-dim:       #64748b;
      --accent:        #6366f1;
      --accent-hover:  #4f46e5;
      --accent-cyan:   #06b6d4;
      --accent-green:  #10b981;
      --accent-amber:  #f59e0b;
      --accent-red:    #ef4444;
      --accent-blue:   #3b82f6;
      --glass-glow:    rgba(99, 102, 241, 0.25);
      --card-shadow:   0 8px 32px rgba(0, 0, 0, 0.45);
      --nav-active:    rgba(99, 102, 241, 0.16);
      --trans:         all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    body.light-theme {
      /* Light Theme */
      --bg-app:        #f1f5f9;
      --bg-sidebar:    #ffffff;
      --bg-card:       #ffffff;
      --bg-card-hover: #f8fafc;
      --bg-input:      #f1f5f9;
      --border:        rgba(0, 0, 0, 0.09);
      --border-focus:  #4f46e5;
      --txt-main:      #0f172a;
      --txt-sub:       #475569;
      --txt-dim:       #94a3b8;
      --accent:        #4f46e5;
      --accent-hover:  #4338ca;
      --accent-cyan:   #0891b2;
      --accent-green:  #059669;
      --accent-amber:  #d97706;
      --accent-red:    #dc2626;
      --accent-blue:   #2563eb;
      --glass-glow:    rgba(79, 70, 229, 0.12);
      --card-shadow:   0 4px 20px rgba(0, 0, 0, 0.07);
      --nav-active:    rgba(79, 70, 229, 0.1);
    }

    body {
      background: var(--bg-app);
      color: var(--txt-main);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      min-height: 100vh;
      display: flex;
      overflow: hidden;
      transition: background-color 0.3s ease, color 0.3s ease;
      -webkit-font-smoothing: antialiased;
    }

    /* ── LAYOUT ────────────────────────────────────────── */
    #app-container {
      display: flex;
      width: 100vw;
      height: 100vh;
      overflow: hidden;
    }

    /* ── SIDEBAR ───────────────────────────────────────── */
    aside.sidebar {
      width: 260px;
      min-width: 260px;
      background: var(--bg-sidebar);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      user-select: none;
      z-index: 10;
      transition: var(--trans);
    }

    .sidebar-header {
      padding: 18px 20px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .brand-icon {
      width: 38px;
      height: 38px;
      border-radius: 10px;
      background: linear-gradient(135deg, #6366f1, #3b82f6, #06b6d4);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.25rem;
      box-shadow: 0 4px 14px var(--glass-glow);
      flex-shrink: 0;
    }

    .brand-text h1 {
      font-size: 0.95rem;
      font-weight: 700;
      letter-spacing: -0.01em;
      color: var(--txt-main);
    }

    .brand-badge {
      display: inline-block;
      font-size: 0.62rem;
      padding: 2px 6px;
      border-radius: 6px;
      background: rgba(99, 102, 241, 0.15);
      color: var(--accent);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    /* Navigation Links */
    .nav-group {
      padding: 14px 12px;
      display: flex;
      flex-direction: column;
      gap: 5px;
      flex: 1;
      overflow-y: auto;
    }

    .nav-label {
      font-size: 0.68rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--txt-dim);
      font-weight: 700;
      margin: 10px 10px 4px 10px;
    }

    .nav-btn {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 14px;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--txt-sub);
      background: transparent;
      border: none;
      cursor: pointer;
      text-align: left;
      transition: var(--trans);
      position: relative;
    }

    .nav-btn:hover {
      color: var(--txt-main);
      background: rgba(125, 125, 125, 0.08);
    }

    .nav-btn.active {
      color: var(--accent);
      background: var(--nav-active);
      font-weight: 700;
    }

    .nav-btn.active::before {
      content: '';
      position: absolute;
      left: 0;
      top: 6px;
      bottom: 6px;
      width: 3.5px;
      background: var(--accent);
      border-radius: 0 4px 4px 0;
    }

    .nav-btn .icon {
      font-size: 1.15rem;
      width: 22px;
      display: flex;
      justify-content: center;
    }

    .nav-count {
      margin-left: auto;
      font-size: 0.72rem;
      background: var(--border);
      padding: 2px 7px;
      border-radius: 10px;
      color: var(--txt-sub);
    }

    /* Sidebar Footer: Audio Visualizer & Mode Switch */
    .sidebar-footer {
      padding: 14px 16px;
      border-top: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      gap: 12px;
      background: rgba(0, 0, 0, 0.04);
    }

    /* Real-time Audio Activity Card */
    .audio-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .audio-card-hdr {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.74rem;
      font-weight: 700;
      color: var(--txt-sub);
    }

    .audio-status-pill {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 0.7rem;
      color: var(--txt-dim);
    }

    .audio-status-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #94a3b8;
      transition: background-color 0.2s;
    }

    .audio-status-dot.active {
      background: var(--accent-green);
      box-shadow: 0 0 8px var(--accent-green);
      animation: pulse 1s infinite;
    }

    /* Equalizer Waveform Bars */
    .equalizer {
      display: flex;
      align-items: flex-end;
      height: 24px;
      gap: 4px;
      padding: 2px 0;
    }

    .eq-bar {
      flex: 1;
      background: rgba(99, 102, 241, 0.35);
      border-radius: 3px;
      height: 15%;
      min-height: 3px;
      transition: height 0.1s ease;
    }

    .eq-bar.active {
      background: linear-gradient(to top, var(--accent), var(--accent-cyan));
    }

    .audio-vol-num {
      font-size: 0.68rem;
      color: var(--txt-dim);
      font-family: ui-monospace, monospace;
      text-align: right;
    }

    /* Light/Dark Toggle Bar */
    .theme-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 0.8rem;
      color: var(--txt-sub);
      font-weight: 600;
      padding: 4px 2px;
    }

    .theme-switch {
      position: relative;
      width: 50px;
      height: 26px;
      border-radius: 13px;
      background: var(--bg-card);
      border: 1px solid var(--border);
      cursor: pointer;
      display: flex;
      align-items: center;
      padding: 3px;
      transition: var(--trans);
    }

    .theme-knob {
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: var(--accent);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.68rem;
      color: #fff;
      transform: translateX(0);
      transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    body.light-theme .theme-knob {
      transform: translateX(24px);
      background: #f59e0b;
    }

    /* ── MAIN CONTENT AREA ─────────────────────────────── */
    main.content-area {
      flex: 1;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
      background: var(--bg-app);
      position: relative;
    }

    /* Top Navigation / Action Bar */
    header.topbar {
      height: 60px;
      min-height: 60px;
      padding: 0 24px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: var(--bg-sidebar);
      z-index: 5;
    }

    .topbar-left {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .section-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--txt-main);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .radar-pill {
      display: flex;
      align-items: center;
      gap: 7px;
      background: rgba(16, 185, 129, 0.1);
      border: 1px solid rgba(16, 185, 129, 0.25);
      border-radius: 20px;
      padding: 4px 10px;
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--accent-green);
    }

    .radar-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--accent-green);
      box-shadow: 0 0 6px var(--accent-green);
      animation: pulse 1.8s infinite;
    }

    .topbar-right {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .clock-pill {
      font-family: ui-monospace, monospace;
      font-size: 0.8rem;
      color: var(--txt-sub);
      background: var(--bg-card);
      border: 1px solid var(--border);
      padding: 5px 10px;
      border-radius: 8px;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 7px 14px;
      border-radius: 8px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid var(--border);
      background: var(--bg-card);
      color: var(--txt-main);
      transition: var(--trans);
    }

    .btn:hover {
      background: var(--bg-card-hover);
      transform: translateY(-1px);
    }

    .btn:active {
      transform: translateY(0);
    }

    .btn-primary {
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
      box-shadow: 0 4px 12px var(--glass-glow);
    }

    .btn-primary:hover {
      background: var(--accent-hover);
    }

    .btn-danger {
      background: var(--accent-red);
      border-color: var(--accent-red);
      color: #fff;
    }

    .btn-danger:hover {
      background: #dc2626;
    }

    .btn-demo {
      background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(6,182,212,0.15));
      border: 1px solid rgba(99,102,241,0.3);
      color: var(--accent);
    }

    /* Auto-Detect switch */
    .switch-wrap {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--txt-sub);
    }

    .toggle-sw {
      position: relative;
      display: inline-block;
      width: 36px;
      height: 20px;
    }

    .toggle-sw input { opacity: 0; width: 0; height: 0; }

    .toggle-slider {
      position: absolute; cursor: pointer; inset: 0;
      background-color: #475569;
      border-radius: 20px;
      transition: .3s;
    }

    .toggle-slider:before {
      position: absolute; content: "";
      height: 14px; width: 14px; left: 3px; bottom: 3px;
      background-color: white;
      border-radius: 50%;
      transition: .3s;
    }

    input:checked + .toggle-slider { background-color: var(--accent-green); }
    input:checked + .toggle-slider:before { transform: translateX(16px); }

    /* ── PANELS CONTAINER ──────────────────────────────── */
    .panels-view {
      flex: 1;
      overflow-y: auto;
      padding: 22px 26px;
    }

    .panel {
      display: none;
      animation: fadeIn 0.25s ease-out forwards;
    }

    .panel.active {
      display: block;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    /* ── PANEL 1: LIVE STUDIO ──────────────────────────── */
    .radar-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px 20px;
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: var(--card-shadow);
      position: relative;
      overflow: hidden;
    }

    .radar-card::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0; height: 2px;
      background: linear-gradient(90deg, #6366f1, #06b6d4, #10b981);
    }

    .radar-card-left {
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .radar-icon-box {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: rgba(99, 102, 241, 0.12);
      border: 1px solid rgba(99, 102, 241, 0.25);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.4rem;
    }

    .radar-info h2 {
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--txt-main);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .radar-info p {
      font-size: 0.8rem;
      color: var(--txt-sub);
      margin-top: 2px;
    }

    /* Pipeline Step Pills */
    .pipeline-steps {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 20px;
    }

    .step-pill {
      display: flex;
      align-items: center;
      gap: 7px;
      padding: 7px 12px;
      border-radius: 20px;
      font-size: 0.74rem;
      font-weight: 600;
      background: var(--bg-card);
      border: 1px solid var(--border);
      color: var(--txt-dim);
      transition: var(--trans);
    }

    .step-pill.working {
      color: var(--accent);
      border-color: var(--accent);
      background: rgba(99, 102, 241, 0.1);
      animation: pulse 1.5s infinite;
    }

    .step-pill.done {
      color: var(--accent-green);
      border-color: rgba(16, 185, 129, 0.3);
      background: rgba(16, 185, 129, 0.08);
    }

    /* Meeting Report Container */
    .report-wrap {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      box-shadow: var(--card-shadow);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .report-header {
      padding: 16px 22px;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }

    .report-title-area h3 {
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--txt-main);
    }

    .report-date {
      font-size: 0.78rem;
      color: var(--txt-sub);
      margin-top: 3px;
    }

    .report-tabs {
      display: flex;
      gap: 6px;
      padding: 10px 20px;
      border-bottom: 1px solid var(--border);
      background: rgba(0, 0, 0, 0.02);
      overflow-x: auto;
    }

    .tab-btn {
      padding: 7px 14px;
      border-radius: 8px;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--txt-sub);
      background: transparent;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: var(--trans);
      white-space: nowrap;
    }

    .tab-btn:hover {
      color: var(--txt-main);
      background: rgba(125, 125, 125, 0.08);
    }

    .tab-btn.active {
      color: var(--accent);
      background: var(--nav-active);
      font-weight: 700;
    }

    .tab-panel {
      padding: 22px;
      display: none;
    }

    .tab-panel.active {
      display: block;
    }

    /* Card Elements Inside Tabs */
    .summary-box {
      font-size: 0.92rem;
      line-height: 1.65;
      color: var(--txt-main);
      background: rgba(0, 0, 0, 0.02);
      padding: 18px;
      border-radius: 10px;
      border: 1px solid var(--border);
      margin-bottom: 18px;
    }

    .section-subtitle {
      font-size: 0.88rem;
      font-weight: 700;
      color: var(--txt-main);
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .item-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .item-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 14px;
      background: rgba(0, 0, 0, 0.02);
      border: 1px solid var(--border);
      border-radius: 8px;
      transition: var(--trans);
    }

    .item-row:hover {
      background: var(--bg-card-hover);
    }

    .item-main {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .badge-pill {
      font-size: 0.7rem;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .badge-high { background: rgba(239, 68, 68, 0.15); color: var(--accent-red); }
    .badge-med  { background: rgba(245, 158, 11, 0.15); color: var(--accent-amber); }
    .badge-low  { background: rgba(100, 116, 139, 0.15); color: var(--txt-dim); }

    .transcript-box {
      width: 100%;
      height: 360px;
      padding: 14px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--bg-input);
      color: var(--txt-main);
      font-family: ui-monospace, monospace;
      font-size: 0.82rem;
      line-height: 1.6;
      resize: vertical;
      outline: none;
    }

    .email-drafts-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 14px;
    }

    .email-drafts-toolbar p {
      margin-top: 3px;
      color: var(--txt-sub);
      font-size: 0.78rem;
    }

    .email-draft-list {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .email-draft-card {
      padding: 16px;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: var(--bg-card);
    }

    .email-profile {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 12px;
    }

    .email-avatar {
      width: 38px;
      height: 38px;
      flex: 0 0 38px;
      display: grid;
      place-items: center;
      border-radius: 50%;
      color: white;
      background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
      font-size: 0.8rem;
      font-weight: 800;
    }

    .email-profile-name { font-size: 0.92rem; font-weight: 700; }
    .email-profile-label { display: block; margin-bottom: 5px; color: var(--txt-dim); font-size: 0.7rem; }

    .email-address-input, .email-subject-input {
      width: 100%;
      min-width: 0;
      padding: 9px 11px;
      border: 1px solid var(--border);
      border-radius: 7px;
      color: var(--txt-main);
      background: var(--bg-input);
      font: inherit;
      font-size: 0.82rem;
    }

    .email-address-input:focus, .email-subject-input:focus, .email-body-input:focus {
      outline: 2px solid var(--accent);
      outline-offset: 1px;
    }

    .email-promise-list {
      margin: 12px 0;
      padding: 11px 13px;
      border-left: 3px solid var(--accent-green);
      background: rgba(16, 185, 129, 0.07);
      color: var(--txt-sub);
      font-size: 0.8rem;
      line-height: 1.5;
    }

    .email-promise-list ul { margin: 6px 0 0 17px; }
    .email-promise-list li + li { margin-top: 3px; }

    .email-body-input {
      width: 100%;
      min-height: 145px;
      margin-top: 10px;
      padding: 12px;
      border: 1px solid var(--border);
      border-radius: 8px;
      resize: vertical;
      color: var(--txt-main);
      background: var(--bg-input);
      font: inherit;
      font-size: 0.82rem;
      line-height: 1.55;
    }

    .email-draft-actions { display: flex; justify-content: flex-end; margin-top: 10px; }

    @media (max-width: 680px) {
      .email-drafts-toolbar { align-items: flex-start; flex-direction: column; }
      .email-drafts-toolbar .btn { width: 100%; justify-content: center; }
    }

    /* ── PANEL 2: MEETING ARCHIVE ──────────────────────── */
    .archive-search-box {
      margin-bottom: 18px;
      display: flex;
      gap: 12px;
    }

    .search-input {
      flex: 1;
      padding: 10px 14px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--bg-card);
      color: var(--txt-main);
      font-size: 0.85rem;
      outline: none;
    }

    .search-input:focus { border-color: var(--accent); }

    .archive-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 14px;
    }

    .archive-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 12px;
      transition: var(--trans);
      cursor: pointer;
    }

    .archive-card:hover {
      border-color: var(--accent);
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
    }

    .archive-card-hdr {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }

    .archive-title {
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--txt-main);
    }

    .archive-date {
      font-size: 0.72rem;
      color: var(--txt-dim);
      margin-top: 3px;
    }

    .archive-snippet {
      font-size: 0.8rem;
      color: var(--txt-sub);
      line-height: 1.45;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .archive-card-ftr {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-top: 1px solid var(--border);
      padding-top: 10px;
    }

    /* ── PANEL 3: TASKS BOARD ──────────────────────────── */
    .task-stats-bar {
      display: flex;
      gap: 14px;
      margin-bottom: 20px;
    }

    .stat-pill-box {
      flex: 1;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px 16px;
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .stat-num {
      font-size: 1.5rem;
      font-weight: 800;
      color: var(--accent);
    }

    .stat-desc {
      font-size: 0.76rem;
      color: var(--txt-sub);
    }

    .task-interactive-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 10px;
      margin-bottom: 8px;
      transition: var(--trans);
    }

    .task-interactive-row.completed {
      opacity: 0.6;
      text-decoration: line-through;
    }

    .chk-box {
      width: 18px;
      height: 18px;
      border-radius: 4px;
      border: 2px solid var(--accent);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.75rem;
      color: #fff;
    }

    .chk-box.checked {
      background: var(--accent);
    }

    /* ── PANEL 5: GEMINI CO-PILOT (THREADED CHAT) ──────── */
    .copilot-container {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      height: calc(100vh - 110px);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .copilot-messages {
      flex: 1;
      padding: 20px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .chat-bubble {
      display: flex;
      gap: 12px;
      max-width: 80%;
      animation: fadeIn 0.2s ease;
    }

    .chat-bubble.user {
      margin-left: auto;
      flex-direction: row-reverse;
    }

    .chat-avatar {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      background: linear-gradient(135deg, #6366f1, #3b82f6);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1rem;
      flex-shrink: 0;
    }

    .chat-bubble.user .chat-avatar {
      background: #0ea5e9;
    }

    .chat-content {
      background: rgba(0, 0, 0, 0.04);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 16px;
      font-size: 0.88rem;
      line-height: 1.55;
      color: var(--txt-main);
    }

    .chat-bubble.user .chat-content {
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }

    .copilot-suggestions {
      padding: 10px 18px;
      display: flex;
      gap: 8px;
      overflow-x: auto;
      border-top: 1px solid var(--border);
      background: rgba(0, 0, 0, 0.02);
    }

    .sug-chip {
      font-size: 0.74rem;
      padding: 5px 10px;
      border-radius: 16px;
      background: var(--bg-card);
      border: 1px solid var(--border);
      color: var(--txt-sub);
      cursor: pointer;
      white-space: nowrap;
      transition: var(--trans);
    }

    .sug-chip:hover {
      border-color: var(--accent);
      color: var(--accent);
    }

    .copilot-input-bar {
      padding: 14px 18px;
      border-top: 1px solid var(--border);
      display: flex;
      gap: 10px;
      align-items: center;
    }

    .copilot-input {
      flex: 1;
      padding: 10px 14px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--bg-input);
      color: var(--txt-main);
      font-size: 0.88rem;
      outline: none;
    }

    .copilot-input:focus { border-color: var(--accent); }

    /* ── MODALS & TOAST ────────────────────────────────── */
    .modal-overlay {
      position: fixed; inset: 0;
      background: rgba(0, 0, 0, 0.65);
      backdrop-filter: blur(4px);
      z-index: 200;
      display: none;
      align-items: center;
      justify-content: center;
    }

    .modal-overlay.open { display: flex; }

    .modal-card {
      background: var(--bg-sidebar);
      border: 1px solid var(--border);
      border-radius: 14px;
      width: 480px;
      max-width: 90vw;
      padding: 24px;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .toast {
      position: fixed;
      bottom: 24px; right: 24px;
      background: var(--bg-sidebar);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px 18px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 0.84rem;
      font-weight: 600;
      z-index: 300;
      transform: translateY(80px);
      opacity: 0;
      transition: var(--trans);
    }

    .toast.on {
      transform: translateY(0);
      opacity: 1;
    }

    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.08); opacity: 0.7; }
    }
  </style>
</head>
<body>

<div id="app-container">
  <!-- ── SIDEBAR ── -->
  <aside class="sidebar">
    <div>
      <div class="sidebar-header">
        <div class="brand-icon">🎙️</div>
        <div class="brand-text">
          <h1>AI Chief of Staff</h1>
          <span class="brand-badge">Gemini 3.7 Pro</span>
        </div>
      </div>

      <nav class="nav-group">
        <span class="nav-label">Navigation</span>
        <button class="nav-btn active" data-nav="studio">
          <span class="icon">🎙️</span> Live Studio
        </button>
        <button class="nav-btn" data-nav="archive">
          <span class="icon">🗄️</span> Meeting Archive
          <span class="nav-count" id="badgeArchCount">0</span>
        </button>
        <button class="nav-btn" data-nav="tasks">
          <span class="icon">📋</span> Action Items
          <span class="nav-count" id="badgeTasksCount">0</span>
        </button>
        <button class="nav-btn" data-nav="commitments">
          <span class="icon">🧠</span> Cross-Memory
          <span class="nav-count" id="badgeCommitCount">0</span>
        </button>
        <button class="nav-btn" data-nav="copilot">
          <span class="icon">💬</span> Gemini Co-Pilot
        </button>

        <span class="nav-label" style="margin-top:14px;">System</span>
        <button class="nav-btn" data-nav="settings">
          <span class="icon">⚙️</span> API & Settings
        </button>
      </nav>
    </div>

    <!-- Sidebar Footer -->
    <div class="sidebar-footer">
      <!-- Real-Time Audio Level & Activity Meter -->
      <div class="audio-card">
        <div class="audio-card-hdr">
          <span>MICROPHONE INPUT</span>
          <span id="audioDbTxt" class="audio-vol-num">-60 dB</span>
        </div>
        <div class="equalizer" id="equalizerBars">
          <div class="eq-bar"></div>
          <div class="eq-bar"></div>
          <div class="eq-bar"></div>
          <div class="eq-bar"></div>
          <div class="eq-bar"></div>
          <div class="eq-bar"></div>
        </div>
        <div class="audio-status-pill">
          <div class="audio-status-dot" id="audioDot"></div>
          <span id="audioStatusTxt">Mic Standby</span>
        </div>
      </div>

      <!-- Light / Dark Theme Switch -->
      <div class="theme-bar">
        <span>Dark / Light Mode</span>
        <div class="theme-switch" id="themeSwitchBtn" title="Toggle Light/Dark Theme">
          <div class="theme-knob" id="themeKnob">🌙</div>
        </div>
      </div>
    </div>
  </aside>

  <!-- ── MAIN CONTENT ── -->
  <main class="content-area">
    <!-- Top Action Bar -->
    <header class="topbar">
      <div class="topbar-left">
        <div class="section-title" id="pageTitle">
          <span>🎙️</span> Live Meeting Studio
        </div>
        <div class="radar-pill">
          <div class="radar-dot"></div>
          <span id="radarStatusText">Radar Active: Monitoring Calls</span>
        </div>
        <div class="radar-pill" style="border-color: rgba(16, 185, 129, 0.4);">
          <span id="backendStatusBadge" style="color:var(--accent-green);font-weight:600;font-size:0.75rem;">⚡ Connected: SQLite & Gemini</span>
        </div>
      </div>

      <div class="topbar-right">
        <div class="clock-pill" id="digitalClock">--:--:-- --</div>
        <div class="switch-wrap">
          <span>Auto-Detect</span>
          <label class="toggle-sw">
            <input type="checkbox" id="autoDetectCheckbox" checked>
            <span class="toggle-slider"></span>
          </label>
        </div>
        <button class="btn btn-primary" id="btnRecordToggle">🎙️ Start Recording</button>
      </div>
    </header>

    <!-- Panels Container -->
    <div class="panels-view">
      
      <!-- ── PANEL 1: LIVE STUDIO ── -->
      <section class="panel active" id="panel-studio">
        <!-- Radar Active Meeting Bar -->
        <div class="radar-card">
          <div class="radar-card-left">
            <div class="radar-icon-box" id="mtgIcon">🎯</div>
            <div class="radar-info">
              <h2 id="mtgTitle">Ready for Your Next Meeting</h2>
              <p id="mtgSub">Monitoring Firefox, Chrome, Safari, Edge, and Zoom for active audio calls.</p>
            </div>
          </div>
          <button class="btn" id="btnManualAnalyze" style="display:none;">⏹️ End & Analyze</button>
        </div>

        <!-- 8 Pipeline Steps -->
        <div class="pipeline-steps">
          <div class="step-pill" id="step-rec">🎙️ Audio Stream</div>
          <div class="step-pill" id="step-stt">⚡ Gemini Transcription</div>
          <div class="step-pill" id="step-speakers">👥 Diarization</div>
          <div class="step-pill" id="step-memory">🧠 Cross-Memory</div>
          <div class="step-pill" id="step-summary">✍️ Summary</div>
          <div class="step-pill" id="step-tasks">📋 Action Items</div>
          <div class="step-pill" id="step-calendar">📅 Calendar Sync</div>
          <div class="step-pill" id="step-email">✉️ Follow-Up Draft</div>
        </div>

        <!-- Meeting Intelligence Report -->
        <div class="report-wrap">
          <div class="report-header">
            <div class="report-title-area">
              <h3 id="repTitle">Meeting Summary & Action Items</h3>
              <div class="report-date" id="repDate">Select a meeting or run a session to view analysis.</div>
            </div>
            <div style="display:flex;gap:8px;">
              <button class="btn" id="btnDownloadMd">📥 Download Report</button>
              <button class="btn" id="btnCopySummary">📋 Copy Summary</button>
            </div>
          </div>

          <!-- Report Tabs -->
          <div class="report-tabs">
            <button class="tab-btn active" data-tab="tab-summary">📊 Summary & Decisions</button>
            <button class="tab-btn" data-tab="tab-tasks">✅ Tasks (<span id="repTaskCount">0</span>)</button>
            <button class="tab-btn" data-tab="tab-promises">🤝 Commitments</button>
            <button class="tab-btn" data-tab="tab-calendar">📅 Follow-ups</button>
            <button class="tab-btn" data-tab="tab-email">✉️ Email Draft</button>
            <button class="tab-btn" data-tab="tab-transcript">📝 Transcript</button>
          </div>

          <!-- Tab Content -->
          <div class="tab-panel active" id="tab-summary">
            <div class="summary-box" id="repSummaryText">
              No meeting analyzed yet. Start speaking in Google Meet or click '✨ Instant Demo' above!
            </div>
            <div class="section-subtitle">📌 Key Decisions Made</div>
            <div class="item-list" id="repDecisionsList">
              <div style="color:var(--txt-dim);font-size:0.85rem;padding:8px;">Decisions will appear here.</div>
            </div>
          </div>

          <div class="tab-panel" id="tab-tasks">
            <div class="item-list" id="repTasksList">
              <div style="color:var(--txt-dim);font-size:0.85rem;padding:8px;">No action items detected yet.</div>
            </div>
          </div>

          <div class="tab-panel" id="tab-promises">
            <div class="item-list" id="repPromisesList">
              <div style="color:var(--txt-dim);font-size:0.85rem;padding:8px;">No cross-meeting commitments recorded.</div>
            </div>
          </div>

          <div class="tab-panel" id="tab-calendar">
            <div class="item-list" id="repCalendarList">
              <div style="color:var(--txt-dim);font-size:0.85rem;padding:8px;">No calendar sync suggestions.</div>
            </div>
          </div>

          <div class="tab-panel" id="tab-email">
            <div class="email-drafts-toolbar">
              <div>
                <div class="section-subtitle" style="margin-bottom:0;">Speaker Follow-Ups</div>
                <p>Personalized drafts with each speaker's recorded promises.</p>
              </div>
              <button class="btn btn-primary" id="btnEmailAllSpeakers">✉️ Open Team Email</button>
            </div>
            <div class="email-draft-list" id="emailDraftsList">
              <div style="color:var(--txt-dim);font-size:0.85rem;padding:8px;">Personalized drafts will appear here after meeting analysis.</div>
            </div>
          </div>

          <div class="tab-panel" id="tab-transcript">
            <textarea class="transcript-box" id="repTranscriptText" readonly placeholder="Raw & Diarized Transcript will appear here..."></textarea>
          </div>
        </div>
      </section>

      <!-- ── PANEL 2: MEETING ARCHIVE ── -->
      <section class="panel" id="panel-archive">
        <div class="archive-search-box">
          <input type="text" class="search-input" id="archiveSearchInput" placeholder="🔍 Search past meetings by title or keywords...">
          <button class="btn" id="btnRefreshArchive">🔄 Refresh</button>
        </div>
        <div class="archive-grid" id="archiveGrid">
          <!-- Populated dynamically via JS -->
        </div>
      </section>

      <!-- ── PANEL 3: ACTION ITEMS BOARD ── -->
      <section class="panel" id="panel-tasks">
        <div class="task-stats-bar">
          <div class="stat-pill-box">
            <div class="stat-num" id="statTotalTasks">0</div>
            <div class="stat-desc">Total Tracked<br>Deliverables</div>
          </div>
          <div class="stat-pill-box">
            <div class="stat-num" id="statPendingTasks" style="color:var(--accent-amber);">0</div>
            <div class="stat-desc">Pending<br>Action Items</div>
          </div>
          <div class="stat-pill-box">
            <div class="stat-num" id="statCompletedTasks" style="color:var(--accent-green);">0</div>
            <div class="stat-desc">Completed<br>Items</div>
          </div>
        </div>
        <div class="item-list" id="allTasksBoardList">
          <!-- Populated dynamically via JS -->
        </div>
      </section>

      <!-- ── PANEL 4: CROSS-MEETING COMMITMENTS ── -->
      <section class="panel" id="panel-commitments">
        <div class="summary-box" style="margin-bottom:16px;">
          🧠 <b>Cross-Meeting Memory:</b> Tracks commitments across multiple meetings. When someone says "As promised last week...", the system verifies fulfillment against previous commitments.
        </div>
        <div class="item-list" id="allCommitmentsList">
          <!-- Populated dynamically via JS -->
        </div>
      </section>

      <!-- ── PANEL 5: GEMINI CO-PILOT (THREADED CHAT) ── -->
      <section class="panel" id="panel-copilot">
        <div class="copilot-container">
          <div class="copilot-messages" id="chatMessages">
            <div class="chat-bubble">
              <div class="chat-avatar">🤖</div>
              <div class="chat-content">
                Hello! I am your <b>AI Chief of Staff</b> Co-Pilot. You can ask me anything about your recorded meetings, commitments, action items, or ask me to draft follow-up communications!
              </div>
            </div>
          </div>

          <!-- Prompt Suggestions -->
          <div class="copilot-suggestions">
            <div class="sug-chip" data-prompt="What are my top pending action items?">📋 Pending Tasks?</div>
            <div class="sug-chip" data-prompt="Summarize the key decisions made in the latest meeting.">📌 Latest Decisions?</div>
            <div class="sug-chip" data-prompt="What did Alice and Bob promise to deliver?">🤝 Team Promises?</div>
            <div class="sug-chip" data-prompt="Draft a polite follow-up email to the team regarding our deadlines.">✉️ Draft Follow-Up</div>
          </div>

          <!-- Input Bar -->
          <div class="copilot-input-bar">
            <input type="text" class="copilot-input" id="copilotInput" placeholder="Ask Gemini about your meetings... (Press Enter to send)">
            <button class="btn btn-primary" id="btnSendCopilot">Send 🚀</button>
          </div>
        </div>
      </section>

      <!-- ── PANEL 6: API & SETTINGS ── -->
      <section class="panel" id="panel-settings">
        <div class="modal-card" style="box-shadow:none;border:1px solid var(--border);width:100%;max-width:650px;">
          <h2 style="font-size:1.15rem;font-weight:700;">⚙️ Application Settings & Gemini API</h2>
          <p style="font-size:0.84rem;color:var(--txt-sub);">Configure your Google Gemini API key to activate cloud transcription and multi-agent synthesis.</p>
          
          <div style="display:flex;flex-direction:column;gap:6px;">
            <label style="font-size:0.8rem;font-weight:600;">Google Gemini API Key</label>
            <input type="password" class="search-input" id="apiKeySettingInput" placeholder="AIzaSy..." style="background:var(--bg-input);">
          </div>

          <div style="font-size:0.8rem;color:var(--txt-sub);background:rgba(0,0,0,0.02);padding:12px;border-radius:8px;border:1px solid var(--border);">
            • <b>Active Model:</b> Google Gemini 3.7 Flash with multi-model cascade (3.6-flash, 3.1-flash-lite)<br>
            • <b>Reports Directory:</b> <code>~/Desktop/ChiefOfStaff/Reports</code><br>
            • <b>Recordings Directory:</b> <code>~/Desktop/ChiefOfStaff/Recordings</code>
          </div>

          <button class="btn btn-primary" id="btnSaveApiKey" style="align-self:flex-start;">💾 Save & Activate API Key</button>

          <div style="border-top:1px solid var(--border);padding-top:16px;display:flex;flex-direction:column;align-items:flex-start;gap:8px;">
            <h3 style="font-size:0.95rem;font-weight:700;">Meeting Data</h3>
            <p style="font-size:0.82rem;color:var(--txt-sub);">Permanently delete all saved meetings, tasks, commitments, and follow-up data.</p>
            <button class="btn btn-danger" id="btnClearAllMeetings">🗑️ Clear All Meeting Data</button>
          </div>
        </div>
      </section>

    </div>
  </main>
</div>

<!-- Toast Notification -->
<div class="toast" id="toast">
  <span id="toastIcon">ℹ️</span>
  <span id="toastMsg">Notification message</span>
</div>

<script>
// ─── STATE & REFERENCES ───────────────────────────────────────────────────────
var state = {
  isRecording: false,
  activeNav: 'studio',
  lastBundle: null,
  allMeetings: [],
  audioInterval: null
};

// ─── THEME TOGGLE (LIGHT & DARK) ──────────────────────────────────────────────
function getSavedTheme() {
  try {
    return window.localStorage.getItem('cos_theme') || 'dark';
  } catch (e) {
    return 'dark';
  }
}

function saveTheme(theme) {
  try {
    window.localStorage.setItem('cos_theme', theme);
  } catch (e) {}
}

var savedTheme = getSavedTheme();
if (savedTheme === 'light') {
  document.body.classList.add('light-theme');
  document.getElementById('themeKnob').textContent = '☀️';
}

document.getElementById('themeSwitchBtn').addEventListener('click', function() {
  document.body.classList.toggle('light-theme');
  var isLight = document.body.classList.contains('light-theme');
  document.getElementById('themeKnob').textContent = isLight ? '☀️' : '🌙';
  saveTheme(isLight ? 'light' : 'dark');
  showToast(isLight ? '☀️' : '🌙', (isLight ? 'Light' : 'Dark') + ' theme enabled');
});

// ─── CLOCK ────────────────────────────────────────────────────────────────────
function updateClock() {
  var now = new Date();
  var s = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
  document.getElementById('digitalClock').textContent = s;
}
setInterval(updateClock, 1000);
updateClock();

// ─── SIDEBAR NAVIGATION ───────────────────────────────────────────────────────
var navButtons = document.querySelectorAll('.nav-btn');
var panels = {
  studio: document.getElementById('panel-studio'),
  archive: document.getElementById('panel-archive'),
  tasks: document.getElementById('panel-tasks'),
  commitments: document.getElementById('panel-commitments'),
  copilot: document.getElementById('panel-copilot'),
  settings: document.getElementById('panel-settings')
};

var pageTitles = {
  studio: '<span>🎙️</span> Live Meeting Studio',
  archive: '<span>🗄️</span> Meeting History & Archive',
  tasks: '<span>📋</span> Action Items & Deliverables',
  commitments: '<span>🧠</span> Cross-Meeting Commitments',
  copilot: '<span>💬</span> Gemini Co-Pilot Assistant',
  settings: '<span>⚙️</span> API Key & Settings'
};

navButtons.forEach(function(btn) {
  btn.addEventListener('click', function() {
    var target = btn.getAttribute('data-nav');
    if (!target || !panels[target]) return;

    navButtons.forEach(function(b) { b.classList.remove('active'); });
    btn.classList.add('active');

    Object.keys(panels).forEach(function(k) { panels[k].classList.remove('active'); });
    panels[target].classList.add('active');

    document.getElementById('pageTitle').innerHTML = pageTitles[target] || 'AI Chief of Staff';
    state.activeNav = target;

    // Load data when opening specific views
    if (target === 'archive') refreshArchive();
    if (target === 'tasks') refreshTasks();
    if (target === 'commitments') refreshCommitments();
  });
});

// ─── REPORT TABS ──────────────────────────────────────────────────────────────
var tabButtons = document.querySelectorAll('.tab-btn');
tabButtons.forEach(function(tb) {
  tb.addEventListener('click', function() {
    tabButtons.forEach(function(b) { b.classList.remove('active'); });
    tb.classList.add('active');

    var targetId = tb.getAttribute('data-tab');
    document.querySelectorAll('.tab-panel').forEach(function(p) { p.classList.remove('active'); });
    var targetPanel = document.getElementById(targetId);
    if (targetPanel) targetPanel.classList.add('active');
  });
});

// ─── REAL-TIME AUDIO VU METER & ACTIVITY MONITOR ─────────────────────────────
var eqBars = document.querySelectorAll('.eq-bar');

function pollAudioStatus() {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.get_audio_status) {
    window.pywebview.api.get_audio_status().then(function(res) {
      if (!res) return;
      var vol = res.volume_percent || 0;
      var db = res.peak_db !== undefined ? res.peak_db : -60;
      var isActive = res.is_active || (vol > 2.5);
      var isRec = res.is_recording || false;

      // Update text
      document.getElementById('audioDbTxt').textContent = (db > -60 ? Math.round(db) + ' dB' : '-60 dB');
      
      var dot = document.getElementById('audioDot');
      var statusTxt = document.getElementById('audioStatusTxt');

      if (isRec) {
        dot.className = 'audio-status-dot active';
        statusTxt.textContent = 'Recording (' + formatSec(res.duration_seconds || 0) + ')';
        statusTxt.style.color = 'var(--accent-red)';
      } else if (isActive) {
        dot.className = 'audio-status-dot active';
        statusTxt.textContent = 'Audio Active (' + Math.round(vol) + '%)';
        statusTxt.style.color = 'var(--accent-green)';
      } else {
        dot.className = 'audio-status-dot';
        statusTxt.textContent = 'Mic Standby';
        statusTxt.style.color = 'var(--txt-dim)';
      }

      // Equalizer bars animation
      eqBars.forEach(function(bar, idx) {
        if (isActive || isRec) {
          bar.classList.add('active');
          var randomFactor = 0.6 + Math.random() * 0.7;
          var heightPct = Math.min(100, Math.max(10, vol * randomFactor));
          bar.style.height = heightPct + '%';
        } else {
          bar.classList.remove('active');
          bar.style.height = '12%';
        }
      });
    }).catch(function(){});
  }
}
setInterval(pollAudioStatus, 150);

function formatSec(s) {
  var m = Math.floor(s / 60);
  var sec = s % 60;
  return (m < 10 ? '0' : '') + m + ':' + (sec < 10 ? '0' : '') + sec;
}

// ─── RECORDING CONTROLS ───────────────────────────────────────────────────────
var btnRecord = document.getElementById('btnRecordToggle');
var btnManualAnalyze = document.getElementById('btnManualAnalyze');

btnRecord.addEventListener('click', function() {
  if (!state.isRecording) {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.start_manual_recording();
    }
  } else {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.stop_and_analyze();
    }
  }
});

btnManualAnalyze.addEventListener('click', function() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.stop_and_analyze();
  }
});

document.getElementById('autoDetectCheckbox').addEventListener('change', function(e) {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.set_auto_detect(e.target.checked);
    showToast('📡', e.target.checked ? 'Auto-detection enabled' : 'Auto-detection paused');
  }
});

// ─── GEMINI CO-PILOT CHAT ─────────────────────────────────────────────────────
var chatInput = document.getElementById('copilotInput');
var btnSend = document.getElementById('btnSendCopilot');
var chatContainer = document.getElementById('chatMessages');

function sendCopilotMessage(text) {
  var q = (text || chatInput.value || '').trim();
  if (!q) return;

  // Add user bubble
  appendChatBubble('user', '👤', esc(q));
  chatInput.value = '';

  // Add thinking placeholder
  var thinkId = 'think_' + Date.now();
  appendChatBubble('bot', '🤖', '<i>Thinking with Gemini 3.7 Flash...</i>', thinkId);

  // Call threaded Python API
  if (window.pywebview && window.pywebview.api && window.pywebview.api.ask_gemini_threaded) {
    window.pywebview.api.ask_gemini_threaded(q, state.lastBundle ? state.lastBundle.meeting_id : null);
  }
}

btnSend.addEventListener('click', function() { sendCopilotMessage(); });
chatInput.addEventListener('keydown', function(e) { if (e.key === 'Enter') sendCopilotMessage(); });

document.querySelectorAll('.sug-chip').forEach(function(chip) {
  chip.addEventListener('click', function() {
    var p = chip.getAttribute('data-prompt');
    if (p) sendCopilotMessage(p);
  });
});

function appendChatBubble(role, avatar, htmlContent, elemId) {
  var b = document.createElement('div');
  b.className = 'chat-bubble ' + role;
  if (elemId) b.id = elemId;
  b.innerHTML = '<div class="chat-avatar">' + avatar + '</div><div class="chat-content">' + htmlContent + '</div>';
  chatContainer.appendChild(b);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

window.receiveGeminiChatResponse = function(payload) {
  // Remove thinking bubble if present
  var thinking = document.querySelector('[id^="think_"]');
  if (thinking) thinking.remove();

  if (payload.ok) {
    appendChatBubble('bot', '🤖', formatMarkdown(payload.answer));
  } else {
    appendChatBubble('bot', '⚠️', 'Error querying Gemini: ' + esc(payload.error));
  }
};

function formatMarkdown(text) {
  if (!text) return '';
  var s = esc(text);
  // bold
  s = s.replace(/\\*\\*(.*?)\\*\\*/g, '<b>$1</b>');
  // bullet items
  s = s.replace(/^[\\*\\-]\\s+(.+)$/gm, '• $1');
  // line breaks
  s = s.replace(/\\n/g, '<br>');
  return s;
}

// ─── ARCHIVE / HISTORY ───────────────────────────────────────────────────────
var allArchiveMeetings = [];

function refreshArchive() {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.get_meeting_history) {
    window.pywebview.api.get_meeting_history().then(function(meetings) {
      allArchiveMeetings = meetings || [];
      renderArchiveGrid(allArchiveMeetings);
    }).catch(function(err) {
      console.error('Error getting meeting history:', err);
    });
  }
}

function renderArchiveGrid(meetings) {
  var grid = document.getElementById('archiveGrid');
  if (!grid) return;
  grid.innerHTML = '';

  var badge = document.getElementById('badgeArchCount');
  if (badge) badge.textContent = meetings ? meetings.length : 0;

  if (!meetings || !meetings.length) {
    grid.innerHTML = '<div style="color:var(--txt-dim);padding:24px;grid-column:1/-1;text-align:center;">No past meetings found in SQLite archive.<br><small style="margin-top:6px;display:block;">Record or simulate a meeting in Live Studio to build history.</small></div>';
    return;
  }

  meetings.forEach(function(m) {
    var card = document.createElement('div');
    card.className = 'archive-card';
    card.onclick = function() { window.loadPastMeeting(m.id); };

    var title = m.title || 'Untitled Meeting';
    var dateStr = m.created_at ? new Date(m.created_at).toLocaleString() : 'Past session';
    var durMin = m.duration_seconds ? Math.round(m.duration_seconds / 60) + ' min' : 'Recorded';
    var summaryTxt = m.summary || m.raw_transcript || 'No summary available.';

    card.innerHTML = 
      '<div>' +
        '<div class="archive-card-hdr">' +
          '<div>' +
            '<div class="archive-title">🎙️ ' + esc(title) + '</div>' +
            '<div class="archive-date">📅 ' + esc(dateStr) + '</div>' +
          '</div>' +
          '<span class="badge-pill badge-med">' + durMin + '</span>' +
        '</div>' +
        '<div class="archive-snippet" style="margin-top:10px;">' + esc(summaryTxt) + '</div>' +
      '</div>' +
      '<div class="archive-card-ftr">' +
        '<span style="font-size:0.75rem;color:var(--accent);font-weight:600;">📂 Click to load report</span>' +
        '<span style="font-size:0.72rem;color:var(--txt-dim);">ID: ' + esc(String(m.id).slice(0, 8)) + '...</span>' +
      '</div>';

    grid.appendChild(card);
  });
}

// Archive search and refresh listeners
var archSearch = document.getElementById('archiveSearchInput');
if (archSearch) {
  archSearch.addEventListener('input', function() {
    var q = this.value.toLowerCase().trim();
    if (!q) {
      renderArchiveGrid(allArchiveMeetings);
      return;
    }
    var filtered = allArchiveMeetings.filter(function(m) {
      return (m.title && m.title.toLowerCase().indexOf(q) !== -1) ||
             (m.summary && m.summary.toLowerCase().indexOf(q) !== -1) ||
             (m.raw_transcript && m.raw_transcript.toLowerCase().indexOf(q) !== -1);
    });
    renderArchiveGrid(filtered);
  });
}

var btnRefArch = document.getElementById('btnRefreshArchive');
if (btnRefArch) {
  btnRefArch.addEventListener('click', function() {
    refreshArchive();
  });
}

window.loadPastMeeting = function(id) {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.load_meeting) {
    window.pywebview.api.load_meeting(id).then(function(res) {
      if (res && res.ok && res.bundle) {
        window.renderResults(res.bundle);
        var studioBtn = document.querySelector('[data-nav="studio"]');
        if (studioBtn) studioBtn.click();
        showToast('📂', 'Loaded report: ' + (res.bundle.title || id));
      } else {
        showToast('⚠️', 'Could not load meeting details.');
      }
    }).catch(function(e) {
      showToast('❌', 'Error loading meeting: ' + e);
    });
  }
};

// ─── ACTION ITEMS BOARD ───────────────────────────────────────────────────────
function refreshTasks() {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.get_action_items_board) {
    window.pywebview.api.get_action_items_board().then(function(tasks) {
      renderTasksBoard(tasks || []);
    });
  }
}

function renderTasksBoard(tasks) {
  var container = document.getElementById('allTasksBoardList');
  if (!container) return;
  container.innerHTML = '';

  var completed = 0;
  (tasks || []).forEach(function(t) { if (t.status === 'Completed') completed++; });
  var total = (tasks || []).length;
  var pending = total - completed;

  var elTot = document.getElementById('statTotalTasks');
  if (elTot) elTot.textContent = total;
  var elComp = document.getElementById('statCompletedTasks');
  if (elComp) elComp.textContent = completed;
  var elPend = document.getElementById('statPendingTasks');
  if (elPend) elPend.textContent = pending;
  var badgeTasks = document.getElementById('badgeTasksCount');
  if (badgeTasks) badgeTasks.textContent = pending;

  if (!total) {
    container.innerHTML = '<div style="color:var(--txt-dim);padding:24px;text-align:center;">No action items tracked in memory yet.</div>';
    return;
  }

  tasks.forEach(function(t) {
    var isDone = (t.status === 'Completed');
    var p = (t.priority || 'Medium').toLowerCase();
    var pClass = p === 'high' ? 'badge-high' : p === 'low' ? 'badge-low' : 'badge-med';

    var row = document.createElement('div');
    row.className = 'task-interactive-row ' + (isDone ? 'completed' : '');

    var itemMain = document.createElement('div');
    itemMain.className = 'item-main';

    var chk = document.createElement('div');
    chk.className = 'chk-box ' + (isDone ? 'checked' : '');
    chk.textContent = isDone ? '✓' : '';
    (function(taskId, taskStatus) {
      chk.addEventListener('click', function(e) {
        e.stopPropagation();
        window.toggleTask(taskId, taskStatus);
      });
    })(t.id, t.status);

    var textDiv = document.createElement('div');
    textDiv.innerHTML = 
      '<div style="font-size:0.88rem;font-weight:600;color:var(--txt-main);' + (isDone ? 'text-decoration:line-through;opacity:0.7;' : '') + '">' + esc(t.task) + '</div>' +
      '<div style="font-size:0.72rem;color:var(--txt-dim);margin-top:2px;">👤 ' + esc(t.owner) + ' &nbsp;|&nbsp; ⏰ ' + esc(t.deadline || 'TBD') + '</div>';

    itemMain.appendChild(chk);
    itemMain.appendChild(textDiv);

    var badgeSpan = document.createElement('span');
    badgeSpan.className = 'badge-pill ' + pClass;
    badgeSpan.textContent = esc(t.priority || 'Medium');

    row.appendChild(itemMain);
    row.appendChild(badgeSpan);
    container.appendChild(row);
  });
}

window.toggleTask = function(id, currStatus) {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.toggle_action_item_status) {
    window.pywebview.api.toggle_action_item_status(id, currStatus).then(function(res) {
      if (res && res.ok) {
        renderTasksBoard(res.items || []);
        showToast('✓', 'Action item marked ' + res.new_status);
      }
    });
  }
};

// ─── COMMITMENTS BOARD ────────────────────────────────────────────────────────
function refreshCommitments() {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.get_commitments_board) {
    window.pywebview.api.get_commitments_board().then(function(list) {
      renderCommitmentsBoard(list || []);
    });
  }
}

function renderCommitmentsBoard(list) {
  var container = document.getElementById('allCommitmentsList');
  if (!container) return;
  container.innerHTML = '';
  var badgeCom = document.getElementById('badgeCommitCount');
  if (badgeCom) badgeCom.textContent = (list || []).length;
  if (!list || !list.length) {
    container.innerHTML = '<div style="color:var(--txt-dim);padding:24px;text-align:center;">No commitments tracked yet across meetings.</div>';
    return;
  }
  list.forEach(function(c) {
    var row = document.createElement('div');
    row.className = 'item-row';
    row.innerHTML = 
      '<div>' +
        '<div style="font-size:0.88rem;font-weight:600;color:var(--txt-main);">' + esc(c.commitment) + '</div>' +
        '<div style="font-size:0.74rem;color:var(--txt-dim);margin-top:2px;">👤 <b>' + esc(c.person) + '</b> &nbsp;|&nbsp; 📅 Due: ' + esc(c.deadline || 'TBD') + ' &nbsp;|&nbsp; 🏛️ ' + esc(c.meeting_title || 'Meeting') + '</div>' +
      '</div>' +
      '<span class="badge-pill badge-med">' + esc(c.status || 'Open') + '</span>';
    container.appendChild(row);
  });
}

function normalizeRecipientName(value) {
  var name = String(value || '').trim();
  if (name.indexOf('/') !== -1) name = name.split('/').pop().trim();
  return name || 'Participant';
}

function sameRecipient(left, right) {
  var a = normalizeRecipientName(left).toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  var b = normalizeRecipientName(right).toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  return a === b || a.indexOf(b + ' ') === 0 || b.indexOf(a + ' ') === 0 ||
    (' ' + a + ' ').indexOf(' ' + b + ' ') !== -1 || (' ' + b + ' ').indexOf(' ' + a + ' ') !== -1;
}

function isPlaceholderEmail(value) {
  var email = String(value || '').trim();
  var at = email.indexOf('@');
  if (!email || email.indexOf(' ') !== -1 || email.indexOf(',') !== -1 || email.indexOf(';') !== -1 ||
      at < 1 || at !== email.lastIndexOf('@') || email.indexOf('.', at) < at + 2 || email.indexOf('.', at) === email.length - 1) return true;
  return ['example.com', 'example.org', 'example.net'].indexOf(email.slice(at + 1).toLowerCase()) !== -1;
}

function promisesForRecipient(bundle, recipient) {
  var promises = [];
  (bundle.action_items || []).forEach(function(item) {
    if (item.owner && sameRecipient(item.owner, recipient)) {
      promises.push('Action: ' + (item.task || 'Follow up') + ' (due ' + (item.deadline || 'TBD') + ')');
    }
  });
  (bundle.commitments || []).forEach(function(item) {
    if (item.person && sameRecipient(item.person, recipient)) {
      promises.push('Promise: ' + (item.commitment || 'Follow up') + ' (due ' + (item.deadline || 'TBD') + ')');
    }
  });
  return promises.filter(function(value, index) { return promises.indexOf(value) === index; });
}

function makeEmailDraft(bundle, profile) {
  var promises = promisesForRecipient(bundle, profile.name);
  var subject = profile.draft.subject || ('Meeting follow-up: ' + (bundle.title || 'Next steps'));
  var body = String(profile.draft.body || '').trim();
  var missingPromises = promises.filter(function(promise) {
    return body.toLowerCase().indexOf(promise.toLowerCase()) === -1;
  });
  var newline = String.fromCharCode(10);
  if (!body) body = 'Hi ' + profile.name + ',' + newline + newline + 'Thank you for the meeting.';
  if (missingPromises.length) {
    body += newline + newline + 'Your recorded follow-ups:' + newline + missingPromises.map(function(promise) { return '- ' + promise; }).join(newline);
  }

  return { name: profile.name, email: profile.draft.recipient_email || '', subject: subject, body: body, promises: promises };
}

function renderEmailDrafts(bundle) {
  var container = document.getElementById('emailDraftsList');
  var teamButton = document.getElementById('btnEmailAllSpeakers');
  if (!container || !teamButton) return;
  container.innerHTML = '';

  var drafts = bundle.email_drafts || [];
  var names = [];
  function addName(value) {
    var name = normalizeRecipientName(value);
    var key = name.toLowerCase();
    if (!name || ['team', 'everyone', 'participants', 'unknown', 'unassigned', 'you'].indexOf(key) !== -1) return;
    if (!names.some(function(existing) { return sameRecipient(existing, name); })) names.push(name);
  }
  drafts.forEach(function(draft) { addName(draft.recipient_name); });
  String(bundle.labeled_transcript || bundle.raw_transcript || '').split(String.fromCharCode(10)).forEach(function(line) {
    var separator = line.indexOf(':');
    if (separator < 1) return;
    var label = line.slice(0, separator).trim();
    if (label.toLowerCase().indexOf('speaker') !== 0) return;
    var openParen = label.indexOf('(');
    var closeParen = label.indexOf(')', openParen + 1);
    addName(openParen !== -1 && closeParen > openParen ? label.slice(openParen + 1, closeParen) : label);
  });
  (bundle.action_items || []).forEach(function(item) { addName(item.owner); });
  (bundle.commitments || []).forEach(function(item) { addName(item.person); });

  var profiles = names.map(function(name) {
    var matchingDraft = drafts.find(function(draft) { return sameRecipient(draft.recipient_name, name); }) || {};
    var profile = makeEmailDraft(bundle, { name: name, draft: matchingDraft });
    if (isPlaceholderEmail(profile.email)) profile.email = '';
    return profile;
  });

  if (!profiles.length && drafts.length) {
    profiles = drafts.map(function(draft) {
      var profile = makeEmailDraft(bundle, { name: normalizeRecipientName(draft.recipient_name), draft: draft });
      if (isPlaceholderEmail(profile.email)) profile.email = '';
      return profile;
    });
  }

  if (!profiles.length) {
    container.innerHTML = '<div style="color:var(--txt-dim);font-size:0.85rem;padding:8px;">No speaker drafts or assigned promises were found.</div>';
    teamButton.disabled = true;
    return;
  }

  teamButton.disabled = false;
  profiles.forEach(function(profile) {
    var card = document.createElement('article');
    card.className = 'email-draft-card';
    card.dataset.recipientName = profile.name;

    var header = document.createElement('div');
    header.className = 'email-profile';
    var avatar = document.createElement('div');
    avatar.className = 'email-avatar';
    avatar.textContent = profile.name.split(' ').filter(Boolean).slice(0, 2).map(function(part) { return part.charAt(0); }).join('').toUpperCase();
    var identity = document.createElement('div');
    identity.className = 'email-profile-name';
    identity.textContent = profile.name;
    header.appendChild(avatar);
    header.appendChild(identity);
    card.appendChild(header);

    var emailLabel = document.createElement('label');
    emailLabel.className = 'email-profile-label';
    emailLabel.textContent = 'Email address';
    var emailInput = document.createElement('input');
    emailInput.className = 'email-address-input';
    emailInput.type = 'email';
    emailInput.autocomplete = 'email';
    emailInput.placeholder = 'Add a real email address';
    emailInput.value = profile.email;
    emailLabel.appendChild(emailInput);
    card.appendChild(emailLabel);

    var promiseBox = document.createElement('div');
    promiseBox.className = 'email-promise-list';
    var promiseTitle = document.createElement('strong');
    promiseTitle.textContent = 'Recorded promises and actions';
    promiseBox.appendChild(promiseTitle);
    if (profile.promises.length) {
      var promiseList = document.createElement('ul');
      profile.promises.forEach(function(promise) {
        var item = document.createElement('li');
        item.textContent = promise;
        promiseList.appendChild(item);
      });
      promiseBox.appendChild(promiseList);
    } else {
      var none = document.createElement('div');
      none.textContent = 'No individual promise was extracted.';
      promiseBox.appendChild(none);
    }
    card.appendChild(promiseBox);

    var subject = document.createElement('input');
    subject.className = 'email-subject-input';
    subject.type = 'text';
    subject.value = profile.subject;
    subject.setAttribute('aria-label', 'Email subject for ' + profile.name);
    card.appendChild(subject);

    var body = document.createElement('textarea');
    body.className = 'email-body-input';
    body.value = profile.body;
    body.setAttribute('aria-label', 'Email body for ' + profile.name);
    card.appendChild(body);

    var actions = document.createElement('div');
    actions.className = 'email-draft-actions';
    var openButton = document.createElement('button');
    openButton.className = 'btn btn-primary btn-open-personal-email';
    openButton.textContent = '✉️ Open in Mail';
    actions.appendChild(openButton);
    card.appendChild(actions);
    container.appendChild(card);
  });
}

function openEmailInDefaultApp(recipients, subject, body) {
  if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.open_email_draft) {
    showToast('⚠️', 'Default email service is unavailable');
    return;
  }
  window.pywebview.api.open_email_draft(recipients, subject, body).then(function(result) {
    if (result && result.ok) showToast('✉️', 'Draft opened in your default email app');
    else showToast('⚠️', (result && result.error) || 'Could not open email draft');
  }).catch(function(error) {
    showToast('❌', 'Could not open email draft: ' + error);
  });
}

document.getElementById('emailDraftsList').addEventListener('click', function(event) {
  var button = event.target.closest('.btn-open-personal-email');
  if (!button) return;
  var card = button.closest('.email-draft-card');
  var address = card.querySelector('.email-address-input').value.trim();
  if (isPlaceholderEmail(address)) {
    showToast('⚠️', 'Enter a real email address for ' + card.dataset.recipientName);
    return;
  }
  openEmailInDefaultApp(
    [address],
    card.querySelector('.email-subject-input').value,
    card.querySelector('.email-body-input').value
  );
});

document.getElementById('btnEmailAllSpeakers').addEventListener('click', function() {
  var cards = Array.prototype.slice.call(document.querySelectorAll('.email-draft-card'));
  if (!cards.length) return;
  var addresses = cards.map(function(card) { return card.querySelector('.email-address-input').value.trim(); });
  if (addresses.some(isPlaceholderEmail)) {
    showToast('⚠️', 'Add a real email address for every speaker first');
    return;
  }

  var bundle = state.lastBundle || {};
  var newline = String.fromCharCode(10);
  var sections = cards.map(function(card) {
    var name = card.dataset.recipientName;
    var promises = promisesForRecipient(bundle, name);
    return name + ':' + newline + (promises.length ? promises.map(function(promise) { return '- ' + promise; }).join(newline) : '- No individual promise was extracted.');
  });
  var body = 'Hello everyone,' + newline + newline + 'Here are the follow-ups from ' + (bundle.title || 'our meeting') + ':' + newline + newline + sections.join(newline + newline) + newline + newline + 'Please reply to confirm your next steps.';
  openEmailInDefaultApp(addresses.filter(function(address, index) { return addresses.indexOf(address) === index; }), 'Meeting follow-up: ' + (bundle.title || 'Next steps'), body);
});

// ─── API SETTINGS ─────────────────────────────────────────────────────────────
document.getElementById('btnSaveApiKey').addEventListener('click', function() {
  var key = document.getElementById('apiKeySettingInput').value.trim();
  if (!key) {
    showToast('⚠️', 'Please enter a valid Gemini API key');
    return;
  }
  if (window.pywebview && window.pywebview.api && window.pywebview.api.save_api_key) {
    window.pywebview.api.save_api_key(key).then(function(res) {
      if (res && res.ok) {
        showToast('✅', 'Gemini API key saved & activated!');
      } else {
        showToast('❌', 'Error saving key: ' + (res ? res.error : ''));
      }
    });
  }
});

document.getElementById('btnClearAllMeetings').addEventListener('click', function() {
  if (!window.confirm('Permanently delete all meeting history and related data?')) return;
  if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.clear_all_meetings) {
    showToast('⚠️', 'Desktop data service is unavailable');
    return;
  }

  var button = this;
  button.disabled = true;
  window.pywebview.api.clear_all_meetings().then(function(res) {
    if (!res || !res.ok) {
      showToast('❌', (res && res.error) || 'Could not clear meeting data');
      return;
    }
    applyPayloadData(res, true);
    if (window.setMeetingState) window.setMeetingState('IDLE', '', '');
    showToast('✅', 'Meeting data cleared');
  }).catch(function(error) {
    showToast('❌', 'Could not clear meeting data: ' + error);
  }).finally(function() {
    button.disabled = false;
  });
});

// ─── CALLED BY PYTHON CONTROLLER ──────────────────────────────────────────────
window.setMeetingState = function(st, title, app) {
  var mtgTitle = document.getElementById('mtgTitle');
  var mtgSub = document.getElementById('mtgSub');
  var mtgIcon = document.getElementById('mtgIcon');

  if (st === 'RECORDING') {
    state.isRecording = true;
    btnRecord.textContent = '⏹️ End & Analyze';
    btnRecord.className = 'btn btn-danger';
    btnManualAnalyze.style.display = 'inline-flex';
    mtgTitle.textContent = '🔴 Recording: ' + (title || 'Meeting');
    mtgSub.textContent = 'Active call detected in ' + (app || 'Microphone') + ' — streaming audio...';
    mtgIcon.textContent = '🎙️';
    setStep('rec', 'working');
  } else if (st === 'ANALYZING') {
    state.isRecording = false;
    btnRecord.textContent = '⚡ Analyzing...';
    btnRecord.className = 'btn btn-demo';
    btnManualAnalyze.style.display = 'none';
    mtgTitle.textContent = '⚡ Synthesizing Meeting Intelligence...';
    mtgSub.textContent = 'Invoking Gemini 3.7 Flash multi-agent pipeline...';
    mtgIcon.textContent = '🧠';
  } else {
    state.isRecording = false;
    btnRecord.textContent = '🎙️ Start Recording';
    btnRecord.className = 'btn btn-primary';
    btnManualAnalyze.style.display = 'none';
    mtgTitle.textContent = 'Ready for Your Next Meeting';
    mtgSub.textContent = 'Monitoring Firefox, Chrome, Safari, Edge, and Zoom for active audio calls.';
    mtgIcon.textContent = '🎯';
  }
};

window.setStep = function(stepName, status) {
  var pill = document.getElementById('step-' + stepName);
  if (!pill) return;
  pill.classList.remove('working', 'done');
  if (status === 'working') pill.classList.add('working');
  if (status === 'done') pill.classList.add('done');
};

window.renderResults = function(d, isInitialLoad) {
  if (!d) return;
  state.lastBundle = d;

  document.getElementById('repTitle').textContent = d.title || 'Meeting Report';
  document.getElementById('repDate').textContent = d.created_at || 'Just now';
  document.getElementById('repSummaryText').innerHTML = formatMarkdown(d.summary || 'Summary unavailable.');

  // Key decisions
  var dl = document.getElementById('repDecisionsList');
  dl.innerHTML = '';
  var decs = d.key_decisions || [];
  if (!decs.length) {
    dl.innerHTML = '<div style="color:var(--txt-dim);padding:6px;">No specific decisions detected.</div>';
  } else {
    decs.forEach(function(dec) {
      var row = document.createElement('div');
      row.className = 'item-row';
      row.innerHTML = '<div style="display:flex;align-items:center;gap:8px;"><span style="color:var(--accent-green);">✓</span><span>' + esc(dec) + '</span></div>';
      dl.appendChild(row);
    });
  }

  // Tasks
  var tl = document.getElementById('repTasksList');
  tl.innerHTML = '';
  var tasks = d.action_items || [];
  document.getElementById('repTaskCount').textContent = tasks.length;
  if (!tasks.length) {
    tl.innerHTML = '<div style="color:var(--txt-dim);padding:6px;">No action items detected.</div>';
  } else {
    tasks.forEach(function(t) {
      var p = (t.priority || 'Medium').toLowerCase();
      var pClass = p === 'high' ? 'badge-high' : p === 'low' ? 'badge-low' : 'badge-med';
      var row = document.createElement('div');
      row.className = 'item-row';
      row.innerHTML = 
        '<div>' +
          '<div style="font-weight:600;color:var(--txt-main);">' + esc(t.task) + '</div>' +
          '<div style="font-size:0.72rem;color:var(--txt-dim);margin-top:2px;">👤 ' + esc(t.owner) + ' &nbsp;|&nbsp; ⏰ ' + esc(t.deadline || 'TBD') + '</div>' +
        '</div>' +
        '<span class="badge-pill ' + pClass + '">' + esc(t.priority || 'Medium') + '</span>';
      tl.appendChild(row);
    });
  }

  // Commitments
  var pl = document.getElementById('repPromisesList');
  pl.innerHTML = '';
  var proms = d.commitments || [];
  if (!proms.length) {
    pl.innerHTML = '<div style="color:var(--txt-dim);padding:6px;">No commitments detected.</div>';
  } else {
    proms.forEach(function(c) {
      var row = document.createElement('div');
      row.className = 'item-row';
      row.innerHTML = 
        '<div>' +
          '<div style="font-weight:600;color:var(--txt-main);">' + esc(c.commitment) + '</div>' +
          '<div style="font-size:0.72rem;color:var(--txt-dim);margin-top:2px;">👤 ' + esc(c.person) + ' &nbsp;|&nbsp; 📅 ' + esc(c.deadline || 'TBD') + '</div>' +
        '</div>' +
        '<span class="badge-pill badge-med">' + esc(c.status || 'Open') + '</span>';
      pl.appendChild(row);
    });
  }

  // Calendar
  var cl = document.getElementById('repCalendarList');
  cl.innerHTML = '';
  var cals = d.calendar_suggestions || [];
  if (!cals.length) {
    cl.innerHTML = '<div style="color:var(--txt-dim);padding:6px;">No follow-up meetings needed.</div>';
  } else {
    cals.forEach(function(c) {
      var row = document.createElement('div');
      row.className = 'item-row';
      row.innerHTML = '<div><div style="font-weight:600;">📅 ' + esc(c.proposed_title || c.title || 'Follow-up') + '</div><div style="font-size:0.72rem;color:var(--txt-dim);margin-top:2px;">⏰ ' + esc(c.suggested_slot) + ' &nbsp;|&nbsp; 👥 ' + esc((c.participants || []).join(', ')) + '</div></div>';
      cl.appendChild(row);
    });
  }

  // Personalized email drafts for every speaker with a task or commitment.
  renderEmailDrafts(d);

  // Transcript
  document.getElementById('repTranscriptText').value = d.labeled_transcript || d.raw_transcript || 'Transcript unavailable.';

  // Mark all steps done
  ['rec','stt','speakers','memory','summary','tasks','calendar','email'].forEach(function(s){ setStep(s, 'done'); });

  // Switch to summary tab
  var sumTab = document.querySelector('[data-tab="tab-summary"]');
  if (sumTab) sumTab.click();
  if (!isInitialLoad) {
    showToast('🎉', 'Meeting analysis complete!');
  }
};

window.updateMetrics = function(stats) {
  if (!stats) return;
  if (stats.total_meetings !== undefined) {
    document.getElementById('badgeArchCount').textContent = stats.total_meetings;
  }
  if (stats.total_tasks !== undefined) {
    document.getElementById('badgeTasksCount').textContent = stats.total_tasks;
  }
};

// Copy & Download helpers
document.getElementById('btnCopySummary').addEventListener('click', function() {
  if (state.lastBundle && state.lastBundle.summary) {
    navigator.clipboard.writeText(state.lastBundle.summary);
    showToast('📋', 'Summary copied to clipboard!');
  }
});

document.getElementById('btnDownloadMd').addEventListener('click', function() {
  if (!state.lastBundle) return;
  var b = state.lastBundle;
  var content = '# ' + (b.title || 'Meeting Summary') + '\\n\\n' +
                '**Date:** ' + (b.created_at || 'Unknown') + '\\n\\n' +
                '## Summary\\n' + (b.summary || '') + '\\n\\n' +
                '## Key Decisions\\n' + (b.key_decisions || []).map(function(d){ return '- ' + d; }).join('\\n') + '\\n\\n' +
                '## Action Items\\n' + (b.action_items || []).map(function(t){ return '- [' + (t.priority||'Med') + '] ' + t.task + ' (' + t.owner + ') Due: ' + t.deadline; }).join('\\n') + '\\n\\n' +
                '## Transcript\\n```\\n' + (b.labeled_transcript || b.raw_transcript || '') + '\\n```\\n';
  
  var blob = new Blob([content], { type: 'text/markdown' });
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url;
  a.download = (b.title || 'Meeting').replace(/\\s+/g, '_') + '_Report.md';
  a.click();
  showToast('💾', 'Report downloaded as Markdown');
});

// Toast
function showToast(icon, msg) {
  var t = document.getElementById('toast');
  document.getElementById('toastIcon').textContent = icon;
  document.getElementById('toastMsg').textContent = msg;
  t.classList.add('on');
  clearTimeout(t._timer);
  t._timer = setTimeout(function(){ t.classList.remove('on'); }, 4000);
}

function esc(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ─── INITIAL HYDRATION & PERSISTENCE ──────────────────────────────────────────
/* __INITIAL_DATA_PLACEHOLDER__ */

function clearLatestMeeting() {
  state.lastBundle = null;
  document.getElementById('repTitle').textContent = 'Meeting Summary & Action Items';
  document.getElementById('repDate').textContent = 'Select a meeting or run a session to view analysis.';
  document.getElementById('repSummaryText').textContent = 'No meeting analyzed yet.';
  document.getElementById('repDecisionsList').innerHTML = '<div style="color:var(--txt-dim);font-size:0.85rem;padding:8px;">Decisions will appear here.</div>';
  document.getElementById('repTasksList').innerHTML = '<div style="color:var(--txt-dim);font-size:0.85rem;padding:8px;">No action items detected yet.</div>';
  document.getElementById('repPromisesList').innerHTML = '<div style="color:var(--txt-dim);font-size:0.85rem;padding:8px;">No commitments recorded.</div>';
  document.getElementById('repCalendarList').innerHTML = '<div style="color:var(--txt-dim);font-size:0.85rem;padding:8px;">No calendar suggestions.</div>';
  document.getElementById('repTaskCount').textContent = '0';
  document.getElementById('emailDraftsList').innerHTML = '<div style="color:var(--txt-dim);font-size:0.85rem;padding:8px;">Personalized drafts will appear here after meeting analysis.</div>';
  document.getElementById('btnEmailAllSpeakers').disabled = true;
  document.getElementById('repTranscriptText').value = '';
}

function applyPayloadData(res, isInitial) {
  if (!res) return;
  if (res.stats) window.updateMetrics(res.stats);
  if (res.latest_bundle) window.renderResults(res.latest_bundle, isInitial);
  else if (Object.prototype.hasOwnProperty.call(res, 'latest_bundle')) clearLatestMeeting();
  if (Array.isArray(res.history)) {
    allArchiveMeetings = res.history;
    renderArchiveGrid(allArchiveMeetings);
  }
  if (Array.isArray(res.tasks)) renderTasksBoard(res.tasks);
  if (Array.isArray(res.commitments)) renderCommitmentsBoard(res.commitments);
}

// 1. Immediately apply preloaded data so the UI is NEVER blank
if (window.__PRELOADED_DATA__) {
  try {
    applyPayloadData(window.__PRELOADED_DATA__, true);
  } catch(e) {
    console.error('Error applying preloaded data:', e);
  }
}

// 2. Continually ensure Python Bridge connection for live events & polling
function initDesktopApp() {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.get_initial_data) {
    window.pywebview.api.get_initial_data().then(function(res) {
      if (res && res.ok) {
        applyPayloadData(res, true);
        var statusEl = document.getElementById('backendStatusBadge');
        if (statusEl) {
          statusEl.textContent = '⚡ Connected: SQLite & Gemini';
          statusEl.style.color = 'var(--accent-green)';
        }
      }
    }).catch(function(err) {
      console.error('Initial data error:', err);
    });
  }
}

// Polling loop to guarantee bridge connection
var bridgePollCount = 0;
function pollBridge() {
  if (window.pywebview && window.pywebview.api) {
    initDesktopApp();
  } else if (bridgePollCount < 40) {
    bridgePollCount++;
    setTimeout(pollBridge, 250);
  }
}

window.addEventListener('pywebviewready', initDesktopApp);
window.addEventListener('DOMContentLoaded', function() {
  if (window.__PRELOADED_DATA__) {
    applyPayloadData(window.__PRELOADED_DATA__, true);
  }
  pollBridge();
});
setTimeout(pollBridge, 300);
</script>
</body>
</html>
"""
