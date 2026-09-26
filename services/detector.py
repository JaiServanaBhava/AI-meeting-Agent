"""Cross-Platform Meeting Detection Engine for macOS (including macOS 12.7.6 Monterey) and Windows.

Detects Google Meet in Firefox, Chrome, Edge, Brave, Safari, and native Zoom / Teams apps
WITHOUT requiring macOS Assistive Access or Accessibility permissions.
"""

import sys
import os
import glob
import json
import time
import subprocess
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import psutil

try:
    import lz4.block
    LZ4_AVAILABLE = True
except ImportError:
    LZ4_AVAILABLE = False


class MeetingDetector:
    """Zero-permission meeting detector for Firefox, Chrome, Safari, Edge, Zoom, and Teams."""

    def __init__(self):
        self.os_type = sys.platform  # 'darwin' or 'win32'
        self.firefox_profile_patterns = self._get_firefox_patterns()

    def _get_firefox_patterns(self):
        if self.os_type == "darwin":
            return [os.path.expanduser("~/Library/Application Support/Firefox/Profiles/*/sessionstore-backups/recovery.jsonlz4")]
        elif self.os_type == "win32":
            appdata = os.getenv("APPDATA", "")
            return [os.path.join(appdata, "Mozilla", "Firefox", "Profiles", "*", "sessionstore-backups", "recovery.jsonlz4")]
        return []

    def scan_for_meeting(self) -> Tuple[bool, str, str]:
        """Scans system for active meetings.

        Returns:
            Tuple of (is_active: bool, meeting_title: str, app_name: str)
        """
        # 1. Check Firefox (Zero permissions needed via sessionstore recovery)
        ff_hit = self._check_firefox_tabs()
        if ff_hit[0]:
            return ff_hit

        # 2. Check Native Desktop Meeting Apps (Zoom, Teams, Webex)
        native_hit = self._check_native_apps()
        if native_hit[0]:
            return native_hit

        # 3. Check Other Browsers (Chrome, Brave, Edge, Safari)
        if self.os_type == "darwin":
            browser_hit = self._check_macos_browsers()
            if browser_hit[0]:
                return browser_hit
        elif self.os_type == "win32":
            win_hit = self._check_windows_windows()
            if win_hit[0]:
                return win_hit

        return False, "", ""

    def _check_firefox_tabs(self) -> Tuple[bool, str, str]:
        """Reads Firefox active tabs via sessionstore recovery.jsonlz4 without needing OS permissions."""
        if not LZ4_AVAILABLE:
            return False, "", ""

        # Quick check if Firefox is running
        ff_running = any(
            "firefox" in (p.info["name"] or "").lower()
            for p in psutil.process_iter(["name"])
        )
        if not ff_running:
            return False, "", ""

        for pattern in self.firefox_profile_patterns:
            files = glob.glob(pattern)
            for fpath in files:
                try:
                    with open(fpath, "rb") as fp:
                        raw = fp.read()
                    if raw.startswith(b"mozLz40\0"):
                        data = lz4.block.decompress(raw[8:])
                        state = json.loads(data.decode("utf-8", errors="ignore"))
                        windows = state.get("windows", [])
                        for w in windows:
                            for t in w.get("tabs", []):
                                entries = t.get("entries", [])
                                if not entries:
                                    continue
                                current_index = t.get("index", len(entries))
                                if not isinstance(current_index, int) or not 1 <= current_index <= len(entries):
                                    current_index = len(entries)
                                current_index -= 1
                                entry = entries[current_index]
                                url = entry.get("url", "").lower()
                                title = entry.get("title", "")
                                # Google Meet Detection
                                if "meet.google.com" in url:
                                    clean_title = title if (title and "meet" not in title.lower()) else "Google Meet Call"
                                    return True, clean_title, "Firefox Browser"
                                # Zoom Web
                                if "zoom.us/j/" in url or "zoom.us/wc/" in url:
                                    return True, title or "Zoom Web Meeting", "Firefox Browser"
                                # Teams Web
                                if "teams.microsoft.com" in url or "teams.live.com" in url:
                                    return True, title or "Microsoft Teams Web", "Firefox Browser"
                except Exception:
                    continue

        return False, "", ""

    def _check_native_apps(self) -> Tuple[bool, str, str]:
        """Checks for running native meeting processes."""
        try:
            for p in psutil.process_iter(["name", "cmdline"]):
                try:
                    pname = (p.info["name"] or "").lower()
                    # Zoom Desktop App
                    if "zoom.us" in pname or "zoom.exe" in pname or pname == "zoom":
                        return True, "Zoom Meeting Call", "Zoom Desktop App"
                    # Teams Desktop
                    if "teams" in pname and "helper" not in pname:
                        cmd = " ".join(p.info.get("cmdline") or [])
                        if "meeting" in cmd.lower() or "call" in cmd.lower():
                            return True, "Microsoft Teams Call", "Microsoft Teams"
                    # Webex
                    if "webex" in pname or "cptwebex" in pname:
                        return True, "Cisco Webex Call", "Cisco Webex"
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        return False, "", ""

    def _check_macos_browsers(self) -> Tuple[bool, str, str]:
        """Direct AppleScript inspection for Chrome, Brave, Edge, and Safari without System Events."""
        browsers = ["Google Chrome", "Brave Browser", "Microsoft Edge", "Safari"]
        for browser in browsers:
            try:
                proc_running = any(
                    browser.lower() in (p.info["name"] or "").lower()
                    for p in psutil.process_iter(["name"])
                )
                if not proc_running:
                    continue

                if browser == "Safari":
                    script = '''
                    try
                        tell application "Safari"
                            set tabList to {}
                            repeat with w in windows
                                repeat with t in tabs of w
                                    set u to URL of t
                                    if u contains "meet.google.com" or u contains "zoom.us/j/" then
                                        return (name of t & "|||" & u)
                                    end if
                                end repeat
                            end repeat
                            return ""
                        end tell
                    on error
                        return ""
                    end try
                    '''
                else:
                    script = f'''
                    try
                        tell application "{browser}"
                            repeat with w in windows
                                repeat with t in tabs of w
                                    set u to URL of t
                                    if u contains "meet.google.com" or u contains "zoom.us/j/" then
                                        return (title of t & "|||" & u)
                                    end if
                                end repeat
                            end repeat
                            return ""
                        end tell
                    on error
                        return ""
                    end try
                    '''

                res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=1.5)
                output = res.stdout.strip()
                if output and "|||" in output:
                    title, url = output.split("|||", 1)
                    title = title.strip()
                    if not title or title.lower() == "meet":
                        title = "Google Meet Call"
                    return True, title, f"{browser}"
            except Exception:
                continue

        return False, "", ""

    def _check_windows_windows(self) -> Tuple[bool, str, str]:
        """Enumerates active window titles on Windows to detect Google Meet / Zoom."""
        try:
            import ctypes
            EnumWindows = ctypes.windll.user32.EnumWindows
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
            GetWindowText = ctypes.windll.user32.GetWindowTextW
            GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
            IsWindowVisible = ctypes.windll.user32.IsWindowVisible

            titles = []

            def foreach_window(hwnd, lParam):
                if IsWindowVisible(hwnd):
                    length = GetWindowTextLength(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        GetWindowText(hwnd, buff, length + 1)
                        titles.append(buff.value)
                return True

            EnumWindows(EnumWindowsProc(foreach_window), 0)

            for t in titles:
                t_lower = t.lower()
                if "meet - " in t_lower or "google meet" in t_lower:
                    return True, t, "Google Meet"
                if "zoom meeting" in t_lower or "zoom webinar" in t_lower:
                    return True, t, "Zoom Meeting"
                if "teams meeting" in t_lower:
                    return True, t, "Microsoft Teams"
        except Exception:
            pass

        return False, "", ""
