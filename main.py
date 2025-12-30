#!/usr/bin/env python3

import argparse
import glob
import os
import re
import tkinter as tk
from enum import Enum, auto
from tkinter import ttk

# Try to import Pillow (optional)
try:
    from PIL import Image, ImageTk

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ============================================================
# Tokenizer for inline markdown
# ============================================================


class TokenType(Enum):
    NORMAL = auto()
    ITALIC = auto()
    BOLD = auto()
    BOLD_ITALIC = auto()
    INLINE_CODE = auto()


def tokenize_inline(line: str):
    tokens = []
    i = 0
    n = len(line)

    while i < n:
        # inline code: `code`
        if line.startswith("`", i):
            end = line.find("`", i + 1)
            if end != -1:
                tokens.append((TokenType.INLINE_CODE, line[i + 1 : end]))
                i = end + 1
                continue

        # ***bold+italic***
        if line.startswith("***", i):
            end = line.find("***", i + 3)
            if end != -1:
                tokens.append((TokenType.BOLD_ITALIC, line[i + 3 : end]))
                i = end + 3
                continue

        # **bold**
        if line.startswith("**", i):
            end = line.find("**", i + 2)
            if end != -1:
                tokens.append((TokenType.BOLD, line[i + 2 : end]))
                i = end + 2
                continue

        # *italic*
        if line.startswith("*", i):
            end = line.find("*", i + 1)
            if end != -1:
                tokens.append((TokenType.ITALIC, line[i + 1 : end]))
                i = end + 1
                continue

        # normal char
        tokens.append((TokenType.NORMAL, line[i]))
        i += 1

    return tokens


# ============================================================
# Markdown Renderer
# ============================================================


def render_markdown(text_widget, content, image_cache, base_folder):
    text_widget.config(state="normal")
    text_widget.delete("1.0", tk.END)

    lines = content.split("\n")
    in_code_block = False

    for line in lines:
        stripped = line.strip()

        # fenced code block
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            text_widget.insert(tk.END, "\n", "codeblock")
            continue

        if in_code_block:
            text_widget.insert(tk.END, line + "\n", "codeblock")
            continue

        # -----------------------------
        # Images: ![alt](path)
        # -----------------------------
        img_match = re.match(r"!\[.*?\]\((.*?)\)", stripped)

        if img_match:
            img_path = img_match.group(1)

            # Resolve relative paths
            if not os.path.isabs(img_path):
                img_path = os.path.join(base_folder, img_path)

            if os.path.exists(img_path):
                img = None

                # Try Tkinter PhotoImage (PNG/GIF)
                try:
                    img = tk.PhotoImage(file=img_path)
                except Exception:
                    img = None

                # Try Pillow for JPEG and others
                if img is None and PIL_AVAILABLE:
                    try:
                        pil_img = Image.open(img_path)
                        img = ImageTk.PhotoImage(pil_img)
                    except Exception:
                        img = None

                if img is not None:
                    image_cache.append(img)
                    text_widget.image_create(tk.END, image=img)
                else:
                    text_widget.insert(tk.END, f"[Unsupported image format: {img_path}]\n")
            else:
                text_widget.insert(tk.END, f"[Image not found: {img_path}]\n")

            text_widget.insert(tk.END, "\n")
            continue

        # headings
        if stripped.startswith("# "):
            text_widget.insert(tk.END, stripped[2:] + "\n", "h1")
            continue
        if stripped.startswith("## "):
            text_widget.insert(tk.END, stripped[3:] + "\n", "h2")
            continue
        if stripped.startswith("### "):
            text_widget.insert(tk.END, stripped[4:] + "\n", "h3")
            continue

        # inline formatting
        tokens = tokenize_inline(line)
        for ttype, text in tokens:
            if ttype == TokenType.NORMAL:
                text_widget.insert(tk.END, text)
            elif ttype == TokenType.ITALIC:
                text_widget.insert(tk.END, text, "italic")
            elif ttype == TokenType.BOLD:
                text_widget.insert(tk.END, text, "bold")
            elif ttype == TokenType.BOLD_ITALIC:
                text_widget.insert(tk.END, text, ("bold", "italic"))
            elif ttype == TokenType.INLINE_CODE:
                text_widget.insert(tk.END, text, "inlinecode")

        text_widget.insert(tk.END, "\n")

    text_widget.config(state="disabled")


# ============================================================
# Main App
# ============================================================


class MarkdownViewerApp:
    def __init__(self, root, folder):
        self.root = root
        self.folder = os.path.abspath(os.path.expanduser(folder))
        self.image_cache = []

        style = ttk.Style()
        style.configure("righttab.TNotebook", tabposition="en")
        style.configure("righttab.TNotebook.Tab", padding=[10, 5], anchor="w")

        self.notebook = ttk.Notebook(root, style="righttab.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        self.load_markdown_files()

    def normalize_path(self, path):
        rel = os.path.relpath(path, self.folder)
        return rel.replace(os.sep, "/")

    def load_markdown_files(self):
        md_files = glob.glob(os.path.join(self.folder, "**/*.md"), recursive=True)

        for md_path in sorted(md_files):
            tab = ttk.Frame(self.notebook)
            label = self.normalize_path(md_path)
            self.notebook.add(tab, text=label)

            # container frame for text + scrollbar
            content_frame = ttk.Frame(tab)
            content_frame.pack(fill="both", expand=True)

            text_widget = tk.Text(content_frame, wrap="word")
            text_widget.pack(side="left", fill="both", expand=True)

            scrollbar = ttk.Scrollbar(content_frame, command=text_widget.yview)
            scrollbar.pack(side="right", fill="y")

            text_widget.configure(yscrollcommand=scrollbar.set)

            # styles
            text_widget.tag_config("h1", font=("Arial", 20, "bold"))
            text_widget.tag_config("h2", font=("Arial", 16, "bold"))
            text_widget.tag_config("h3", font=("Arial", 14, "bold"))
            text_widget.tag_config("bold", font=("Arial", 12, "bold"))
            text_widget.tag_config("italic", font=("Arial", 12, "italic"))
            text_widget.tag_config("inlinecode", font=("Courier", 11), background="#e8e8e8")
            text_widget.tag_config("codeblock", font=("Courier", 11), background="#f0f0f0")

            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()

            render_markdown(text_widget, content, self.image_cache, base_folder=self.folder)


# ============================================================
# CLI
# ============================================================


def parse_args():
    parser = argparse.ArgumentParser(description="Markdown Viewer")
    parser.add_argument("folder", nargs="?", default=".", help="Folder to scan for markdown files")
    return parser.parse_args()


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    args = parse_args()
    root = tk.Tk()
    root.geometry("1280x960")
    root.title(f"Markdown Viewer -- {args.folder}")
    app = MarkdownViewerApp(root, folder=args.folder)
    root.mainloop()
