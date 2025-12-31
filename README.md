# 📘 **Markdown Reader (Tkinter‑based)**

A lightweight, cross‑platform Markdown viewer built entirely with **standard Python libraries** — no external dependencies required.  
It recursively loads all `*.md` files from a given folder (or unpacks and displays them from a compressed `.mdlz` archive) and displays each file in its own tab.

This tool is ideal for quickly browsing notes, documentation, research logs, and learning materials (e.g., copied Q&A from Copilot or Gemini) without installing heavy editors or requiring external software.

---

## ✨ Features

- **Pure Python + Tkinter** — no external packages needed  
- **Folder support**: recursively scan all `*.md` files from any directory  
- **Compressed archive support**: open saved `.mdlz` archives (ZIP format) containing markdown files  
- **Library launcher**: save frequently-used folders and archives for quick access  
- **One tab per file**, with paths shown relative to the chosen folder  
- **Markdown rendering**, including:
  - `#`, `##`, `###` headings  
  - *italic*, **bold**, and ***bold+italic***  
  - Inline code `` `like this` ``  
  - Fenced code blocks  
  - Links (click to open in browser)  
  - Images (if they exist relative to the markdown)  
- **Resizable window** with auto-expanding buttons, scrollable content  
- **Cross‑platform** (Linux, macOS, Windows)  
- **Command‑line folder or archive path selection**  

---Launch from the md_reader directory (or use the run.bash/run.bat):

```bash
cd md_reader
python -m src.main
```

This opens the **Library Launcher** GUI where you can:
- Click **"Open Directory..."** to select a markdown folder
- Click a saved folder/archive button to open it directly
- Add one new folder to your library

### Open a specific folder from the command line:

```bash
cd md_reader
python -m src.main ./example_folder
```

It will scan all `*.md` files recursively and use the folder as the base path for images.

Example output:

![example1](misc/test_example.png)

The archive will be extracted to a temporary directory and displayed. The folder path is auto-detected from the archive filename.

### Compress a folder into an archive:

Use the **"Save"** option in the File menu (or manually call the save function) to create a `.mdlz` archive of the current folder for portable sharing and storage.

---

## 📂 Folder Structure

All markdown files under the chosen folder are discovered recursively:

```
notes/
├── intro.md
├── chapter1/
│   └── overview.md
└── appendix/
    └── references.md
```

Tabs will appear as:

```
intro.md
chapter1/overview.md
appendix/references.md
```

Paths are normalized to use forward slashes for consistency across platforms.

If a reordering or selection of the files is needed, a index.json can be helpful.

---

## 📝 Supported Markdown Syntax

### Headings

```
# Heading 1
## Heading 2
### Heading 3
```

### Inline formatting

```
*italic*
**bold**
***bold and italic***
`inline code`
```

### Code blocks

```
def hello():
    print("Hello")
```

```
![alt text](path/to/image.png)
```

Image parsing is implemented but disabled until the feature is finalized.

---

## 🧩 Implementation Notes

- The UI uses a `ttk.Notebook` with tabs on the **right** for better alignment.
- Each tab contains a `Text` widget with a vertical scrollbar.
- Markdown is rendered using a small custom tokenizer (no external parser).
- Inline formatting is handled via Tkinter text tags.
- The code is intentionally simple and hackable — ideal for extending.

---

## 🛠 Requirements

- Python 3.8+
- Tkinter (included with most Python installations)

No external libraries required.

---

## 📌 Roadmap

- [ ] Image rendering (PNG/GIF first, optional JPEG via Pillow)  
- [ ] Tree‑view sidebar instead of Notebook tabs  
- [ ] Dark mode  
- [ ] Search inside markdown  
- [ ] Auto‑reload on file changes  
- [ ] Split‑view comparison mode  
