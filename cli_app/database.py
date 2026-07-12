import logging
import psycopg2
from psycopg2.extras import DictCursor
from cli_app.config import CLIConfig

logger = logging.getLogger(__name__)

class TargetDatabaseClient:
    """
    Manages connection profiles and read-only query executions targeting target_db.
    """
    def __init__(self, config: CLIConfig):
        """
        Initializes the client with configuration parameters.
        
        Args:
            config (CLIConfig): Database credentials and settings.
        """
        self._config = config
        self._conn = None

    def connect(self) -> None:
        """
        Establishes read-only, autocommit connection to the target database.
        """
        if self._conn is not None and not self._conn.closed:
            return
        
        try:
            self._conn = psycopg2.connect(
                host=self._config.db_host,
                port=self._config.db_port,
                user=self._config.db_user,
                password=self._config.db_password,
                dbname=self._config.db_name,
                connect_timeout=5
            )
            # Enforce read-only access for presentation layer safety
            self._conn.set_session(readonly=True, autocommit=True)
            
        except Exception as e:
            logger.error(f"Failed to connect to target DB: {e}")
            self._conn = None
            raise

    def disconnect(self) -> None:
        """Closes target database connection session."""
        if self._conn is not None:
            if not self._conn.closed:
                self._conn.close()
            self._conn = None

    def execute_query(self, query: str, params: tuple = ()) -> list:
        """
        Executes SELECT queries and yields list of row dictionaries.
        
        Args:
            query (str): SQL SELECT query string.
            params (tuple): Query parameters tuple.
            
        Returns:
            list: List of dictionary records representing matching database rows.
        """
        self.connect()
        try:
            with self._conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error executing database query: {e}")
            raise

    def __enter__(self) -> "TargetDatabaseClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
