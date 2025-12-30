from pathlib import Path

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
