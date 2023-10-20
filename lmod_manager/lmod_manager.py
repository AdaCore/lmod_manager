#!/usr/bin/env python3

"""
Manage Lmod modulefiles for various AdaCore software.

Prerequisites: Write access to installation directory (e.g., /opt/sparkpro) and lmod config
directory (e.g., /etc/lmod/modules/sparkpro or ~/.config/lmod/modulefiles/sparkpro)
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import textwrap
from abc import abstractmethod
from importlib.metadata import version
from pathlib import Path
from subprocess import call
from typing import Optional, Union

DEFAULT_LMOD_MODULES_DIR = "/etc/lmod/modules"
DEFAULT_INSTALLATION_DIR = "/opt"


class Error(Exception):
    pass


class Tool:
    def __init__(self, archive: Optional[Path] = None, module_name: Optional[str] = None) -> None:
        assert (archive and not module_name) or (not archive and module_name)

        if archive:
            match = re.match(
                rf"{self.archive_name()}-([\d.wrc]*(?:-\d*)?)"
                rf"-([\w-]*)-(linux(?:64|)?)-bin\.tar\.gz",
                archive.name,
            )

            if not match:
                raise Error("unexpected archive name format")

            self._archive = archive
            self._version = match.group(1)
            self._target = match.group(2)
            self._linux = match.group(3)

        if module_name:
            match = re.match(rf"{self.name()}((?:-[^/]*)?)/([\d.wrc]*(?:-\d*)?)", module_name)

            if not match:
                raise Error("unexpected module name format")

            self._target = match.group(1)[1:]
            self._version = match.group(2)

    @staticmethod
    def from_archive(archive: Path) -> Tool:
        if archive.name.startswith(Gnat.archive_name()):
            return Gnat(archive)
        if archive.name.startswith(Spark.archive_name()):
            return Spark(archive)
        if archive.name.startswith(CodePeer.archive_name()):
            return CodePeer(archive)
        if archive.name.startswith(GnatStudio.archive_name()):
            return GnatStudio(archive)
        raise Error("unexpected archive type")

    @staticmethod
    def from_module(module_name: str) -> Tool:
        if module_name.startswith(Gnat.name()):
            return Gnat(module_name=module_name)
        if module_name.startswith(Spark.name()):
            return Spark(module_name=module_name)
        if module_name.startswith(CodePeer.name()):
            return CodePeer(module_name=module_name)
        if module_name.startswith(GnatStudio.name()):
            return GnatStudio(module_name=module_name)
        raise Error("unexpected module type")

    @staticmethod
    @abstractmethod
    def name() -> str:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def archive_name() -> str:
        raise NotImplementedError

    @property
    def module_name(self) -> str:
        if self._target and self._target != "x86_64":
            return f"{self.name()}-{self._target}"
        return self.name()

    def install(self, installation_dir: Path, lmod_modules_dir: Path) -> None:
        full_installation_dir = self._installation_dir(installation_dir)
        full_installation_dir.parent.mkdir(exist_ok=True)
        config_dir = self._config_dir(lmod_modules_dir)
        config_dir.mkdir(exist_ok=True)
        config_file = self._config_file(lmod_modules_dir)
        config_file.touch()

        shutil.unpack_archive(self._archive, format="gztar")
        self._install_archive(full_installation_dir)
        shutil.rmtree(self._extracted_archive_dir())

        with open(config_file, "w", encoding="utf-8") as f:
            f.write(
                textwrap.dedent(
                    f"""\
                    local pkgName = myModuleName()
                    local version = myModuleVersion()
                    local pkg     = pathJoin("{installation_dir}",pkgName,version,"bin")
                    prepend_path("PATH", pkg)
                    """
                )
            )

    def uninstall(self, installation_dir: Path, lmod_modules_dir: Path) -> None:
        installation_dir = self._installation_dir(installation_dir)

        if not installation_dir.exists():
            raise Error(f"installation directory '{installation_dir}' not found")
        if not (installation_dir / self._installation_file()).exists():
            raise Error(f"directory '{installation_dir}' seems not to contain a valid installation")

        config_file = self._config_file(lmod_modules_dir)

        if not config_file.exists():
            raise Error(f"config file '{config_file}' not found")

        shutil.rmtree(installation_dir)
        config_file.unlink()

    def _config_dir(self, prefix: Path) -> Path:
        return prefix / self.module_name

    def _config_file(self, prefix: Path) -> Path:
        return prefix / self.module_name / f"{self._version}.lua"

    def _installation_dir(self, prefix: Path) -> Path:
        return prefix / self.module_name / self._version

    def _extracted_archive_dir(self) -> Path:
        return Path(f"{self.archive_name()}-{self._version}-{self._target}-{self._linux}-bin")

    @staticmethod
    @abstractmethod
    def _installation_file() -> Path:
        raise NotImplementedError

    @abstractmethod
    def _install_archive(self, installation_dir: Path) -> None:
        raise NotImplementedError


class Gnat(Tool):
    @staticmethod
    def name() -> str:
        return "gnatpro"

    @staticmethod
    def archive_name() -> str:
        return "gnatpro"

    @staticmethod
    def _installation_file() -> Path:
        return Path("bin/gnat")

    def _install_archive(self, installation_dir: Path) -> None:
        call(
            f"cd {self._extracted_archive_dir()}"
            f" && echo -e '\n{installation_dir}\nY\nY\n' | ./doinstall",
            shell=True,
        )


class Spark(Tool):
    @staticmethod
    def name() -> str:
        return "sparkpro"

    @staticmethod
    def archive_name() -> str:
        return "spark-pro"

    @staticmethod
    def _installation_file() -> Path:
        return Path("bin/gnatprove")

    def _install_archive(self, installation_dir: Path) -> None:
        call(f"echo '{installation_dir}' | {self._extracted_archive_dir()}/doinstall", shell=True)


class CodePeer(Tool):
    @staticmethod
    def name() -> str:
        return "codepeer"

    @staticmethod
    def archive_name() -> str:
        return "codepeer"

    @staticmethod
    def _installation_file() -> Path:
        return Path("bin/codepeer")

    def _install_archive(self, installation_dir: Path) -> None:
        call(f"cd {self._extracted_archive_dir()} && ./doinstall {installation_dir}", shell=True)


class GnatStudio(Tool):
    @staticmethod
    def name() -> str:
        return "gnatstudio"

    @staticmethod
    def archive_name() -> str:
        return "gnatstudio"

    @staticmethod
    def _installation_file() -> Path:
        return Path("bin/gnatstudio")

    def _install_archive(self, installation_dir: Path) -> None:
        call(f"cd {self._extracted_archive_dir()} && ./doinstall {installation_dir}", shell=True)


def main() -> Union[int, str]:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--version",
        action="version",
        version=version("lmod_manager"),
    )
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
        "archives",
        metavar="ARCHIVE",
        type=Path,
        nargs="+",
        help="list of archives (e.g., spark-pro-22.1-x86_64-linux-bin.tar.gz)",
    )

    parser_uninstall = subparsers.add_parser("uninstall")
    parser_uninstall.set_defaults(func=uninstall)
    parser_uninstall.add_argument(
        "modules",
        metavar="MODULE",
        type=str,
        nargs="+",
        help="list of modules (e.g., sparkpro/22.1)",
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
    for archive in args.archives:
        if not archive.is_file():
            return f'file "{archive}" not found'

        try:
            Tool.from_archive(archive).install(args.installation_dir, args.lmod_modules_dir)
        except Error as e:
            return str(e)

    return 0


def uninstall(args: argparse.Namespace) -> Union[int, str]:
    for module in args.modules:
        try:
            Tool.from_module(module).uninstall(args.installation_dir, args.lmod_modules_dir)
        except Error as e:
            return str(e)

    return 0
