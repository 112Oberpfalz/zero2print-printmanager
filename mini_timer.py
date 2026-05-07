import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import requests


DEFAULT_SERVER_URL = "http://127.0.0.1:8000"
CONFIG_FILE = "mini_timer_config.json"


class MiniTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Zero2Print Mini-Timer")
        self.root.geometry("420x420")
        self.root.resizable(False, False)

        self.server_url = self.load_server_url()

        self.projects = []
        self.jobs = []
        self.categories = []
        self.active_entry = None

        self.selected_project_id = None
        self.selected_job_id = None

        self.build_ui()
        self.load_initial_data()
        self.refresh_active_timer_loop()

    def load_server_url(self):
        if not os.path.exists(CONFIG_FILE):
            return DEFAULT_SERVER_URL

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            server_url = data.get("server_url", DEFAULT_SERVER_URL).strip()

            if server_url.endswith("/"):
                server_url = server_url[:-1]

            return server_url or DEFAULT_SERVER_URL
        except Exception:
            return DEFAULT_SERVER_URL

    def api_url(self, path):
        return f"{self.server_url}{path}"

    def build_ui(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)

        title = ttk.Label(main, text="Zero2Print Mini-Timer", font=("Arial", 15, "bold"))
        title.pack(anchor="w")

        self.server_label = ttk.Label(main, text=f"Server: {self.server_url}", foreground="#666")
        self.server_label.pack(anchor="w", pady=(2, 14))

        ttk.Label(main, text="Projekt").pack(anchor="w")
        self.project_box = ttk.Combobox(main, state="readonly")
        self.project_box.pack(fill="x", pady=(0, 10))
        self.project_box.bind("<<ComboboxSelected>>", self.on_project_selected)

        ttk.Label(main, text="Druckjob optional").pack(anchor="w")
        self.job_box = ttk.Combobox(main, state="readonly")
        self.job_box.pack(fill="x", pady=(0, 10))
        self.job_box.bind("<<ComboboxSelected>>", self.on_job_selected)

        ttk.Label(main, text="Kategorie").pack(anchor="w")
        self.category_box = ttk.Combobox(main, state="readonly")
        self.category_box.pack(fill="x", pady=(0, 10))

        ttk.Label(main, text="Notiz optional").pack(anchor="w")
        self.note_entry = ttk.Entry(main)
        self.note_entry.pack(fill="x", pady=(0, 14))

        self.status_label = ttk.Label(main, text="Kein aktiver Timer", font=("Arial", 10, "bold"))
        self.status_label.pack(anchor="w", pady=(4, 8))

        self.runtime_label = ttk.Label(main, text="", foreground="#2563eb")
        self.runtime_label.pack(anchor="w", pady=(0, 14))

        button_frame = ttk.Frame(main)
        button_frame.pack(fill="x")

        self.start_button = ttk.Button(button_frame, text="Start", command=self.start_timer)
        self.start_button.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_timer)
        self.stop_button.pack(side="left", fill="x", expand=True, padx=(6, 0))

        self.refresh_button = ttk.Button(main, text="Aktualisieren", command=self.load_initial_data)
        self.refresh_button.pack(fill="x", pady=(12, 0))

    def load_initial_data(self):
        try:
            self.load_projects()
            self.load_categories()
            self.load_active_timer()
        except requests.RequestException:
            messagebox.showerror(
                "Verbindungsfehler",
                f"Server nicht erreichbar:\n{self.server_url}"
            )

    def load_projects(self):
        response = requests.get(self.api_url("/time/api/projects"), timeout=5)
        response.raise_for_status()

        self.projects = response.json()

        values = [project["name"] for project in self.projects]
        self.project_box["values"] = values

        if values and not self.project_box.get():
            self.project_box.current(0)
            self.on_project_selected()

    def load_categories(self):
        response = requests.get(self.api_url("/time/api/categories"), timeout=5)
        response.raise_for_status()

        self.categories = response.json()
        self.category_box["values"] = self.categories

        if self.categories and not self.category_box.get():
            self.category_box.current(0)

    def on_project_selected(self, event=None):
        index = self.project_box.current()

        if index < 0 or index >= len(self.projects):
            self.selected_project_id = None
            return

        project = self.projects[index]
        self.selected_project_id = project["id"]

        self.load_jobs_for_project(self.selected_project_id)

    def load_jobs_for_project(self, project_id):
        response = requests.get(
            self.api_url(f"/time/api/jobs?project_id={project_id}"),
            timeout=5
        )
        response.raise_for_status()

        self.jobs = response.json()

        values = ["Kein Druckjob"]

        for job in self.jobs:
            values.append(f'DJ-{job["id"]:04d} - {job["status"]}')

        self.job_box["values"] = values
        self.job_box.current(0)
        self.selected_job_id = None

    def on_job_selected(self, event=None):
        index = self.job_box.current()

        if index <= 0:
            self.selected_job_id = None
            return

        job_index = index - 1

        if job_index < len(self.jobs):
            self.selected_job_id = self.jobs[job_index]["id"]

    def load_active_timer(self):
        response = requests.get(self.api_url("/time/api/active"), timeout=5)
        response.raise_for_status()

        data = response.json()

        if data:
            self.active_entry = data
        else:
            self.active_entry = None

        self.update_active_display()

    def update_active_display(self):
        if not self.active_entry:
            self.status_label.config(text="Kein aktiver Timer")
            self.runtime_label.config(text="")
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            return

        project_name = self.active_entry.get("project_name", "-")
        category = self.active_entry.get("category", "-")

        self.status_label.config(text=f"Läuft: {project_name} / {category}")

        runtime = self.calculate_runtime_text()
        self.runtime_label.config(text=runtime)

        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

    def calculate_runtime_text(self):
        if not self.active_entry:
            return ""

        start_time_raw = self.active_entry.get("start_time")

        if not start_time_raw:
            return ""

        try:
            start_time = datetime.fromisoformat(start_time_raw)
            diff = datetime.now() - start_time

            total_seconds = int(diff.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            return f"Laufzeit: {hours:02d}:{minutes:02d}:{seconds:02d}"
        except Exception:
            return ""

    def refresh_active_timer_loop(self):
        try:
            self.load_active_timer()
        except Exception:
            pass

        self.root.after(10000, self.refresh_active_timer_loop)

    def start_timer(self):
        if not self.selected_project_id:
            messagebox.showwarning("Fehlt", "Bitte ein Projekt auswählen.")
            return

        category = self.category_box.get().strip()

        if not category:
            messagebox.showwarning("Fehlt", "Bitte eine Kategorie auswählen.")
            return

        payload = {
            "project_id": self.selected_project_id,
            "print_job_id": self.selected_job_id,
            "category": category,
            "note": self.note_entry.get().strip()
        }

        try:
            response = requests.post(
                self.api_url("/time/api/start"),
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            self.note_entry.delete(0, tk.END)
            self.load_active_timer()
        except requests.RequestException as error:
            messagebox.showerror("Fehler", f"Timer konnte nicht gestartet werden:\n{error}")

    def stop_timer(self):
        try:
            response = requests.post(
                self.api_url("/time/api/stop"),
                timeout=5
            )
            response.raise_for_status()
            self.load_active_timer()
        except requests.RequestException as error:
            messagebox.showerror("Fehler", f"Timer konnte nicht gestoppt werden:\n{error}")


def main():
    root = tk.Tk()
    app = MiniTimerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()