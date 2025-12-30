import pytest

from src.storage import flatten_path


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
