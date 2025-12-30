#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from src.viewer import MarkdownViewerApp

# ============================================================
# CLI
# ============================================================


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Markdown Viewer")
    parser.add_argument(
        "folder",
        nargs="?",
        default=None,
        help="Folder to scan for markdown files. If there is no index.json, all md files will be loaded and sorted.",
    )
    return parser.parse_args()


# ============================================================
# Library Launcher GUI
# ============================================================


class LibraryLauncher:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Markdown Viewer - Library")
        self.root.geometry("400x300")

        # Main frame with scrollbar
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(main_frame, text="Select a folder:", font=("DejaVu Sans", 12, "bold")).pack(anchor="w", pady=(0, 10))

        # Canvas + Scrollbar for button stack
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Directory picker button
        ttk.Button(
            scrollable_frame,
            text="Open Directory...",
            command=self.on_open_directory,
        ).pack(fill="x", pady=5)

        # Load library entries
        library_path = Path(__file__).parent / "library.json"
        self.library_path = library_path

        if not library_path.exists():
            with open(library_path, "w", encoding="utf-8") as f:
                json.dump({"folders": []}, f, indent=4)
        try:
            with open(library_path, "r", encoding="utf-8") as f:
                library_data = json.load(f)
            entries = library_data.get("folders", [])
            for entry_path in entries:
                ttk.Button(
                    scrollable_frame,
                    text=entry_path,
                    command=lambda p=entry_path: self.open_folder(p),
                ).pack(fill="x", pady=5)
        except Exception as e:
            print(f"Error loading library.json: {e}")

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def on_open_directory(self) -> None:
        folder = filedialog.askdirectory(title="Select Markdown Folder")
        if folder:
            self.open_folder(folder)

            with open(self.library_path, "r", encoding="utf-8") as f:
                self.library_data = json.load(f)

                if folder not in self.library_data.get("folders", []):
                    self.library_data.setdefault("folders", []).append(folder)
                    with open(self.library_path, "w", encoding="utf-8") as wf:
                        json.dump(self.library_data, wf, indent=4)

    def open_folder(self, folder: str) -> None:
        # Restart the app with the folder argument
        subprocess.Popen([sys.executable, __file__, folder])
        self.root.quit()


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    args = parse_args()
    root = tk.Tk()

    if args.folder is not None:
        # Launch viewer with folder
        app = MarkdownViewerApp(root, folder=args.folder)
    else:
        # Show library launcher
        launcher = LibraryLauncher(root)

    root.mainloop()
