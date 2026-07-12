import sys
import logging
from cli_app.config import CLIConfig
from cli_app.database import TargetDatabaseClient
from cli_app.queries import VehicleAnalyticsQueries
from cli_app.menu import CLIMenu

def main() -> None:
    """
    Main application entrypoint for the terminal presentation layer.
    Resolves settings, connects to target database, and opens menu loop.
    """
    # 1. Load configuration settings
    try:
        config = CLIConfig.from_env()
    except ValueError as e:
        print(f"\n[Fatal Error] Configuration loading failed: {e}\n")
        sys.exit(1)

    # 2. Configure logging settings
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.WARNING),
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)] # Route technical logs to stderr
    )

    # 3. Instantiate database client and query wrapper
    db_client = TargetDatabaseClient(config)
    queries = VehicleAnalyticsQueries(db_client)
    menu = CLIMenu(queries)

    # 4. Connect and open CLI terminal loops
    try:
        db_client.connect()
        menu.run()
    except KeyboardInterrupt:
        # Graceful exit on ctrl+c
        print("\n\nProcess interrupted by user. Exiting. Thank you.\n")
    except Exception as e:
        print(f"\n[Fatal Error] Application execution halted: {e}\n")
        sys.exit(1)
    finally:
        db_client.disconnect()

if __name__ == "__main__":
    main()
