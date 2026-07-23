#!/usr/bin/env python3
# Copyright Sensors & Signals LLC https://www.snstac.com
# SPDX-License-Identifier: Apache-2.0
"""PyTAK Command Line for SAPIENTCOT."""

import pytak


def main() -> None:
    """Boilerplate main func — hands off to the PyTAK CLI runner."""
    pytak.cli(__name__.split(".", maxsplit=1)[0])


if __name__ == "__main__":
    main()
