import sys
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from lmod_manager import main

TEST_DATA = Path("tests/data")


def test_noarg(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", [""])
    assert main() == 2


def test_install_noarg(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["", "install"])
    with pytest.raises(SystemExit):
        main()


def test_install_file_not_found(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["", "install", "foo"])
    assert main() == 'file "foo" not found'


def test_install_lmod_directory_not_found(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    directory = tmp_path / "lmod"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "",
            "install",
            "-l",
            str(directory),
            "-i",
            str(tmp_path),
            str(TEST_DATA / "spark-pro-22.1-x86_64-linux-bin.tar.gz"),
        ],
    )
    assert main() == f'directory "{directory}" not found'


def test_install_installation_directory_not_found(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    directory = tmp_path / "install"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "",
            "install",
            "-l",
            str(tmp_path),
            "-i",
            str(directory),
            str(TEST_DATA / "spark-pro-22.1-x86_64-linux-bin.tar.gz"),
        ],
    )
    assert main() == f'directory "{directory}" not found'


def test_install_unexpected_archive_type(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    archive = tmp_path / "foo-22.1-x86_64-linux-bin.tar.gz"
    archive.touch()
    monkeypatch.setattr(
        sys, "argv", ["", "install", "-l", str(tmp_path), "-i", str(tmp_path), str(archive)]
    )
    assert main() == "unexpected archive type"


def test_install_unexpected_file_name(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    archive = tmp_path / "spark-pro-22.1.tar.gz"
    archive.touch()
    monkeypatch.setattr(
        sys, "argv", ["", "install", "-l", str(tmp_path), "-i", str(tmp_path), str(archive)]
    )
    assert main() == "unexpected file name"


@pytest.mark.parametrize(
    "archive, name, version",
    [
        (
            "spark-pro-22.1-x86_64-linux-bin.tar.gz",
            "sparkpro",
            "22.1",
        ),
        (
            "spark-pro-23.0w-20220202-x86_64-linux-bin.tar.gz",
            "sparkpro",
            "23.0w-20220202",
        ),
        (
            "gnatpro-22.1-x86_64-linux-bin.tar.gz",
            "gnatpro",
            "22.1",
        ),
        (
            "gnatpro-23.0w-20220202-x86_64-linux-bin.tar.gz",
            "gnatpro",
            "23.0w-20220202",
        ),
        (
            "gnatpro-23.0w-20220202-arm-elf-linux64-bin.tar.gz",
            "gnatpro-arm-elf",
            "23.0w-20220202",
        ),
        (
            "gnatpro-23.0w-20220202-riscv64-elf-linux64-bin.tar.gz",
            "gnatpro-riscv64-elf",
            "23.0w-20220202",
        ),
    ],
)
def test_install(
    archive: str, name: str, version: str, monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    lmod_dir = tmp_path / "lmod"
    lmod_dir.mkdir()
    install_dir = tmp_path / "install"
    install_dir.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "",
            "install",
            "-l",
            str(lmod_dir),
            "-i",
            str(install_dir),
            str(TEST_DATA / archive),
        ],
    )
    assert main() == 0
    assert (lmod_dir / name / f"{version}.lua").is_file()
    assert (install_dir / name / version / "done").is_file()
