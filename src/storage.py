"""Utilities for packing/unpacking and storing markdown library archives.

This module provides helpers to create `.mdlz` archives (zip files),
list stored archives, and convert absolute paths into a safe filename
representation used for storage.
"""

from __future__ import annotations

import glob
import json
import logging
import os
import re
import tempfile
import zipfile
from pathlib import Path, PureWindowsPath
from typing import List, Union

EXTENSION = "mdlz"
PATH_STORAGE = Path(__file__).parent.parent / "storage"
PATH_LIBRARY = Path(__file__).parent.parent / "library.json"
DEFAULT_LIBRARY_STRUCTURE = {"folders": []}

if not PATH_STORAGE.exists():
    PATH_STORAGE.mkdir(parents=True, exist_ok=True)

if not PATH_LIBRARY.exists():
    with open(PATH_LIBRARY, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_LIBRARY_STRUCTURE, f, indent=4)


def _is_absolute_path(path: str) -> bool:
    """Return True if ``path`` is an absolute path on Windows or Unix.

    This accepts Unix-style roots ('/...') and Windows drive prefixes
    like 'C:\\' or 'C:/' as absolute.
    """
    # Unix absolute
    if path.startswith("/"):
        return True

    # Windows absolute: C:\ or C:/
    if re.match(r"^[A-Za-z]:[\\\\/]", path):
        return True

    return False


def flatten_path(path_str: str) -> str:
    """Convert an absolute path into a safe single-token filename.

    Examples:
    - ``C:\\Users\\me\\Docs`` -> ``C_Users_me_Docs``
    - ``/mnt/hdd1/docs`` -> ``mnt_hdd1_docs``

    Raises ``ValueError`` if ``path_str`` is not absolute.
    """
    if not _is_absolute_path(path_str):
        raise ValueError(f"Path must be absolute: {path_str}")

    # If the string is a Windows drive-style path (e.g. C:\ or C:/), parse
    # it with PureWindowsPath so the drive root and path components are
    # recognized consistently on all platforms.
    if re.match(r"^[A-Za-z]:[\\\\/]", path_str):
        parts = list(PureWindowsPath(path_str).parts)
    else:
        parts = list(Path(path_str).parts)

    # Remove root markers like "/" or "\\" or "C:\\"
    # Windows: ('C:\\', 'Users', 'anoth', 'Documents')
    # Linux:   ('/', 'mnt', 'hdd1', 'docs')
    cleaned: List[str] = []

    for part in parts:
        # Windows drive root like "C:\\"
        if part.endswith(":\\") or part.endswith(":/"):
            cleaned.append(part.rstrip("\\/").rstrip(":"))
        # Linux root "/"
        elif part in ("/", "\\"):
            continue
        else:
            cleaned.append(part)

    return "_".join(cleaned)


def is_mdlz_file(file_path: str) -> bool:
    """Return True if ``file_path`` ends with the `.mdlz` extension.

    The check is case-insensitive.
    """
    return file_path.lower().endswith(EXTENSION)


def unpack_file(zip_path: Union[str, Path], extract_to: Union[str, Path]) -> None:
    """Unpack the zip archive at ``zip_path`` into ``extract_to``.

    Both ``zip_path`` and ``extract_to`` may be strings or `Path`.
    """
    zip_path = os.path.abspath(str(zip_path))
    extract_to = os.path.abspath(str(extract_to))

    os.makedirs(extract_to, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zipf:
        zipf.extractall(extract_to)

    logging.debug(f"Extracted '{zip_path}' → '{extract_to}'")


def pack_folder(folder_path: Union[str, Path], zip_path: Union[str, Path]) -> None:
    """Compress ``folder_path`` into a zip archive at ``zip_path``.

    ``folder_path`` may be a directory path; the archive will contain the
    folder's files with relative paths.
    """
    folder_path = os.path.abspath(str(folder_path))

    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                abs_file = os.path.join(root, file)
                rel_path = os.path.relpath(abs_file, folder_path)
                zipf.write(abs_file, rel_path)

    logging.debug(f"Compressed '{folder_path}' → '{zip_path}'")


def unpack_file_to_temp(zip_path: Union[str, Path]) -> str:
    """Unpack ``zip_path`` into a newly-created temporary directory.

    Returns the path to the temporary directory as a string. Caller is
    responsible for cleaning it up.
    """
    zip_path = os.path.abspath(str(zip_path))

    # stays alive until YOU delete it, the files should be small, good luck
    extract_to = tempfile.mkdtemp()

    with zipfile.ZipFile(zip_path, "r") as zipf:
        zipf.extractall(extract_to)

    return extract_to


def load_library_data() -> dict:
    """Load the library data from PATH_LIBRARY.

    If the file does not exist, returns an empty library structure.
    """
    if not PATH_LIBRARY.exists():
        return DEFAULT_LIBRARY_STRUCTURE

    try:
        with open(PATH_LIBRARY, "r", encoding="utf-8") as f:
            library_data = json.load(f)
        return library_data
    except Exception as e:
        logging.error(f"Error loading library.json: {e}")
        return DEFAULT_LIBRARY_STRUCTURE


def add_folder_to_library(folder: str) -> None:
    """Add a folder path to the library.json file.

    If the folder is already present, it will not be added again.
    """
    library_data = load_library_data()

    if folder not in library_data.get("folders", []):
        library_data.setdefault("folders", []).append(folder)
        with open(PATH_LIBRARY, "w", encoding="utf-8") as wf:
            json.dump(library_data, wf, indent=4)


def list_all_files_with_ext(folder_path: Union[str, Path], ext: str) -> List[Path]:
    """Recursively list all files in the specified folder with given extension.

    Returns a list of `Path` objects.
    """
    logging.debug(f"Listing all .{ext} files in folder: {folder_path}")
    files = glob.glob(str(Path(folder_path) / f"**/*.{ext}"), recursive=True)
    return sorted([Path(f) for f in files])


def gen_init_index_json(path_to_folder: Union[str, Path]) -> None:
    """Generate an initial index.json file in the specified folder.

    The index.json will contain an empty list of entries.
    """
    if not _is_absolute_path(str(path_to_folder)):
        raise ValueError(f"Path must be absolute: {path_to_folder}")

    # Ensure we operate on a string path and create JSON-serializable entries
    path_to_folder = str(path_to_folder)
    index_path = os.path.join(path_to_folder, "index.json")

    entries = [str(p) for p in list_all_files_with_ext(path_to_folder, "md")]
    initial_index = {"entries": entries}

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(initial_index, f, indent=4)

    logging.debug(f"Generated initial index.json at '{index_path}'")


def clean_non_existing_folders_from_library() -> None:
    """Remove non-existing folder paths from the library.json file."""
    library_data = load_library_data()
    folders = library_data.get("folders", [])
    existing_folders = [f for f in folders if Path(f).exists()]

    if len(existing_folders) != len(folders):
        library_data["folders"] = existing_folders
        with open(PATH_LIBRARY, "w", encoding="utf-8") as wf:
            json.dump(library_data, wf, indent=4)
        logging.debug("Cleaned non-existing folders from library.json")
