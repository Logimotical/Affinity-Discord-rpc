"""
Affinity -> Discord Rich Presence (Windows background version)

- Detects Affinity Photo, Designer, Publisher, or the unified Affinity app.
- Updates Discord Rich Presence while an Affinity app is running.
- Retries the Discord connection if Discord is closed or restarts.
- Designed to run with pythonw.exe, so no console window stays open.

Install:
  1. Run install_startup.bat once.
  2. Keep Discord desktop installed and signed in.
  3. Open an Affinity app.
"""

import ctypes
import logging
import platform
import subprocess
import time
from pathlib import Path

import psutil
from pypresence import Presence

# ---------------- CONFIG ----------------
CLIENT_ID = "1569370632242864139"
SHOW_FILENAME = True       # False hides the document name from Discord
UPDATE_INTERVAL = 15       # Discord Rich Presence update interval, in seconds
RETRY_INTERVAL = 10        # Wait before retrying a failed Discord connection

# Process name (lowercase, without .exe) -> (display name, Discord asset key)
# If your Affinity version uses a different process name, add it here.
APPS = {
    "photo": ("Affinity Photo", "affinity_photo"),
    "designer": ("Affinity Designer", "affinity_designer"),
    "publisher": ("Affinity Publisher", "affinity_publisher"),
    "affinity": ("Affinity", "affinity"),
}
# ----------------------------------------

SYSTEM = platform.system()
LOG_FILE = Path(__file__).with_name("affinity_rpc.log")

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)


def find_running_app():
    """Return app details for a running Affinity process, or None."""
    for proc in psutil.process_iter(["name", "create_time"]):
        try:
            name = (proc.info["name"] or "").lower()
            if name.endswith(".exe"):
                name = name[:-4]
            if name in APPS:
                display, asset = APPS[name]
                return name, display, asset, proc.info["create_time"]
        except (psutil.Error, OSError):
            continue
    return None


def windows_titles():
    """Return visible window titles on Windows."""
    user32 = ctypes.windll.user32
    titles = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                titles.append(buf.value)
        return True

    user32.EnumWindows(callback, 0)
    return titles


def mac_front_title(app_display):
    """Get the front window title on macOS (requires Accessibility permission)."""
    script = (
        'tell application "System Events" to tell (first process whose name '
        f'contains "{app_display}") to get name of front window'
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def get_document_name(display):
    """Best-effort document name parsed from the Affinity window title."""
    if not SHOW_FILENAME:
        return None

    if SYSTEM == "Windows":
        try:
            for title in windows_titles():
                if "affinity" in title.lower() and " - " in title:
                    document = title.split(" - ")[0].strip()
                    if document and "affinity" not in document.lower():
                        return document
        except Exception:
            logging.exception("Could not read Windows window titles")

    elif SYSTEM == "Darwin":
        title = mac_front_title(display)
        if title and "affinity" not in title.lower():
            return title.split(" - ")[0].strip()

    return None


def run_connected_session():
    """Connect to Discord and monitor Affinity until the connection fails."""
    rpc = Presence(CLIENT_ID)
    rpc.connect()
    logging.info("Connected to Discord RPC")

    active = False
    last_signature = None

    try:
        while True:
            found = find_running_app()

            if found:
                _, display, asset, started = found
                document = get_document_name(display)
                details = f"Editing {document}" if document else f"Working in {display}"
                state = display if document else "Creating something"
                signature = (details, state, asset, int(started))

                # Avoid sending the same activity on every scan.
                if signature != last_signature:
                    rpc.update(
                        details=details,
                        state=state,
                        large_image=asset,
                        large_text=display,
                        start=int(started),
                    )
                    last_signature = signature
                    logging.info("Presence updated: %s", display)

                active = True

            elif active:
                rpc.clear()
                active = False
                last_signature = None
                logging.info("No Affinity app detected; presence cleared")

            time.sleep(UPDATE_INTERVAL)

    finally:
        try:
            if active:
                rpc.clear()
        finally:
            rpc.close()
            logging.info("Discord RPC session closed")


def main():
    logging.info("Affinity Rich Presence background process started")

    while True:
        try:
            run_connected_session()
        except Exception:
            # This also handles Discord being closed or restarted.
            logging.exception("RPC session failed; will retry")
            time.sleep(RETRY_INTERVAL)


if __name__ == "__main__":
    main()
