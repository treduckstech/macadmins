#!/usr/bin/env python3
"""
Provides a graphical interface to select installed applications and add them to
the Dock using dockutil. Users can optionally clear or empty the Dock.

Author: Ben Rillie <ben@treducks.tech>
WARNING: Use at your own risk.
License: MIT
"""

import os
import sys
import subprocess
import logging
import tkinter as tk
from tkinter import ttk

# Logging Setup
LOG_FILE = '/var/log/pylog.log'

def setup_logging(log_file=LOG_FILE, level=logging.INFO):
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logging.info("Logging setup complete.")

def run_command(command, as_user=None):
    if as_user:
        # Use a login shell to ensure user's environment is loaded
        full_command = f"su - {as_user} -c '/usr/local/bin/dockutil {command}'"
    else:
        full_command = f"/usr/local/bin/dockutil {command}"
    logging.info(f"Running command: {full_command}")
    try:
        result = subprocess.run(full_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logging.info(f"Command output: {result.stdout.strip()}")
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed with return code {e.returncode}")
        logging.error(f"Error output: {e.stderr.strip()}")
        raise

def log_exception(e):
    logging.error(f"Exception occurred: {e}", exc_info=True)

def get_console_user():
    try:
        return subprocess.check_output("who | grep console | awk '{print $1}'", shell=True, text=True).strip()
    except subprocess.CalledProcessError:
        return None

# Set up logging
setup_logging()

def get_applications():
    logging.debug("Getting list of applications")
    applications_folder = "/Applications"
    apps = [f for f in os.listdir(applications_folder) if f.endswith(".app")]
    logging.debug(f"Found {len(apps)} applications")
    return sorted(apps)  # Sort the apps alphabetically

class AppSelector(tk.Tk):
    def __init__(self, apps):
        super().__init__()
        self.title("Select Applications")
        self.apps = apps
        self.selected_apps = []
        self.dont_clear_dock = tk.BooleanVar()

        self.create_widgets()
        self.update_idletasks()
        self.geometry(f"{self.winfo_reqwidth()}x{self.winfo_reqheight()}")
        self.center_window()
        
        # Make the window appear in the foreground
        self.lift()
        self.attributes("-topmost", True)
        self.after_idle(self.attributes, "-topmost", False)
        logging.debug("AppSelector window initialized")

    def center_window(self):
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        logging.debug(f"Window centered at position: {x}, {y}")

    def create_widgets(self):
        logging.debug("Creating widgets")
        self.frame = tk.Frame(self)
        self.frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.frame)
        self.scrollbar = tk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.checkbuttons = []
        self.vars = []

        columns = 5
        rows = -(-len(self.apps) // columns)  # Ceiling division to get number of rows

        for i, app in enumerate(self.apps):
            var = tk.BooleanVar()
            chk = tk.Checkbutton(self.inner_frame, text=app, variable=var)
            row = i % rows
            col = i // rows
            chk.grid(row=row, column=col, sticky="w", padx=5, pady=2)
            self.checkbuttons.append(chk)
            self.vars.append(var)

        self.inner_frame.update_idletasks()
        self.canvas.config(width=self.inner_frame.winfo_reqwidth(), height=min(500, self.inner_frame.winfo_reqheight()))

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(side="bottom", fill="x", pady=(0, 10))

        self.dont_clear_chk = tk.Checkbutton(self.button_frame, text="Don't Clear Dock", variable=self.dont_clear_dock)
        self.dont_clear_chk.grid(row=0, column=0, sticky="w", padx=5)

        self.ok_button = tk.Button(self.button_frame, text="OK", command=self.on_ok, width=10)
        self.cancel_button = tk.Button(self.button_frame, text="Cancel", command=self.on_cancel, width=10)
        self.empty_dock_button = tk.Button(self.button_frame, text="Empty Dock", command=self.on_empty_dock, width=10)

        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid_columnconfigure(5, weight=1)
        self.ok_button.grid(row=0, column=2, padx=5)
        self.cancel_button.grid(row=0, column=3, padx=5)
        self.empty_dock_button.grid(row=0, column=4, padx=5)
        logging.debug("Widgets created")

    def on_ok(self):
        self.selected_apps = [app for app, var in zip(self.apps, self.vars) if var.get()]
        if not self.selected_apps:
            logging.info("No applications selected, exiting without changes")
            self.selected_apps = None
        else:
            logging.info(f"Selected apps: {self.selected_apps}")
            logging.info(f"Don't Clear Dock: {self.dont_clear_dock.get()}")
        self.destroy()

    def on_cancel(self):
        logging.info("Selection cancelled")
        self.selected_apps = None
        self.destroy()

    def on_empty_dock(self):
        logging.info("Empty Dock selected")
        self.selected_apps = []
        self.destroy()

def clear_dock(user):
    logging.info("Clearing Dock")
    run_command("--remove all", as_user=user)

def add_to_dock(apps, user):
    logging.info(f"Adding {len(apps)} apps to Dock")
    for app in apps:
        app_path = f"/Applications/{app}"
        escaped_path = app_path.replace(" ", r"\ ")
        logging.debug(f"Adding {escaped_path} to Dock")
        try:
            run_command(f"--add {escaped_path}", as_user=user)
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to add {app} to Dock: {e}")
            # Continue with the next app instead of raising an exception
            continue

def main():
    logging.info("Starting Dock Cleaner application")
    try:
        if os.geteuid() != 0:
            raise PermissionError("This script must be run as root.")

        console_user = get_console_user()
        if not console_user:
            raise RuntimeError("No user logged in at the console.")

        logging.info(f"Console user: {console_user}")

        apps = get_applications()
        app_selector = AppSelector(apps)
        app_selector.mainloop()
        selected_apps = app_selector.selected_apps
        dont_clear_dock = app_selector.dont_clear_dock.get()

        if selected_apps is None:
            logging.info("No changes made to the Dock")
        elif len(selected_apps) > 0:
            if not dont_clear_dock:
                logging.info("Clearing dock before adding selected applications")
                clear_dock(console_user)
            logging.info("Adding selected applications to Dock")
            add_to_dock(selected_apps, console_user)
            logging.info("Dock updated successfully")
        else:
            logging.info("Emptying dock")
            clear_dock(console_user)
            logging.info("Dock emptied successfully")

    except Exception as e:
        log_exception(e)
        print(f"An error occurred: {str(e)}")

    logging.info("Dock Cleaner application completed")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_exception(e)
        sys.exit(1)
