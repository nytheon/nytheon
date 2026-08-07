"""Allow ``python -m profile_builder`` to invoke the CLI."""

import sys

from .main import main

if __name__ == "__main__":
    sys.exit(main())
