import json
import threading
import urllib.parse
import urllib.request
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox


SERVER_URL = "http://127.0.0.1:8000"


class MiniTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Zero2Print Mini-Timer")
        self.root.geometry("540x580")
        self.root.minsize(480, 540)

        self.projects = []
        self.jobs = []
        self.active_timers = []
        self.categories = []

        self.selected_project_id = None

        self.build_ui()
        self.load_initial_data()

    def build_ui(self):
        self.root.columnconfigure(0, weight=1)

        header = tk.Frame(self.root, padx=12, pady=10)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        title = tk.Label(
            header,
            text="Zero2Print Mini-Timer",
            font=("Arial", 16, "bold")
        )
        title.grid(row=0, column=0, sticky="w")

        self.status_label = tk.Label(
            header,
            text="Bereit",
            fg="#6b7280"
        )
        self.status_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        form = tk.LabelFrame(self.root, text="Timer starten", padx=12, pady=12)
        form.grid(row=1, column=0, sticky="ew", padx=12, pady=8)
        form.columnconfigure(1, weight=1)

        tk.Label(form, text="Projekt").grid(row=0, column=0, sticky="w", pady=5)
        self.project_combo = ttk.Combobox(form, state="readonly")
        self.project_combo.grid(row=0, column=1, sticky="ew", pady=5)
        self.project_combo.bind("<<ComboboxSelected>>", self.on_project_selected)

        tk.Label(form, text="Druckjob").grid(row=1, column=0, sticky="w", pady=5)
        self.job_combo = ttk.Combobox(form, state="readonly")
        self.job_combo.grid(row=1, column=1, sticky="ew", pady=5)

        tk.Label(form, text="Kategorie").grid(row=2, column=0, sticky="w", pady=5)
        self.category_combo = ttk.Combobox(form, state="readonly")
        self.category_combo.grid(row=2, column=1, sticky="ew", pady=5)

        tk.Label(form, text="Notiz").grid(row=3, column=0, sticky="nw", pady=5)
        self.note_text = tk.Text(form, height=4, wrap="word")
        self.note_text.grid(row=3, column=1, sticky="ew", pady=5)

        button_frame = tk.Frame(form)
        button_frame.grid(row=4, column=1, sticky="e", pady=(10, 0))

        self.start_button = tk.Button(
            button_frame,
            text="Timer starten",
            command=self.start_timer,
            bg="#2563eb",
            fg="white",
            padx=12,
            pady=6
        )
        self.start_button.pack(side="left", padx=(0, 8))

        self.open_web_button = tk.Button(
            button_frame,
            text="Web öffnen",
            command=self.open_web,
            padx=12,
            pady=6
        )
        self.open_web_button.pack(side="left")

        active = tk.LabelFrame(self.root, text="Aktive Timer", padx=12, pady=12)
        active.grid(row=2, column=0, sticky="nsew", padx=12, pady=8)
        active.columnconfigure(0, weight=1)
        active.rowconfigure(0, weight=1)

        self.root.rowconfigure(2, weight=1)

        self.active_list = tk.Listbox(active, height=10)
        self.active_list.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(active, orient="vertical", command=self.active_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.active_list.configure(yscrollcommand=scrollbar.set)

        active_buttons = tk.Frame(active)
        active_buttons.grid(row=1, column=0, columnspan=2, sticky="e", pady=(10, 0))

        self.refresh_button = tk.Button(
            active_buttons,
            text="Aktualisieren",
            command=self.refresh_active_timers,
            padx=12,
            pady=6
        )
        self.refresh_button.pack(side="left", padx=(0, 8))

        self.stop_button = tk.Button(
            active_buttons,
            text="Ausgewählten stoppen",
            command=self.stop_selected_timer,
            bg="#16a34a",
            fg="white",
            padx=12,
            pady=6
        )
        self.stop_button.pack(side="left")

        footer = tk.Frame(self.root, padx=12, pady=8)
        footer.grid(row=3, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)

        self.server_label = tk.Label(
            footer,
            text=f"Server: {SERVER_URL}",
            fg="#6b7280"
        )
        self.server_label.grid(row=0, column=0, sticky="w")

    def set_status(self, message, error=False):
        self.status_label.config(
            text=str(message),
            fg="#dc2626" if error else "#16a34a"
        )

    def safe_error_message(self, error):
        text = str(error)

        if not text or text.lower() == "none":
            return "Unbekannter Fehler. Bitte Hauptfenster/Server prüfen."

        return text

    def api_get(self, path):
        url = f"{SERVER_URL}{path}"

        with urllib.request.urlopen(url, timeout=5) as response:
            data = response.read().decode("utf-8")
            return json.loads(data)

    def api_post(self, path, payload):
        url = f"{SERVER_URL}{path}"
        encoded = urllib.parse.urlencode(payload).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=encoded,
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )

        with urllib.request.urlopen(request, timeout=5) as response:
            data = response.read().decode("utf-8")
            return json.loads(data)

    def run_threaded(self, func):
        thread = threading.Thread(target=func, daemon=True)
        thread.start()

    def load_initial_data(self):
        self.run_threaded(self._load_initial_data)

    def _load_initial_data(self):
        try:
            categories_data = self.api_get("/time/api/categories")
            projects_data = self.api_get("/time/api/projects")

            self.categories = categories_data.get("categories", [])
            self.projects = projects_data.get("projects", [])

            self.root.after(0, self.update_project_combo)
            self.root.after(0, self.update_category_combo)
            self.root.after(0, self.refresh_active_timers)
            self.root.after(0, lambda: self.set_status("Verbunden"))

        except Exception as error:
            error_text = self.safe_error_message(error)

            self.root.after(
                0,
                lambda: self.set_status(
                    "Keine Verbindung. Läuft der PrintManager?",
                    error=True
                )
            )
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Verbindung fehlgeschlagen",
                    f"Mini-Timer kann den Server nicht erreichen:\n\n{SERVER_URL}\n\nFehler:\n{error_text}"
                )
            )

    def update_project_combo(self):
        values = []

        for project in self.projects:
            values.append(
                f"{project['id']} | {project['customer']} — {project['name']}"
            )

        self.project_combo["values"] = values

        if values:
            self.project_combo.current(0)
            self.on_project_selected()

    def update_category_combo(self):
        self.category_combo["values"] = self.categories

        if self.categories:
            default_index = 0

            for index, category in enumerate(self.categories):
                if category == "CAD / Konstruktion":
                    default_index = index
                    break

            self.category_combo.current(default_index)

    def on_project_selected(self, event=None):
        selection = self.project_combo.get()

        if not selection:
            self.selected_project_id = None
            return

        try:
            self.selected_project_id = int(selection.split("|")[0].strip())
        except ValueError:
            self.selected_project_id = None
            return

        self.run_threaded(self._load_jobs_for_project)

    def _load_jobs_for_project(self):
        if not self.selected_project_id:
            return

        try:
            jobs_data = self.api_get(f"/time/api/jobs?project_id={self.selected_project_id}")
            self.jobs = jobs_data.get("jobs", [])

            self.root.after(0, self.update_job_combo)

        except Exception as error:
            error_text = self.safe_error_message(error)
            self.root.after(
                0,
                lambda: self.set_status(f"Jobs konnten nicht geladen werden: {error_text}", error=True)
            )

    def update_job_combo(self):
        values = ["0 | Kein Druckjob"]

        for job in self.jobs:
            values.append(
                f"{job['id']} | {job['job_number']} — {job['project']} — {job['status']}"
            )

        self.job_combo["values"] = values
        self.job_combo.current(0)

    def get_selected_job_id(self):
        selection = self.job_combo.get()

        if not selection:
            return ""

        try:
            job_id = int(selection.split("|")[0].strip())
        except ValueError:
            return ""

        if job_id == 0:
            return ""

        return str(job_id)

    def start_timer(self):
        if not self.selected_project_id:
            messagebox.showwarning("Fehlt", "Bitte ein Projekt auswählen.")
            return

        category = self.category_combo.get().strip()

        if not category:
            messagebox.showwarning("Fehlt", "Bitte eine Kategorie auswählen.")
            return

        note = self.note_text.get("1.0", "end").strip()

        payload = {
            "project_id": str(self.selected_project_id),
            "print_job_id": self.get_selected_job_id(),
            "category": category,
            "note": note,
        }

        self.run_threaded(lambda: self._start_timer_request(payload))

    def _start_timer_request(self, payload):
        try:
            result = self.api_post("/time/api/start", payload)

            if result.get("success"):
                self.root.after(0, lambda: self.set_status("Timer gestartet"))
                self.root.after(0, lambda: self.note_text.delete("1.0", "end"))
                self.root.after(0, self.refresh_active_timers)
            else:
                message = result.get("message") or "Timer konnte nicht gestartet werden."
                self.root.after(0, lambda: self.set_status(message, error=True))
                self.root.after(0, lambda: messagebox.showerror("Fehler", message))

        except Exception as error:
            error_text = self.safe_error_message(error)
            self.root.after(
                0,
                lambda: self.set_status(f"Fehler beim Starten: {error_text}", error=True)
            )
            self.root.after(
                0,
                lambda: messagebox.showerror("Fehler beim Starten", error_text)
            )

    def refresh_active_timers(self):
        self.run_threaded(self._refresh_active_timers)

    def _refresh_active_timers(self):
        try:
            data = self.api_get("/time/api/active")
            self.active_timers = data.get("active_timers", [])

            self.root.after(0, self.update_active_list)

        except Exception as error:
            error_text = self.safe_error_message(error)
            self.root.after(
                0,
                lambda: self.set_status(f"Aktive Timer konnten nicht geladen werden: {error_text}", error=True)
            )

    def update_active_list(self):
        self.active_list.delete(0, "end")

        if not self.active_timers:
            self.active_list.insert("end", "Keine aktiven Timer")
            return

        for entry in self.active_timers:
            entry_id = entry.get("id")
            customer = entry.get("customer", "-")
            project = entry.get("project", "-")
            job_number = entry.get("job_number", "-")
            category = entry.get("category", "-")
            start_time = entry.get("start_time", "-")

            line = (
                f"{entry_id} | "
                f"{customer} — {project} | "
                f"{job_number} | "
                f"{category} | "
                f"seit {start_time}"
            )
            self.active_list.insert("end", line)

    def stop_selected_timer(self):
        selection_index = self.active_list.curselection()

        if not selection_index:
            messagebox.showwarning("Fehlt", "Bitte einen aktiven Timer auswählen.")
            return

        if not self.active_timers:
            messagebox.showinfo("Info", "Es gibt aktuell keinen aktiven Timer.")
            return

        index = selection_index[0]

        if index >= len(self.active_timers):
            messagebox.showinfo("Info", "Bitte einen echten aktiven Timer auswählen.")
            return

        entry = self.active_timers[index]
        entry_id = entry.get("id")

        if not entry_id:
            messagebox.showerror("Fehler", "Timer-ID konnte nicht gelesen werden.")
            return

        self.run_threaded(lambda: self._stop_timer_request(entry_id))

    def _stop_timer_request(self, entry_id):
        try:
            result = self.api_post(
                "/time/api/stop",
                {
                    "entry_id": str(entry_id)
                }
            )

            if result.get("success"):
                minutes = result.get("duration_minutes")
                if minutes is None:
                    minutes = "-"

                self.root.after(0, lambda: self.set_status(f"Timer gestoppt: {minutes} min"))
                self.root.after(0, self.refresh_active_timers)
            else:
                message = result.get("message") or "Timer konnte nicht gestoppt werden."
                self.root.after(0, lambda: self.set_status(message, error=True))
                self.root.after(0, lambda: messagebox.showerror("Fehler", message))

        except Exception as error:
            error_text = self.safe_error_message(error)
            self.root.after(
                0,
                lambda: self.set_status(f"Fehler beim Stoppen: {error_text}", error=True)
            )
            self.root.after(
                0,
                lambda: messagebox.showerror("Fehler beim Stoppen", error_text)
            )

    def open_web(self):
        webbrowser.open(f"{SERVER_URL}/time")


def main():
    root = tk.Tk()
    MiniTimerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()