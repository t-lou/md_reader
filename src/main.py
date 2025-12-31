#!/usr/bin/env python3

import argparse
import tkinter as tk
from tkinter import ttk

from .launcher import LibraryLauncher
from .viewer import MarkdownViewerApp

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
# Entry Point
# ============================================================

if __name__ == "__main__":
    print("Starting Markdown Viewer...")

    args = parse_args()
    root = tk.Tk()

    style = ttk.Style()
    style.configure(
        "LeftAligned.TButton",
        anchor="w",  # west = left
        justify="left",  # for multi-line text
        padding=(10, 5),  # optional: add left padding
    )

    if args.folder is not None:
        # Launch viewer with folder
        app = MarkdownViewerApp(root, folder=args.folder)
    else:
        # Show library launcher
        launcher = LibraryLauncher(root)

    root.mainloop()
