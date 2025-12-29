#!/usr/bin/env python3

import argparse
import glob
import os
import tkinter as tk
from enum import Enum, auto
from tkinter import ttk

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


def render_markdown(text_widget, content, image_cache):
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

        root.title("Markdown Viewer")
        root.minsize(800, 600)

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

            render_markdown(text_widget, content, self.image_cache)


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
    app = MarkdownViewerApp(root, folder=args.folder)
    root.mainloop()
