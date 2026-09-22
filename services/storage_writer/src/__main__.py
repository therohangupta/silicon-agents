"""Module runner for ``python -m services.storage_writer.src``.

Delegates to ``main.main`` so both ``python -m services.storage_writer.src``
and ``python -m services.storage_writer.src.main`` share one implementation.
The ``if __name__`` guard ensures importing this package for tests does not
start the consumer loop.
"""

# Entrypoint function that parses args and runs the async supervisor.
from .main import main

# Only start when executed as __main__ (python -m …).
if __name__ == "__main__":
    # Hand off to the real CLI/async runner.
    main()
