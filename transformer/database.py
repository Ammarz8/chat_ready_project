import logging
from typing import List, Dict, Any, Tuple, Optional
import psycopg2
from psycopg2.extras import DictCursor
from transformer.config import TransformerConfig

logger = logging.getLogger(__name__)

class ETLDatabaseManager:
    """
    Manages connections and transactions for the Bronze (source_db) 
    and Silver (target_db) databases. Facilitates reading raw data,
    updating processed status, and executing transactional normalized inserts.
    """
    def __init__(self, config: TransformerConfig):
        """
        Initializes the database manager with configurations.
        
        Args:
            config (TransformerConfig): Database settings and credentials.
        """
        self._config = config
        self._source_conn = None
        self._target_conn = None

    def connect_source(self) -> None:
        """Establishes connection to the source_db database."""
        if self._source_conn is not None and not self._source_conn.closed:
            return
        
        logger.info(f"Connecting to source DB: host={self._config.source_db_host}, db={self._config.source_db_name}")
        try:
            self._source_conn = psycopg2.connect(
                host=self._config.source_db_host,
                port=self._config.source_db_port,
                user=self._config.source_db_user,
                password=self._config.source_db_password,
                dbname=self._config.source_db_name,
                connect_timeout=10
            )
            self._source_conn.autocommit = False
        except Exception as e:
            logger.error(f"Failed to connect to source DB: {e}")
            raise

    def connect_target(self) -> None:
        """Establishes connection to the target_db database."""
        if self._target_conn is not None and not self._target_conn.closed:
            return
        
        logger.info(f"Connecting to target DB: host={self._config.target_db_host}, db={self._config.target_db_name}")
        try:
            self._target_conn = psycopg2.connect(
                host=self._config.target_db_host,
                port=self._config.target_db_port,
                user=self._config.target_db_user,
                password=self._config.target_db_password,
                dbname=self._config.target_db_name,
                connect_timeout=10
            )
            self._target_conn.autocommit = False
        except Exception as e:
            logger.error(f"Failed to connect to target DB: {e}")
            raise

    def disconnect(self) -> None:
        """Safely closes connections to both databases."""
        if self._source_conn is not None:
            if not self._source_conn.closed:
                self._source_conn.close()
            self._source_conn = None
        if self._target_conn is not None:
            if not self._target_conn.closed:
                self._target_conn.close()
            self._target_conn = None
        logger.info("Database connections disconnected successfully.")

    def fetch_unprocessed_batches(self) -> List[Tuple[int, Any, int]]:
        """
        Retrieves raw payloads that have not yet been transformed.
        
        Returns:
            List[Tuple[int, Any, int]]: list of (request_id, payload, status_code).
        """
        self.connect_source()
        query = """
            SELECT request_id, payload, status_code 
            FROM raw_requests 
            WHERE processed = FALSE 
            ORDER BY retrieved_at ASC
        """
        batches = []
        try:
            with self._source_conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                for row in rows:
                    batches.append((row["request_id"], row["payload"], row["status_code"]))
            logger.info(f"Fetched {len(batches)} unprocessed batches from Bronze DB.")
            return batches
        except Exception as e:
            logger.error(f"Failed to fetch unprocessed batches: {e}")
            raise

    def mark_batches_processed(self, request_ids: List[int]) -> None:
        """
        Marks processed request batches to prevent re-extraction.
        
        Args:
            request_ids (List[int]): Database primary keys to update.
        """
        if not request_ids:
            return
        self.connect_source()
        query = "UPDATE raw_requests SET processed = TRUE WHERE request_id = ANY(%s)"
        try:
            with self._source_conn.cursor() as cursor:
                cursor.execute(query, (request_ids,))
            self._source_conn.commit()
            logger.info(f"Marked request IDs {request_ids} as processed in Bronze DB.")
        except Exception as e:
            if self._source_conn:
                self._source_conn.rollback()
            logger.error(f"Failed to update processed status for request IDs {request_ids}: {e}")
            raise

    def load_normalized_data(
        self, 
        makes: List[str], 
        classes: List[str], 
        models: List[Dict[str, Any]]
    ) -> Tuple[int, int, int]:
        """
        Performs atomic insertions of dimensions and facts into the Silver database.
        
        Args:
            makes (List[str]): Unique manufacturer names.
            classes (List[str]): Unique vehicle class names.
            models (List[Dict[str, Any]]): Cleaned vehicle detail dictionaries.
            
        Returns:
            Tuple[int, int, int]: (upserted_makes, upserted_classes, inserted_models).
        """
        self.connect_target()
        
        makes_upserted = 0
        classes_upserted = 0
        models_inserted = 0
        
        try:
            with self._target_conn.cursor() as cursor:
                # 1. UPSERT Makes & extract IDs
                make_ids = {}
                for name in makes:
                    cursor.execute(
                        """
                        INSERT INTO makes (name) VALUES (%s) 
                        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                        RETURNING make_id;
                        """,
                        (name,)
                    )
                    make_ids[name] = cursor.fetchone()[0]
                    makes_upserted += 1
                
                # 2. UPSERT Classes & extract IDs
                class_ids = {}
                for name in classes:
                    cursor.execute(
                        """
                        INSERT INTO vehicle_classes (name) VALUES (%s) 
                        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                        RETURNING class_id;
                        """,
                        (name,)
                    )
                    class_ids[name] = cursor.fetchone()[0]
                    classes_upserted += 1
                
                # 3. Insert Models with Conflict Resolution
                for model in models:
                    make_id = make_ids[model["make"]]
                    class_id = class_ids[model["class"]] if model["class"] else None
                    
                    cursor.execute(
                        """
                        INSERT INTO car_models (
                            make_id, model_name, year, class_id, transmission, drive_type, 
                            fuel_type, cylinders, displacement, city_mpg, highway_mpg, combination_mpg
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) ON CONFLICT ON CONSTRAINT uq_car_specification DO NOTHING
                        RETURNING model_id;
                        """,
                        (
                            make_id,
                            model["model_name"],
                            model["year"],
                            class_id,
                            model["transmission"],
                            model["drive_type"],
                            model["fuel_type"],
                            model["cylinders"],
                            model["displacement"],
                            model["city_mpg"],
                            model["highway_mpg"],
                            model["combination_mpg"]
                        )
                    )
                    result = cursor.fetchone()
                    # Only count if it was inserted (DO NOTHING returns no ID)
                    if result:
                        models_inserted += 1
                        
            # Commit the target transaction atomic block
            self._target_conn.commit()
            logger.info("Successfully loaded batch to Target DB.")
            return makes_upserted, classes_upserted, models_inserted
            
        except Exception as e:
            if self._target_conn:
                self._target_conn.rollback()
            logger.error(f"Database loading transaction failed: {e}")
            raise

    def __enter__(self) -> "ETLDatabaseManager":
        self.connect_source()
        self.connect_target()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
