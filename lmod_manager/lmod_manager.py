#!/usr/bin/env python3

"""
Manage Lmod modulefiles for various AdaCore software.

Prerequisites: Write access to installation directory (e.g., /opt/sparkpro) and lmod config
directory (e.g., /etc/lmod/modules/sparkpro or ~/.config/lmod/modulefiles/sparkpro)
"""

import argparse
import re
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


def main() -> Union[int, str]:
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="subcommand")

    parser_install = subparsers.add_parser("install")
    parser_install.add_argument(
        "archive",
        metavar="ARCHIVE",
        type=Path,
        help="path to archive (e.g., spark-pro-22.1-x86_64-linux-bin.tar.gz)",
    )
    parser_install.add_argument(
        "-l",
        metavar="LMOD_MODULES_DIR",
        dest="lmod_modules_dir",
        default=DEFAULT_LMOD_MODULES_DIR,
        type=Path,
        help=f"path to lmod module directory (default: {DEFAULT_LMOD_MODULES_DIR})",
    )
    parser_install.add_argument(
        "-i",
        metavar="INSTALLATION_DIR",
        dest="installation_dir",
        default=DEFAULT_INSTALLATION_DIR,
        type=Path,
        help=f"path to installation directory (default: {DEFAULT_INSTALLATION_DIR})",
    )
    parser_install.set_defaults(func=install)

    args = parser.parse_args(sys.argv[1:])

    if not args.subcommand:
        parser.print_usage()
        return 2

    return args.func(args)  # type: ignore[no-any-return]


def install(args: argparse.Namespace) -> Union[int, str]:
    if not args.archive.is_file():
        return f'file "{args.archive}" not found'

    if not args.lmod_modules_dir.is_dir():
        return f'directory "{args.lmod_modules_dir}" not found'

    if not args.installation_dir.is_dir():
        return f'directory "{args.installation_dir}" not found'

    if "spark-pro" in args.archive.name:
        archive_type = Type.SPARK
        archive_regex = r"spark-pro-([\d.w]*(?:-\d*)?)-([\w-]*)-(linux(?:64|)?)-bin\.tar\.gz"
        name = "sparkpro"
    elif "gnatpro" in args.archive.name:
        archive_type = Type.GNAT
        archive_regex = r"gnatpro-([\d.w]*(?:-\d*)?)-([\w-]*)-(linux(?:64|)?)-bin\.tar\.gz"
        name = "gnatpro"
    else:
        return "unexpected archive type"

    match = re.match(archive_regex, args.archive.name)
    if not match:
        return "unexpected file name"
    version = match.group(1)
    target = match.group(2)
    linux = match.group(3)

    if target != "x86_64":
        name = f"{name}-{target}"

    installation_dir = Path(f"{args.installation_dir}/{name}/{version}/")
    installation_dir.parent.mkdir(exist_ok=True)
    config_dir = Path(f"{args.lmod_modules_dir}/{name}")
    config_dir.mkdir(exist_ok=True)
    config_file = Path(f"{config_dir}/{version}.lua")
    config_file.touch()

    if archive_type is Type.SPARK:
        extracted_archive_dir = f"spark-pro-{version}-{target}-{linux}-bin"
        installation_cmd = f"echo '{installation_dir}' | {extracted_archive_dir}/doinstall"
    elif archive_type is Type.GNAT:
        extracted_archive_dir = f"gnatpro-{version}-{target}-{linux}-bin"
        installation_cmd = f"cd {extracted_archive_dir} && ./doinstall {installation_dir}"
    else:
        assert_never(archive_type)  # pragma: no cover

    call(f"tar xzf {args.archive}", shell=True)
    call(installation_cmd, shell=True)
    call(f"rm -rf {extracted_archive_dir}", shell=True)

    with open(config_file, "w", encoding="utf-8") as f:
        f.write(
            f"""local pkgName = myModuleName()
local version = myModuleVersion()
local pkg     = pathJoin("{args.installation_dir}",pkgName,version,"bin")
prepend_path("PATH", pkg)
"""
        )

    return 0


def assert_never(value: NoReturn) -> NoReturn:
    assert False, f"Unhandled value: {value} ({type(value).__name__})"
