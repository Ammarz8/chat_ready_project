import json
import logging
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extras import Json
from extractor.config import ExtractorConfig

logger = logging.getLogger(__name__)

class SourceDatabaseClient:
    """
    Handles connections and SQL executions targeting the Bronze Landing Database (source_db).
    Ensures safe transaction rollbacks and structured JSONB serialization.
    """
    def __init__(self, config: ExtractorConfig):
        """
        Initializes the database client with configuration settings.
        
        Args:
            config (ExtractorConfig): Configurations containing credentials.
        """
        self._config = config
        self._conn = None

    def connect(self) -> None:
        """
        Establishes a connection to the PostgreSQL source database.
        Raises connection error on failures.
        """
        if self._conn is not None and not self._conn.closed:
            return
        
        logger.info(
            f"Establishing connection to source database: "
            f"host={self._config.db_host}, port={self._config.db_port}, db={self._config.db_name}"
        )
        
        try:
            self._conn = psycopg2.connect(
                host=self._config.db_host,
                port=self._config.db_port,
                user=self._config.db_user,
                password=self._config.db_password,
                dbname=self._config.db_name,
                connect_timeout=10
            )
            # Enforce explicit transaction control
            self._conn.autocommit = False
            logger.info("Successfully connected to source database.")
            
        except Exception as e:
            logger.error(f"Failed to establish database connection: {e}")
            self._conn = None
            raise

    def disconnect(self) -> None:
        """
        Safely disconnects from the database if a connection is active.
        """
        if self._conn is not None:
            if not self._conn.closed:
                self._conn.close()
                logger.info("Source database connection closed.")
            self._conn = None

    def insert_raw_request(
        self, 
        endpoint: str, 
        parameters: Dict[str, Any], 
        status_code: int, 
        payload: Any
    ) -> None:
        """
        Inserts a raw API response and payload into the raw_requests table.
        Rolls back the transaction upon failures.
        
        Args:
            endpoint (str): API endpoint path queried.
            parameters (dict): Query parameters dictionary passed to the request.
            status_code (int): Response HTTP status code.
            payload (any): Parsed JSON object list retrieved.
        """
        self.connect()
        
        query = """
            INSERT INTO raw_requests (
                endpoint, 
                request_parameters, 
                status_code, 
                payload, 
                processed
            ) VALUES (%s, %s, %s, %s, FALSE)
        """
        
        try:
            with self._conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        endpoint,
                        Json(parameters),
                        status_code,
                        Json(payload)
                    )
                )
            self._conn.commit()
            logger.info(
                f"Successfully saved raw payload for '{endpoint}' to Bronze database."
            )
            
        except Exception as e:
            if self._conn:
                self._conn.rollback()
            logger.error(f"Transaction failed while inserting raw request payload: {e}")
            raise
            
    def __enter__(self) -> "SourceDatabaseClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
