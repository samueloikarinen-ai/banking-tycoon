import threading
import time
import datetime
import os

class HistoryLogger:
    def __init__(self, bank, log_file="history.log", check_interval=0.5):
        self.bank = bank
        self.log_file = log_file
        self.check_interval = check_interval
        self.logged_entries = set()  # track unique (day, desc) globally
        self._stop_event = threading.Event()

        # Ensure log file exists
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", encoding="utf-8") as f:
                pass

        # Load existing entries from file
        self._load_existing_entries()

        # Start background thread
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _load_existing_entries(self):
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    # Each line can have multiple entries separated by " | "
                    entries = line.split(" | ")
                    for entry in entries:
                        if entry.startswith("["):
                            # Remove timestamp prefix
                            text = entry.split("] ", 1)[1]
                        else:
                            text = entry
                        day_end = text.find(":")
                        if day_end != -1:
                            day = int(text[4:day_end])
                            desc = text[day_end+2:]
                            self.logged_entries.add((day, desc))
        except FileNotFoundError:
            pass

    def _run(self):
        while not self._stop_event.is_set():
            self._log_new_entries()
            time.sleep(self.check_interval)

    def _log_new_entries(self):
        # Collect all truly new entries
        batch_entries = []
        for day, desc in self.bank.history:
            if (day, desc) not in self.logged_entries:
                self.logged_entries.add((day, desc))
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                batch_entries.append(f"[{timestamp}] Day {day}: {desc}")

        if not batch_entries:
            return  # nothing new, don’t create a line

        # Append batch as a new line
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(" | ".join(batch_entries) + "\n")

    def stop(self):
        self._stop_event.set()
        self.thread.join()
