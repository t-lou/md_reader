import shutil
import zipfile
from pathlib import Path

import pytest

from src import storage
from src.storage import flatten_path
import json


@pytest.mark.parametrize(
    "input_path, expected",
    [
        # Windows-style absolute paths
        ("C:\\Users\\admin\\Documents", "C_Users_admin_Documents"),
        ("C:/Users/admin/Documents", "C_Users_admin_Documents"),
        ("C:\\Users\\admin\\Documents\\", "C_Users_admin_Documents"),
        # Windows drive root
        ("C:\\", "C"),
        ("D:/", "D"),
        # Linux-style absolute paths
        ("/mnt/hdd1/docs", "mnt_hdd1_docs"),
        ("/mnt/hdd1/docs/", "mnt_hdd1_docs"),
        ("/", ""),  # root becomes empty
        # Mixed separators
        ("C:/Users\\admin/mixed\\path", "C_Users_admin_mixed_path"),
    ],
)
def test_flatten_path(input_path, expected):
    result = flatten_path(input_path)
    assert result == expected


@pytest.mark.parametrize(
    "relative_path",
    [
        "relative",
        "relative/path",
        "folder/subfolder",
        "./something",
        "../parent",
        "../parent/child",
        "C:relative",  # Windows-style relative
        "C:folder\\file",  # Windows-style relative with backslashes
        "",  # empty path
        ".",  # current directory
        "..",  # parent directory
    ],
)
def test_flatten_path_relative(relative_path):
    with pytest.raises(Exception):
        flatten_path(relative_path)


def test_list_mdlz_files_respects_path_storage(tmp_path, monkeypatch):
    fake_storage = tmp_path / "storage"
    fake_storage.mkdir()

    (fake_storage / "one.mdlz").write_text("x")
    (fake_storage / "two.MDLZ").write_text("y")
    (fake_storage / "three.txt").write_text("z")

    monkeypatch.setattr(storage, "PATH_STORAGE", fake_storage)

    files = storage.list_mdlz_files()
    # list_mdlz_files uses Path.suffix == EXTENSION (case-sensitive), so
    # only the lower-case .mdlz file should be returned
    names = {p.name for p in files}
    assert "one.mdlz" in names
    assert "two.MDLZ" not in names
    assert "three.txt" not in names


def test_pack_and_unpack_folder(tmp_path):
    # create a folder with nested files
    src_folder = tmp_path / "orig"
    src_folder.mkdir()
    (src_folder / "a.txt").write_text("hello")
    sub = src_folder / "subdir"
    sub.mkdir()
    (sub / "b.md").write_text("world")

    zip_path = tmp_path / "out.mdlz"

    storage.pack_folder(str(src_folder), str(zip_path))
    assert zip_path.exists()

    # inspect zip contents
    with zipfile.ZipFile(str(zip_path), "r") as zf:
        names = zf.namelist()
    assert any("a.txt" in n for n in names)
    assert any("subdir" in n for n in names)

    # unpack to a new folder
    extract_to = tmp_path / "extracted"
    storage.unpack_file(str(zip_path), str(extract_to))
    assert (extract_to / "a.txt").read_text() == "hello"
    assert (extract_to / "subdir" / "b.md").read_text() == "world"


def test_unpack_file_to_temp_and_cleanup(tmp_path):
    # create a small zip to test unpack_file_to_temp
    src_folder = tmp_path / "s"
    src_folder.mkdir()
    (src_folder / "f.txt").write_text("data")

    zip_path = tmp_path / "z.mdlz"
    storage.pack_folder(str(src_folder), str(zip_path))

    tempdir = storage.unpack_file_to_temp(str(zip_path))
    try:
        assert Path(tempdir).exists()
        assert (Path(tempdir) / "f.txt").read_text() == "data"
    finally:
        # cleanup the temporary directory created by the function
        shutil.rmtree(tempdir, ignore_errors=True)


def test_load_library_data_and_add_folder(tmp_path, monkeypatch):
    fake_lib = tmp_path / "library.json"

    # Ensure we are not touching the project's real library.json
    monkeypatch.setattr(storage, "PATH_LIBRARY", fake_lib)

    # When file does not exist, load_library_data should return default
    if fake_lib.exists():
        fake_lib.unlink()

    data = storage.load_library_data()
    assert data == storage.DEFAULT_LIBRARY_STRUCTURE

    # Add a folder and verify it is written
    folder = "/home/user/docs"
    storage.add_folder_to_library(folder)

    assert fake_lib.exists()
    written = json.loads(fake_lib.read_text(encoding="utf-8"))
    assert folder in written.get("folders", [])

    # Adding the same folder again should not duplicate
    storage.add_folder_to_library(folder)
    written2 = json.loads(fake_lib.read_text(encoding="utf-8"))
    assert written2.get("folders", []).count(folder) == 1
