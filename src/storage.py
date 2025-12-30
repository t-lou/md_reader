import logging
import os
import re
import tempfile
import zipfile
from pathlib import Path

EXTENSION = ".mdlz"
PATH_STORAGE = Path(__file__).parent.parent / "storage"


def _is_absolute_path(path: str) -> bool:
    # Unix absolute
    if path.startswith("/"):
        return True

    # Windows absolute: C:\ or C:/
    if re.match(r"^[A-Za-z]:[\\/]", path):
        return True

    return False


def flatten_path(path_str: str) -> str:
    if not _is_absolute_path(path_str):
        raise ValueError(f"Path must be absolute: {path_str}")

    parts = list(Path(path_str).parts)

    # Remove root markers like "/" or "\" or "C:\"
    # Windows: ('C:\\', 'Users', 'anoth', 'Documents')
    # Linux:   ('/', 'mnt', 'hdd1', 'docs')
    cleaned = []

    for part in parts:
        # Windows drive root like "C:\"
        if part.endswith(":\\") or part.endswith(":/"):
            cleaned.append(part.rstrip("\\/").rstrip(":"))
        # Linux root "/"
        elif part in ("/", "\\"):
            continue
        else:
            cleaned.append(part)

    return "_".join(cleaned)


def is_mdlz_file(file_path):
    return file_path.lower().endswith(EXTENSION)


def list_mdlz_files():
    mdlz_files = []
    for item in PATH_STORAGE.iterdir():
        if item.is_file() and item.suffix == EXTENSION:
            mdlz_files.append(item)
    return mdlz_files


def to_mdlz_filename(folder_path):
    base_name = os.path.basename(os.path.normpath(folder_path))
    return f"{base_name}{EXTENSION}"


def unpack_file(zip_path, extract_to):
    zip_path = os.path.abspath(zip_path)
    extract_to = os.path.abspath(extract_to)

    os.makedirs(extract_to, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zipf:
        zipf.extractall(extract_to)

    logging.debug(f"Extracted '{zip_path}' → '{extract_to}'")


def pack_folder(folder_path, zip_path):
    folder_path = os.path.abspath(folder_path)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                abs_file = os.path.join(root, file)
                rel_path = os.path.relpath(abs_file, folder_path)
                zipf.write(abs_file, rel_path)

    logging.debug(f"Compressed '{folder_path}' → '{zip_path}'")


def unpack_file_to_temp(zip_path):
    zip_path = os.path.abspath(zip_path)

    # stays alive until YOU delete it, the files should be small, good luck
    extract_to = tempfile.mkdtemp()

    with zipfile.ZipFile(zip_path, "r") as zipf:
        zipf.extractall(extract_to)

    return extract_to
