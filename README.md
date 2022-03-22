# Lmod Manager

This tool manages [Lmod](https://github.com/TACC/Lmod) modulefiles for various AdaCore software. The created modulefiles enable easy switching between different software versions. Lmod achieves that by dynamically changing the `PATH` environment variable.

## Installation

```console
$ pip3 install git+https://github.com/AdaCore/lmod_manager.git
```

## Usage

A new software version can be installed using the `install` subcommand.

```console
$ lmod_manager install spark-pro-22.1-x86_64-linux-bin.tar.gz
```

A corresponding modulefile will be automatically created.

```console
$ module avail

------------------------------------------------- /etc/lmod/modules --------------------------------------------------
   gnat/2020                     gnatpro/22.0                              sparkpro/20.2
   gnat/2021                     gnatpro/22.1                              sparkpro/21.1
   gnatpro/20.0                  gnatpro-arm-elf/22.0                      sparkpro/22.0
   gnatpro/20.1                  gnatpro-riscv32-elf/22.0                  sparkpro/22.1

```

To use or switch to a particular version, the corresponding module must be loaded.

```console
$ module load sparkpro/22.1
```

See the [User Guide for Lmod](https://lmod.readthedocs.io/en/latest/010_user.html) for an introduction to Lmod.

## Requirements

- [Python](https://www.python.org/) 3.7+
- [Lmod](https://github.com/TACC/Lmod)

## Limitations

So far, only GNAT Pro and SPARK Pro are supported.
