# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

"""Main entry point for the application commands."""

import sys

from . import (
    exceptions,
    fsteal,
)


def fsteal_main():
    """Entry point for the fsteal command."""
    _run(fsteal)


def _run(command):
    """Set up and run the given command.

    The provided command is an object implementing the following interface:
        - setup() -> args: for parsing command line arguments;
        - run(args): for executing the command, possibly raising AppError.
    """
    args = command.setup()
    try:
        command.run(args)
    except KeyboardInterrupt:
        print('exiting')
        sys.exit(1)
    except exceptions.AppError as err:
        sys.exit(err)
