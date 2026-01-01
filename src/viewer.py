import logging
import os
import re
import shutil
import tkinter as tk
import webbrowser
from enum import Enum, auto
from tkinter import filedialog, ttk
from typing import Any, Callable, Dict, List, Tuple

from .storage import (
    PATH_STORAGE,
    add_folder_to_library,
    flatten_path,
    gen_init_index_json,
    list_all_files_with_ext,
    pack_folder,
)

# Optional Pillow support for JPEG and others
try:
    from PIL import Image, ImageTk

    PIL_AVAILABLE: bool = True
except ImportError:
    PIL_AVAILABLE = False


# Optional mistune for proper Markdown parsing
try:
    import mistune

    MISTUNE_AVAILABLE: bool = True
except Exception:
    MISTUNE_AVAILABLE = False


# ============================================================
# Inline Markdown Tokenizer
# ============================================================
class TokenType(Enum):
    NORMAL = auto()
    ITALIC = auto()
    BOLD = auto()
    BOLD_ITALIC = auto()
    INLINE_CODE = auto()


link_callbacks: Dict[str, Callable[[Any], Any]] = {}


def on_click(event: Any, url: str) -> None:
    logging.debug(f"will open {url}")
    _ = event  # keep reference to satisfy callback signature
    webbrowser.open_new(url)


def insert_hyperlink(
    text_widget: tk.Text, start_index: str, end_index: str, url: str, callback_store: Dict[str, Callable[[Any], Any]]
) -> None:
    tag_name = f"hyperlink_{len(callback_store)}"
    text_widget.tag_add(tag_name, start_index, end_index)

    # Bind click
    callback_store[tag_name] = lambda e, url=url: on_click(e, url)
    text_widget.tag_bind(tag_name, "<Button-1>", callback_store[tag_name])

    # debugging line, it should not be empty
    logging.debug("Tag ranges:", text_widget.tag_ranges(tag_name))


def tokenize_inline(line: str) -> List[Tuple[TokenType, str]]:
    tokens: List[Tuple[TokenType, str]] = []
    i = 0
    n = len(line)

    while i < n:
        # inline code
        if line.startswith("`", i):
            end = line.find("`", i + 1)
            if end != -1:
                tokens.append((TokenType.INLINE_CODE, line[i + 1 : end]))
                i = end + 1
                continue

        # ***bold italic***
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
def render_markdown_with_mistune(text_widget: tk.Text, content: str, image_cache: List[Any], base_folder: str) -> None:
    try:
        md = mistune.create_markdown(renderer="ast")
        ast = md(content)

        def visit(node: dict) -> None:
            ntype = node.get("type")

            if ntype == "text":
                text_widget.insert(tk.END, node.get("text", ""))
                return

            if ntype == "heading":
                level = node.get("level", 1)
                start = text_widget.index("end-1c")
                for child in node.get("children", []):
                    visit(child)
                end = text_widget.index("end-1c")
                tag = "h1" if level == 1 else "h2" if level == 2 else "h3"
                text_widget.tag_add(tag, start, end)
                text_widget.insert(tk.END, "\n")
                return

            if ntype == "paragraph":
                start = text_widget.index("end-1c")
                for child in node.get("children", []):
                    visit(child)
                end = text_widget.index("end-1c")
                text_widget.insert(tk.END, "\n")
                return

            if ntype == "strong":
                start = text_widget.index("end-1c")
                for child in node.get("children", []):
                    visit(child)
                end = text_widget.index("end-1c")
                text_widget.tag_add("bold", start, end)
                return

            if ntype == "emphasis":
                start = text_widget.index("end-1c")
                for child in node.get("children", []):
                    visit(child)
                end = text_widget.index("end-1c")
                text_widget.tag_add("italic", start, end)
                return

            if ntype == "codespan":
                start = text_widget.index("end-1c")
                text_widget.insert(tk.END, node.get("text", ""))
                end = text_widget.index("end-1c")
                text_widget.tag_add("inlinecode", start, end)
                return

            if ntype == "code":
                text_widget.insert(tk.END, node.get("text", "") + "\n", "codeblock")
                return

            if ntype == "link":
                url = node.get("link") or node.get("href") or ""
                start = text_widget.index("end-1c")
                for child in node.get("children", []):
                    visit(child)
                end = text_widget.index("end-1c")
                text_widget.tag_add("hyperlink", start, end)
                insert_hyperlink(text_widget, start, end, url, link_callbacks)
                return

            if ntype == "image":
                src = node.get("src") or node.get("url") or ""
                # Resolve relative paths
                img_path = src
                if not os.path.isabs(img_path):
                    img_path = os.path.join(base_folder, img_path)
                img_path = os.path.abspath(img_path)

                if os.path.exists(img_path):
                    img = None
                    try:
                        img = tk.PhotoImage(file=img_path)
                    except Exception:
                        img = None
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
                return

            if ntype == "list":
                for item in node.get("children", []):
                    # list_item
                    text_widget.insert(tk.END, "- ")
                    for child in item.get("children", []):
                        visit(child)
                    text_widget.insert(tk.END, "\n")
                return

            # fallback: attempt to visit children
            for child in node.get("children", []):
                visit(child)

        text_widget.config(state="normal")
        text_widget.delete("1.0", tk.END)
        for node in ast:
            visit(node)
        text_widget.config(state="disabled")
        return
    except Exception:
        # fall back to the original renderer on error
        pass


def render_markdown_raw(text_widget: tk.Text, content: str, image_cache: List[Any], base_folder: str) -> None:
    # original simple renderer (fallback)
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

        # ----------------------------------------------------
        # Images: ![alt](path)
        # ----------------------------------------------------
        img_match = re.match(r"!\[.*?\]\((.*?)\)", stripped)
        if img_match:
            img_path = img_match.group(1)

            # Resolve relative paths
            if not os.path.isabs(img_path):
                img_path = os.path.join(base_folder, img_path)

            img_path = os.path.abspath(img_path)

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

        # ----------------------------------------------------
        # Inline links: [text](url)
        # ----------------------------------------------------
        link_pattern = r"\[(.*?)\]\((.*?)\)"
        pos = 0

        for match in re.finditer(link_pattern, line):
            start, end = match.span()
            link_text, url = match.group(1), match.group(2)

            # Insert text before the link
            before = line[pos:start]
            for ttype, text in tokenize_inline(before):
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

            # Insert the link text
            link_start = text_widget.index("end-1c")
            text_widget.insert("end-1c", link_text, "hyperlink")
            link_end = text_widget.index("end-1c")

            insert_hyperlink(text_widget, link_start, link_end, url, callback_store=link_callbacks)

            pos = end

        # Insert remaining text after last link
        remaining = line[pos:]
        for ttype, text in tokenize_inline(remaining):
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
        continue

    text_widget.config(state="disabled")


def render_markdown(text_widget: tk.Text, content: str, image_cache: List[Any], base_folder: str) -> None:
    # If mistune is available, use the AST renderer for robust parsing
    if MISTUNE_AVAILABLE:
        render_markdown_with_mistune(text_widget, content, image_cache, base_folder)
        return
    # Fallback to the raw renderer
    render_markdown_raw(text_widget, content, image_cache, base_folder)


# ============================================================
# Main Application
# ============================================================
class MarkdownViewerApp:
    def __init__(self, root: tk.Tk, folder: str) -> None:
        self.root: tk.Tk = root
        self.folder: str = os.path.abspath(os.path.expanduser(folder))
        self.image_cache: List[Any] = []

        abs_target_path = os.path.join(os.getcwd(), folder)
        root.title(f"Markdown Viewer -- {abs_target_path}")
        root.minsize(1366, 768)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("righttab.TNotebook", tabposition="en")
        style.configure("righttab.TNotebook.Tab", padding=[10, 5], anchor="w")

        # Menu
        menubar = tk.Menu(root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(
            label="Save to file",
            command=lambda: pack_folder(self.folder, str(PATH_STORAGE / (flatten_path(self.folder) + ".mdlz"))),
        )
        file_menu.add_command(
            label="Save to folder",
            command=self.save_to_folder,
        )
        file_menu.add_command(
            label="Init Index",
            command=lambda: gen_init_index_json(self.folder),
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

        self.notebook = ttk.Notebook(root, style="righttab.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        self.load_markdown_files()

    def save_to_folder(self) -> None:
        """Open a dialog to select a directory and copy the current folder to it."""
        target_dir = filedialog.askdirectory(title="Select destination folder")
        if target_dir:
            try:
                shutil.copytree(self.folder, target_dir, dirs_exist_ok=True)
                logging.info(f"Successfully copied {self.folder} to {target_dir}")
            except Exception as e:
                logging.error(f"Error copying folder: {e}")

        self.folder = target_dir
        add_folder_to_library(self.folder)

    def normalize_path(self, path: str) -> str:
        rel: str = os.path.relpath(path, self.folder)
        return rel.replace(os.sep, "/")

    def load_markdown_files(self) -> None:
        md_files = list_all_files_with_ext(self.folder, "md")

        for md_path in md_files:
            tab = ttk.Frame(self.notebook)
            label = self.normalize_path(md_path)
            self.notebook.add(tab, text=label)

            # container frame for text + scrollbar
            frame = ttk.Frame(tab)
            frame.pack(fill="both", expand=True)

            text_widget = tk.Text(frame, wrap="word")
            text_widget.pack(side="left", fill="both", expand=True)

            scrollbar = ttk.Scrollbar(frame, command=text_widget.yview)
            scrollbar.pack(side="right", fill="y")
            text_widget.configure(yscrollcommand=scrollbar.set)

            # fonts
            text_widget.tag_config("h1", font=("DejaVu Sans", 20, "bold"))
            text_widget.tag_config("h2", font=("DejaVu Sans", 16, "bold"))
            text_widget.tag_config("h3", font=("DejaVu Sans", 14, "bold"))
            text_widget.tag_config("bold", font=("DejaVu Sans", 12, "bold"))
            text_widget.tag_config("italic", font=("DejaVu Sans", 12, "italic"))
            text_widget.tag_config("bold_italic", font=("Arial", 12, "bold", "italic"))
            text_widget.tag_config("inlinecode", font=("Courier", 11), background="#707070", foreground="#90ee90")
            text_widget.tag_config("codeblock", font=("Courier", 11), background="#707070", foreground="#90ee90")
            text_widget.tag_config("hyperlink", foreground="blue", underline=True)

            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()

            render_markdown(text_widget, content, self.image_cache, self.folder)
