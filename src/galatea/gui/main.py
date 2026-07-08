"""Main entrypoint for launching speedwagon with galatea configured."""

import sys

__all__ = []


def main() -> int:
    """Run the Speedwagon based gui."""
    from galatea.gui.bootstrap_speedwagon import run_speedwagon  # noqa

    return run_speedwagon(sys.argv)
    # try:
    # except ImportError:
    #     print("Error: This feature requires the 'gui' extra.")
    #     print("Please install it using: pip install 'galatea[gui]'")
    #     return 1


if __name__ == "__main__":
    sys.exit(main())
