#!/usr/bin/env python3
"""
Fleet Manager process entrypoint.

This module is invoked as ``python -m services.fleet_server.src``. It is
responsible for:

  1. Loading environment variables from a local ``.env`` (OpenAI key, DB URL).
  2. Parsing CLI flags (port, DB reset, verbosity, SQL debug).
  3. Installing SIGINT/SIGTERM handlers for graceful asyncio shutdown.
  4. Launching ``serve()`` from ``service.py`` as a background task.
  5. Waiting for a stop signal, then cancelling the server task cleanly.

Behavior is intentionally thin: all gRPC / DB / planner logic lives in
``service.py`` and its collaborators. This file only owns process lifecycle.
"""

# asyncio drives the gRPC aio server and the stop Event wait loop below.
import asyncio
# argparse exposes --port / --reset-db / -v / --sql-debug for operators.
import argparse
# os is used to read DATABASE_URL from the process environment.
import os
# signal provides SIGINT/SIGTERM constants registered with the event loop.
import signal
# sys is used for a clean exit code after KeyboardInterrupt at top level.
import sys
# dotenv loads secrets and config from a .env file before other imports that
# may read OPENAI_API_KEY / DATABASE_URL.
from dotenv import load_dotenv

# Load environment variables from .env file into os.environ early so that
# packages.config and OpenAI client construction see the same values as local
# development shells that source .env manually.
load_dotenv()

# GRPC_SERVER_PORT is the default listen port (typically 50051) when --port
# is omitted.
from packages.config import GRPC_SERVER_PORT
# serve() constructs FleetManagerService, initializes the DB, and blocks on
# gRPC wait_for_termination until cancelled.
from .service import serve


async def main():
    """
    Parse CLI arguments, install signal handlers, and run the gRPC server.

    The server is started as an asyncio Task so that this coroutine can wait
    on ``stop_event`` independently. When a signal arrives, the stop event is
    set, the finally block cancels ``server_task``, and cancellation is
    swallowed so the process exits without a noisy traceback.

    Returns:
        None. Process exit is handled by the ``__main__`` guard below.
    """
    # Build an argument parser describing how to start the Fleet Manager.
    parser = argparse.ArgumentParser(description='Start the Fleet Manager server')
    # --port overrides the default from packages.config.GRPC_SERVER_PORT.
    parser.add_argument('--port', type=int, default=GRPC_SERVER_PORT, help='Port to listen on')
    # --reset-db drops and recreates all ORM tables on startup (destructive).
    parser.add_argument('--reset-db', action='store_true', help='Reset database on startup')
    # -v / --verbose raises application loggers to DEBUG for diagnosis.
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose application logging')
    # --sql-debug raises sqlalchemy.engine logging so SQL statements appear.
    parser.add_argument('--sql-debug', action='store_true', help='Enable SQL debug logging')
    # Parse argv into a Namespace consumed when calling serve().
    args = parser.parse_args()

    # Optional DATABASE_URL override; serve() falls back to packages.config
    # DATABASE_URL when this is None/empty.
    db_url = os.environ.get('DATABASE_URL')

    # stop_event is set by signal handlers to unblock wait() and enter finally.
    stop_event = asyncio.Event()

    def handle_signal(*_):
        """
        Mark the stop event when the OS delivers SIGINT or SIGTERM.

        The unused ``*_`` absorbs signal number / frame arguments from the
        loop's signal handler callback signature. Printing here gives the
        operator immediate feedback that shutdown has begun.
        """
        # Inform the operator that a graceful shutdown path was taken.
        print("\nReceived exit signal, shutting down gracefully...")
        # Unblock await stop_event.wait() in main so finally can cancel serve.
        stop_event.set()

    # Obtain the running loop so we can register OS signal callbacks on it.
    loop = asyncio.get_running_loop()
    # Register the same handler for interactive Ctrl-C and container stop.
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            # Prefer loop-native handlers so signals wake the event loop safely.
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            # add_signal_handler may not be implemented on Windows; ignore and
            # rely on KeyboardInterrupt around asyncio.run instead.
            pass

    # Launch serve() as a Task so we can cancel it when stop_event fires.
    server_task = asyncio.create_task(
        serve(port=args.port, db_url=db_url, reset_db=args.reset_db, verbose=args.verbose, sql_debug=args.sql_debug)
    )
    try:
        # Block until a signal handler sets stop_event (or cancellation).
        await stop_event.wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        # Secondary path if KeyboardInterrupt somehow surfaces here.
        print("\nGraceful shutdown initiated.")
    finally:
        # Request cancellation of the gRPC serve loop / wait_for_termination.
        server_task.cancel()
        try:
            # Await the cancelled task so cleanup in serve()'s finally runs.
            await server_task
        except asyncio.CancelledError:
            # Expected when we cancelled the task; swallow to exit cleanly.
            pass


# Standard module entry: only run when executed as a script/module, not import.
if __name__ == '__main__':
    try:
        # Drive the async main() coroutine until it returns or is interrupted.
        asyncio.run(main())
    except KeyboardInterrupt:
        # Top-level Ctrl-C fallback for platforms without loop signal handlers.
        print("\nServer stopped by user.")
        # Exit with success so containers/orchestrators treat Ctrl-C as clean.
        sys.exit(0)
