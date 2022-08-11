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


def test_install_file_not_found(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "",
            "-l",
            str(tmp_path),
            "-i",
            str(tmp_path),
            "install",
            "foo",
        ],
    )
    assert main() == 'file "foo" not found'


def test_install_lmod_directory_not_found(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    directory = tmp_path / "lmod"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "",
            "-l",
            str(directory),
            "-i",
            str(tmp_path),
            "install",
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
            "-l",
            str(tmp_path),
            "-i",
            str(directory),
            "install",
            str(TEST_DATA / "spark-pro-22.1-x86_64-linux-bin.tar.gz"),
        ],
    )
    assert main() == f'directory "{directory}" not found'


def test_install_unexpected_archive_type(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    archive = tmp_path / "foo-22.1-x86_64-linux-bin.tar.gz"
    archive.touch()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "",
            "-l",
            str(tmp_path),
            "-i",
            str(tmp_path),
            "install",
            str(archive),
        ],
    )
    assert main() == "unexpected archive type"


def test_install_unexpected_file_name(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    archive = tmp_path / "spark-pro-22.1.tar.gz"
    archive.touch()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "",
            "-l",
            str(tmp_path),
            "-i",
            str(tmp_path),
            "install",
            str(archive),
        ],
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
def test_install_and_uninstall(
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
            "-l",
            str(lmod_dir),
            "-i",
            str(install_dir),
            "install",
            str(TEST_DATA / archive),
        ],
    )
    assert main() == 0
    assert (lmod_dir / name / f"{version}.lua").is_file()
    assert (install_dir / name / version / "done").is_file()

    if name.startswith("gnat"):
        file = "bin/gnat"
    elif name.startswith("spark"):
        file = "bin/gnatprove"
    (install_dir / name / version / file).mkdir(parents=True)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "",
            "-l",
            str(lmod_dir),
            "-i",
            str(install_dir),
            "uninstall",
            f"{name}/{version}",
        ],
    )
    assert main() == 0
    assert (lmod_dir / name).is_dir()
    assert not (lmod_dir / name / f"{version}.lua").is_file()
    assert (install_dir / name).is_dir()
    assert not (install_dir / name / version).exists()


def test_uninstall_unexpected_module_name_format(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "",
            "-l",
            str(tmp_path),
            "-i",
            str(tmp_path),
            "uninstall",
            "invalid",
        ],
    )
    assert main() == "unexpected module name format"


def test_uninstall_unexpected_type(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "",
            "-l",
            str(tmp_path),
            "-i",
            str(tmp_path),
            "uninstall",
            "invalid/1",
        ],
    )
    assert main() == "unexpected type 'invalid'"


def test_uninstall_installation_directory_not_found(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "",
            "-l",
            str(tmp_path),
            "-i",
            str(tmp_path),
            "uninstall",
            "sparkpro/12.3",
        ],
    )
    assert main() == f"installation directory '{tmp_path}/sparkpro/12.3' not found"


def test_uninstall_installation_directory_invalid(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "",
            "-l",
            str(tmp_path),
            "-i",
            str(tmp_path),
            "uninstall",
            "sparkpro/12.3",
        ],
    )
    (tmp_path / "sparkpro" / "12.3").mkdir(parents=True)
    assert (
        main() == f"directory '{tmp_path}/sparkpro/12.3' seems not to contain a valid installation"
    )


def test_uninstall_config_file_not_found(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "",
            "-l",
            str(tmp_path),
            "-i",
            str(tmp_path),
            "uninstall",
            "sparkpro/12.3",
        ],
    )
    (tmp_path / "sparkpro" / "12.3" / "bin" / "gnatprove").mkdir(parents=True)
    assert main() == f"config file '{tmp_path}/sparkpro/12.3.lua' not found"
