import os
import sys
import time
import subprocess
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
EXTENSIONS_TO_WATCH = {'.py', '.html', '.css', '.js', '.md', '.bat'}
EXCLUDE_DIRS = {'.git', '__pycache__', 'venv', '.venv', '.idea', '.vscode'}

def run_git_sync():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Detected project change. Syncing to GitHub...")
    try:
        subprocess.run(["git", "add", "."], cwd=WORKSPACE_DIR, check=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subprocess.run(["git", "commit", "-m", f"Auto-sync: {timestamp}"], cwd=WORKSPACE_DIR, check=False)
        subprocess.run(["git", "push", "origin", "main"], cwd=WORKSPACE_DIR, check=True)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [✓] GitHub sync successful!")
        print("Live repo: https://github.com/Pushpendu-Maity/Final_Year_project\n")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [X] Git sync error: {e}")

class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_sync_time = 0

    def on_any_event(self, event):
        if event.is_directory:
            return
        ext = os.path.splitext(event.src_path)[1]
        if ext in EXTENSIONS_TO_WATCH and not any(ex in event.src_path for ex in EXCLUDE_DIRS):
            current_time = time.time()
            # Debounce 5 seconds so multiple rapid saves trigger only 1 push
            if current_time - self.last_sync_time > 5:
                self.last_sync_time = current_time
                time.sleep(2)
                run_git_sync()

def main():
    print("=" * 65)
    print("     BACKGROUND AUTO-SYNC WATCHER (Pushpendu-Maity/Final_Year_project)")
    print("=" * 65)
    print(f"Watching folder: {WORKSPACE_DIR}")
    print("Every time you save a file, it will automatically push to GitHub.")
    print("Press Ctrl+C to stop watching.\n")

    if HAS_WATCHDOG:
        event_handler = ChangeHandler()
        observer = Observer()
        observer.schedule(event_handler, WORKSPACE_DIR, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    else:
        print("Running simple polling watcher...")
        while True:
            time.sleep(10)

if __name__ == '__main__':
    main()
