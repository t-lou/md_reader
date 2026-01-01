#!/usr/bin/env python3

import logging
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from .storage import (
    EXTENSION,
    PATH_STORAGE,
    add_folder_to_library,
    clean_non_existing_folders_from_library,
    load_library_data,
    unpack_file_to_temp,
)


# ============================================================
# Library Launcher GUI
# ============================================================
class LibraryLauncher:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Markdown Viewer - Library")
        self.root.geometry("390x844")

        # Main frame with scrollbar
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(main_frame, text="Select a Doc:", font=("DejaVu Sans", 12, "bold")).pack(anchor="w", pady=(0, 10))

        # Canvas + Scrollbar for button stack
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # update scrollregion when inner frame changes
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        # create a window on the canvas and keep its id so we can
        # make the inner frame match the canvas width on resize
        self._canvas_window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # make inner frame width follow canvas width so children (buttons)
        # can expand to fill horizontally
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(self._canvas_window_id, width=e.width))

        # Directory picker button (fill full width)
        ttk.Button(
            scrollable_frame,
            text="Open Directory...",
            command=self.on_open_directory,
        ).pack(fill="x", pady=5, padx=6, expand=True)

        # List the saved folders from library.json
        clean_non_existing_folders_from_library()
        library_data = load_library_data()
        for entry_path in library_data.get("folders", []):
            ttk.Button(
                scrollable_frame,
                text=entry_path,
                style="LeftAligned.TButton",
                command=lambda p=entry_path: self.open_folder(p),
            ).pack(fill="x", pady=5, padx=6, expand=True)

        # List the saved files
        all_saved_files = [p for p in PATH_STORAGE.iterdir() if p.is_file() and p.suffix == EXTENSION]
        for entry_path in all_saved_files:
            ttk.Button(
                scrollable_frame,
                text=entry_path.stem,
                style="LeftAligned.TButton",
                command=lambda p=entry_path: self.open_saved_file(p),
            ).pack(fill="x", pady=5, padx=6, expand=True)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def open_saved_file(self, file_path: Path) -> None:
        folder = unpack_file_to_temp(file_path)
        logging.info(f"Will open in temporary folders {folder}")
        self.open_folder(folder)

    def on_open_directory(self) -> None:
        folder = filedialog.askdirectory(title="Select Markdown Folder")
        if folder:
            self.open_folder(folder)
            add_folder_to_library(folder)

    def open_folder(self, folder: str) -> None:
        # Restart the app with the folder argument
        if not Path(folder).exists():
            logging.error(f"Folder does not exist: {folder}")
            raise FileNotFoundError(f"Folder does not exist: {folder}")

        subprocess.Popen([sys.executable, "-m", "src.main", folder])
        self.root.quit()
