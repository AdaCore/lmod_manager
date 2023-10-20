import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

import pytest
from pytest import MonkeyPatch

from lmod_manager import main

TEST_DATA = Path("tests/data")

Archive = NamedTuple("Archive", [("archive", str), ("name", str), ("version", str)])


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


def test_install_unexpected_archive_name_format(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
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
    assert main() == "unexpected archive name format"


@pytest.mark.parametrize(
    "archives",
    [
        [
            Archive(
                "spark-pro-22.1-x86_64-linux-bin.tar.gz",
                "sparkpro",
                "22.1",
            ),
        ],
        [
            Archive(
                "spark-pro-23.0w-20220202-x86_64-linux-bin.tar.gz",
                "sparkpro",
                "23.0w-20220202",
            ),
        ],
        [
            Archive(
                "gnatpro-20.2-x86_64-linux-bin.tar.gz",
                "gnatpro",
                "20.2",
            ),
        ],
        [
            Archive(
                "gnatpro-22.2-x86_64-linux-bin.tar.gz",
                "gnatpro",
                "22.2",
            ),
        ],
        [
            Archive(
                "gnatpro-23.0w-20220202-x86_64-linux-bin.tar.gz",
                "gnatpro",
                "23.0w-20220202",
            ),
        ],
        [
            Archive(
                "gnatpro-23.0w-20220202-arm-elf-linux64-bin.tar.gz",
                "gnatpro-arm-elf",
                "23.0w-20220202",
            ),
        ],
        [
            Archive(
                "gnatpro-23.0w-20220202-riscv64-elf-linux64-bin.tar.gz",
                "gnatpro-riscv64-elf",
                "23.0w-20220202",
            ),
        ],
        [
            Archive(
                "codepeer-22.1-x86_64-linux-bin.tar.gz",
                "codepeer",
                "22.1",
            ),
        ],
        [
            Archive(
                "codepeer-23.0w-20220202-x86_64-linux-bin.tar.gz",
                "codepeer",
                "23.0w-20220202",
            ),
        ],
        [
            Archive(
                "gnatstudio-23.2-x86_64-linux-bin.tar.gz",
                "gnatstudio",
                "23.2",
            ),
        ],
        [
            Archive(
                "gnatpro-23.0w-20220202-aarch64-qnx-linux64-bin.tar.gz",
                "gnatpro-aarch64-qnx",
                "23.0w-20220202",
            ),
        ],
        [
            Archive(
                "gnatpro-24.1rc-20231020-aarch64-qnx-linux64-bin.tar.gz",
                "gnatpro-aarch64-qnx",
                "24.1rc-20231020",
            ),
        ],
        [
            Archive(
                "gnatpro-24.1rc-20231020-aarch64-elf-linux64-bin.tar.gz",
                "gnatpro-aarch64-elf",
                "24.1rc-20231020",
            ),
        ],
        [
            Archive(
                "gnatpro-24.1rc-20231020-x86_64-linux-bin.tar.gz",
                "gnatpro",
                "24.1rc-20231020",
            ),
        ],
        [
            Archive(
                "gnatpro-24.1rc-20231020-aarch64-qnx-linux64-bin.tar.gz",
                "gnatpro-aarch64-qnx",
                "24.1rc-20231020",
            ),
            Archive(
                "gnatpro-24.1rc-20231020-aarch64-elf-linux64-bin.tar.gz",
                "gnatpro-aarch64-elf",
                "24.1rc-20231020",
            ),
            Archive(
                "spark-pro-23.0w-20220202-x86_64-linux-bin.tar.gz",
                "sparkpro",
                "23.0w-20220202",
            ),
        ],
    ],
)
def test_install_and_uninstall(
    archives: Sequence[Archive], monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    lmod_dir = tmp_path / "lmod"
    lmod_dir.mkdir()
    lmod_files = {lmod_dir / a.name / f"{a.version}.lua" for a in archives}
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
            *[str(TEST_DATA / a.archive) for a in archives],
        ],
    )
    assert main() == 0
    assert all(lmod_file.is_file() for lmod_file in lmod_files)
    assert all((install_dir / a.name / a.version / "done").is_file() for a in archives)

    for lmod_file in lmod_files:
        lmod_file_lines = lmod_file.read_text().split("\n")

        assert any(f'"{install_dir}"' in l for l in lmod_file_lines)

        for l in lmod_file_lines:
            assert not l.startswith(" ")

    for archive in archives:
        if archive.name.startswith("gnatstudio"):
            file = "bin/gnatstudio"
        elif archive.name.startswith("gnat"):
            file = "bin/gnat"
        elif archive.name.startswith("spark"):
            file = "bin/gnatprove"
        elif archive.name.startswith("codepeer"):
            file = "bin/codepeer"
        else:
            assert False
        (install_dir / archive.name / archive.version / file).mkdir(parents=True)

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
            *[f"{a.name}/{a.version}" for a in archives],
        ],
    )
    assert main() == 0
    assert all((lmod_dir / a.name).is_dir() for a in archives)
    assert not all((lmod_dir / a.name / f"{a.version}.lua").is_file() for a in archives)
    assert all((install_dir / a.name).is_dir() for a in archives)
    assert not all((install_dir / a.name / a.version).exists() for a in archives)


def test_uninstall_unexpected_module_type(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
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
    assert main() == "unexpected module type"


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
            "sparkpro#invalid",
        ],
    )
    assert main() == "unexpected module name format"


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
