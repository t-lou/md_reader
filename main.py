#!/usr/bin/env python3

import glob
import os
import tkinter as tk
from enum import Enum, auto
from tkinter import ttk


# ---------------------------------------------------------
# Token types for font styling in text
# ---------------------------------------------------------
class TokenType(Enum):
    NORMAL = auto()
    ITALIC = auto()
    BOLD = auto()
    BOLD_ITALIC = auto()


def tokenize_inline_markdown(line: str):
    tokens = []
    i = 0
    n = len(line)

    while i < n:
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

        # Normal text (single character)
        tokens.append((TokenType.NORMAL, line[i]))
        i += 1

    return tokens


# ---------------------------------------------------------
# Simple Markdown Renderer for Tkinter Text widget
# ---------------------------------------------------------


def render_markdown(text_widget, content, image_cache):
    text_widget.config(state="normal")
    text_widget.delete("1.0", tk.END)

    lines = content.split("\n")
    in_code_block = False

    for line in lines:
        # -----------------------------
        # Code block start/end
        # -----------------------------
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            if in_code_block:
                text_widget.insert(tk.END, "\n", "codeblock")
            else:
                text_widget.insert(tk.END, "\n")
            continue

        if in_code_block:
            text_widget.insert(tk.END, line + "\n", "codeblock")
            continue

        # -----------------------------
        # Headings
        # -----------------------------
        if line.startswith("# "):
            text_widget.insert(tk.END, line[2:] + "\n", "h1")
            continue
        elif line.startswith("## "):
            text_widget.insert(tk.END, line[3:] + "\n", "h2")
            continue
        elif line.startswith("### "):
            text_widget.insert(tk.END, line[4:] + "\n", "h3")
            continue

        # -----------------------------
        # Images: ![alt](path)
        # -----------------------------
        #         img_match = re.match(r"!

        # \[.*?\]

        # \((.*?)\)", line.strip())
        #         if img_match:
        #             img_path = img_match.group(1)
        #             if os.path.exists(img_path):
        #                 try:
        #                     img = PhotoImage(file=img_path)
        #                     image_cache.append(img)  # prevent garbage collection
        #                     text_widget.image_create(tk.END, image=img)
        #                 except Exception as e:
        #                     text_widget.insert(tk.END, f"[Image load error: {e}]\n")
        #             else:
        #                 text_widget.insert(tk.END, f"[Image not found: {img_path}]\n")
        #             text_widget.insert(tk.END, "\n")
        #             continue

        # -----------------------------
        # Bold and italic
        # -----------------------------
        tokens = tokenize_inline_markdown(line)
        for ttype, text in tokens:
            if ttype == TokenType.NORMAL:
                text_widget.insert(tk.END, text)
            elif ttype == TokenType.ITALIC:
                text_widget.insert(tk.END, text, "italic")
            elif ttype == TokenType.BOLD:
                text_widget.insert(tk.END, text, "bold")
            elif ttype == TokenType.BOLD_ITALIC:
                text_widget.insert(tk.END, text, ("bold", "italic"))

        text_widget.insert(tk.END, "\n")

    text_widget.config(state="disabled")


# ---------------------------------------------------------
# Main App
# ---------------------------------------------------------


class MarkdownViewerApp:
    def __init__(self, root, folder):
        self.root = root
        self.folder = folder
        self.image_cache = []  # prevent image GC

        root.title("Markdown Viewer Prototype")

        # Notebook with tabs on the left
        style = ttk.Style()
        style.configure("lefttab.TNotebook", tabposition="wn")

        self.notebook = ttk.Notebook(root, style="lefttab.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        self.load_markdown_files()

    def load_markdown_files(self):
        md_files = sorted(glob.glob(os.path.join(self.folder, "**/*.md"), recursive=True))

        def _normalize_path(path):
            rel = os.path.relpath(path, self.folder)
            return rel.replace(os.sep, "/")

        for md_path in md_files:
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=_normalize_path(md_path))

            text_widget = tk.Text(tab, wrap="word")
            text_widget.pack(fill="both", expand=True)

            # Define styles
            text_widget.tag_config("h1", font=("Arial", 20, "bold"))
            text_widget.tag_config("h2", font=("Arial", 16, "bold"))
            text_widget.tag_config("h3", font=("Arial", 14, "bold"))
            text_widget.tag_config("bold", font=("Arial", 12, "bold"))
            text_widget.tag_config("italic", font=("Arial", 12, "italic"))
            text_widget.tag_config("codeblock", background="#f0f0f0", font=("Courier", 11))

            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()

            render_markdown(text_widget, content, self.image_cache)


# ---------------------------------------------------------
# Run the app
# ---------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = MarkdownViewerApp(root, folder="./example_folder")
    root.mainloop()
