#!/usr/bin/env python3

"""
Manage Lmod modulefiles for various AdaCore software.

Prerequisites: Write access to installation directory (e.g., /opt/sparkpro) and lmod config
directory (e.g., /etc/lmod/modules/sparkpro or ~/.config/lmod/modulefiles/sparkpro)
"""

import argparse
import re
import shutil
import sys
from enum import Enum, auto
from pathlib import Path
from subprocess import call
from typing import NoReturn, Union

DEFAULT_LMOD_MODULES_DIR = "/etc/lmod/modules"
DEFAULT_INSTALLATION_DIR = "/opt"


class Type(Enum):
    GNAT = auto()
    SPARK = auto()
    CODEPEER = auto()


def main() -> Union[int, str]:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-l",
        metavar="LMOD_MODULES_DIR",
        dest="lmod_modules_dir",
        default=DEFAULT_LMOD_MODULES_DIR,
        type=Path,
        help=f"path to lmod module directory (default: {DEFAULT_LMOD_MODULES_DIR})",
    )
    parser.add_argument(
        "-i",
        metavar="INSTALLATION_DIR",
        dest="installation_dir",
        default=DEFAULT_INSTALLATION_DIR,
        type=Path,
        help=f"path to installation directory (default: {DEFAULT_INSTALLATION_DIR})",
    )

    subparsers = parser.add_subparsers(dest="subcommand")

    parser_install = subparsers.add_parser("install")
    parser_install.set_defaults(func=install)
    parser_install.add_argument(
        "archive",
        metavar="ARCHIVE",
        type=Path,
        help="path to archive (e.g., spark-pro-22.1-x86_64-linux-bin.tar.gz)",
    )

    parser_uninstall = subparsers.add_parser("uninstall")
    parser_uninstall.set_defaults(func=uninstall)
    parser_uninstall.add_argument(
        "module",
        metavar="MODULE",
        type=str,
        help="name of module (e.g., sparkpro/22.1)",
    )

    args = parser.parse_args(sys.argv[1:])

    if not args.subcommand:
        parser.print_usage()
        return 2

    if not args.lmod_modules_dir.is_dir():
        return f'directory "{args.lmod_modules_dir}" not found'

    if not args.installation_dir.is_dir():
        return f'directory "{args.installation_dir}" not found'

    return args.func(args)  # type: ignore[no-any-return]


def install(args: argparse.Namespace) -> Union[int, str]:
    if not args.archive.is_file():
        return f'file "{args.archive}" not found'

    try:
        archive_type = _archive_type(args.archive.name)
    except ValueError:
        return "unexpected archive type"

    match = re.match(_archive_regex(archive_type), args.archive.name)
    if not match:
        return "unexpected file name"
    version = match.group(1)
    target = match.group(2)
    linux = match.group(3)

    name = _module_name(archive_type)

    if target != "x86_64":
        name = f"{name}-{target}"

    installation_dir = _installation_dir(args.installation_dir, name, version)
    installation_dir.parent.mkdir(exist_ok=True)
    config_dir = _config_dir(args.lmod_modules_dir, name)
    config_dir.mkdir(exist_ok=True)
    config_file = _config_file(args.lmod_modules_dir, name, version)
    config_file.touch()
    extracted_archive_dir = _extracted_archive_dir(archive_type, version, target, linux)

    shutil.unpack_archive(args.archive, format="gztar")
    _install_archive(archive_type, installation_dir, extracted_archive_dir)
    shutil.rmtree(extracted_archive_dir)

    with open(config_file, "w", encoding="utf-8") as f:
        f.write(
            f"""local pkgName = myModuleName()
local version = myModuleVersion()
local pkg     = pathJoin("{args.installation_dir}",pkgName,version,"bin")
prepend_path("PATH", pkg)
"""
        )

    return 0


def uninstall(args: argparse.Namespace) -> Union[int, str]:
    match = re.match(r"([^/-]*)((?:-[^/]*)?)/([\d.w]*(?:-\d*)?)", args.module)
    if not match:
        return "unexpected module name format"

    name = match.group(1)
    target = match.group(2)[1:]
    version = match.group(3)

    try:
        module_type = _module_type(name)
    except ValueError:
        return f"unexpected type '{name}'"

    if target:
        name = f"{name}-{target}"

    installation_dir = _installation_dir(args.installation_dir, name, version)

    if not installation_dir.exists():
        return f"installation directory '{installation_dir}' not found"
    if not (installation_dir / _installation_file(module_type)).exists():
        return f"directory '{installation_dir}' seems not to contain a valid installation"

    config_file = _config_file(args.lmod_modules_dir, name, version)

    if not config_file.exists():
        return f"config file '{config_file}' not found"

    shutil.rmtree(installation_dir)
    config_file.unlink()

    return 0


def assert_never(value: NoReturn) -> NoReturn:
    assert False, f"Unhandled value: {value} ({type(value).__name__})"


def _archive_type(name: str) -> Type:
    if name.startswith("gnatpro"):
        return Type.GNAT
    if name.startswith("spark-pro"):
        return Type.SPARK
    if name.startswith("codepeer"):
        return Type.CODEPEER
    raise ValueError


def _archive_name(module_type: Type) -> str:
    if module_type is Type.GNAT:
        return "gnatpro"
    if module_type is Type.SPARK:
        return "spark-pro"
    if module_type is Type.CODEPEER:
        return "codepeer"
    assert_never(module_type)  # pragma: no cover


def _module_type(name: str) -> Type:
    if name == "gnatpro":
        return Type.GNAT
    if name == "sparkpro":
        return Type.SPARK
    if name == "codepeer":
        return Type.CODEPEER
    raise ValueError


def _module_name(module_type: Type) -> str:
    if module_type is Type.GNAT:
        return "gnatpro"
    if module_type is Type.SPARK:
        return "sparkpro"
    if module_type is Type.CODEPEER:
        return "codepeer"
    assert_never(module_type)  # pragma: no cover


def _archive_regex(archive_type: Type) -> str:
    archive_name = _archive_name(archive_type)
    return rf"{archive_name}-([\d.w]*(?:-\d*)?)-([\w-]*)-(linux(?:64|)?)-bin\.tar\.gz"


def _extracted_archive_dir(archive_type: Type, version: str, target: str, linux: str) -> Path:
    archive_name = _archive_name(archive_type)
    return Path(f"{archive_name}-{version}-{target}-{linux}-bin")


def _install_archive(
    archive_type: Type, installation_dir: Path, extracted_archive_dir: Path
) -> None:
    if archive_type is Type.GNAT:
        call(f"cd {extracted_archive_dir} && ./doinstall {installation_dir}", shell=True)
    elif archive_type is Type.SPARK:
        call(f"echo '{installation_dir}' | {extracted_archive_dir}/doinstall", shell=True)
    elif archive_type is Type.CODEPEER:
        call(f"cd {extracted_archive_dir} && ./doinstall {installation_dir}", shell=True)
    else:
        assert_never(archive_type)  # pragma: no cover


def _installation_dir(prefix: Path, name: str, version: str) -> Path:
    return prefix / name / version


def _installation_file(module_type: Type) -> Path:
    if module_type is Type.GNAT:
        return Path("bin/gnat")
    if module_type is Type.SPARK:
        return Path("bin/gnatprove")
    if module_type is Type.CODEPEER:
        return Path("bin/codepeer")
    assert_never(module_type)  # pragma: no cover


def _config_dir(prefix: Path, name: str) -> Path:
    return prefix / name


def _config_file(prefix: Path, name: str, version: str) -> Path:
    return prefix / name / f"{version}.lua"
