import sys
import logging
from typing import List, Dict, Any
from transformer.config import TransformerConfig
from transformer.logger import setup_logger
from transformer.database import ETLDatabaseManager
from transformer.transform import CarDataTransformer
from transformer.validation import DataQualityValidator

logger = logging.getLogger("transformer")

def run_transform_pipeline() -> None:
    """
    Orchestrates the Silver transformation pipeline (Transformer).
    Reads unprocessed JSONB records from the Landing Zone (Bronze),
    applies cleaning, filters through domain validations, and loads
    the normalized data into the target analytics database (Silver).
    """
    # 1. Load configuration
    try:
        config = TransformerConfig.from_env()
    except ValueError as e:
        logging.basicConfig(level=logging.ERROR)
        logging.error(f"Failed to load transformer configurations: {e}")
        sys.exit(1)

    # 2. Setup logging level
    setup_logger(config.log_level)
    logger.info("Initializing Transformer ETL processing pipeline...")

    # 3. Instantiate ETL components
    transformer = CarDataTransformer()
    validator = DataQualityValidator()
    db_manager = ETLDatabaseManager(config)

    # Global tracking counters
    total_batches_processed = 0
    total_records_read = 0
    total_records_valid = 0
    total_records_inserted = 0
    
    processed_request_ids: List[int] = []

    try:
        with db_manager:
            # 4. Fetch unprocessed records from Landing Zone (Bronze DB)
            raw_batches = db_manager.fetch_unprocessed_batches()
            
            if not raw_batches:
                logger.info("No unprocessed batches found in Landing Zone. Pipeline idle.")
                sys.exit(0)

            logger.info(f"Beginning transformation loop for {len(raw_batches)} batches.")

            for request_id, payload, status_code in raw_batches:
                total_batches_processed += 1
                
                # Mark batch ID for processing update regardless of success/error
                processed_request_ids.append(request_id)
                
                # If extraction was not successful (e.g. 400 Bad Request log), skip processing
                if status_code != 200:
                    logger.warning(
                        f"Skipping transformation for batch ID {request_id} "
                        f"due to non-200 ingestion status ({status_code})."
                    )
                    continue

                if not isinstance(payload, list):
                    logger.error(
                        f"Invalid payload format in batch ID {request_id}. "
                        f"Expected list, found {type(payload)}."
                    )
                    continue

                batch_cleaned_models: List[Dict[str, Any]] = []
                batch_records_count = len(payload)
                total_records_read += batch_records_count
                
                logger.info(
                    f"Processing batch ID {request_id} containing {batch_records_count} raw records."
                )

                # 5. Clean, transform, and validate each item in the batch
                for raw_car in payload:
                    cleaned_car = transformer.transform_record(raw_car)
                    if cleaned_car is not None:
                        if validator.is_valid(cleaned_car):
                            batch_cleaned_models.append(cleaned_car)
                            total_records_valid += 1
                        else:
                            logger.warning(
                                f"Record rejected by validation checks: {raw_car.get('make')}-{raw_car.get('model')}"
                            )
                    else:
                        logger.warning(
                            f"Record rejected by transformation parsing: {raw_car.get('make')}-{raw_car.get('model')}"
                        )

                if not batch_cleaned_models:
                    logger.info(
                        f"Batch ID {request_id} yielded 0 valid relational records. Skipping DB write."
                    )
                    continue

                # 6. Extract unique makes and classes lookup values for reference tables
                makes, classes = transformer.extract_dimensions(batch_cleaned_models)

                # 7. Write transactional updates to the target database (Silver DB)
                logger.info(
                    f"Writing relational transaction for batch ID {request_id}: "
                    f"makes={len(makes)}, classes={len(classes)}, models={len(batch_cleaned_models)}"
                )
                
                try:
                    _, _, models_inserted = db_manager.load_normalized_data(
                        makes=makes,
                        classes=classes,
                        models=batch_cleaned_models
                    )
                    total_records_inserted += models_inserted
                    logger.info(f"Loaded {models_inserted} new car models into target_db.")
                except Exception as load_err:
                    logger.error(
                        f"Failed to load normalized transaction block for batch ID {request_id}: {load_err}"
                    )
                    # We continue to let other batches process, but remove from processed list so it can be retried
                    processed_request_ids.remove(request_id)

            # 8. Mark all processed batches in Bronze DB to prevent duplicate processing
            if processed_request_ids:
                logger.info(f"Updating processed flag for request IDs: {processed_request_ids}")
                db_manager.mark_batches_processed(processed_request_ids)

    except Exception as db_err:
        logger.critical(f"ETL Execution halted due to database connection fault: {db_err}")
        sys.exit(1)

    # 9. Log execution stats summary
    logger.info("Transformation cycle complete.")
    logger.info(
        f"ETL Run Summary: Processed={total_batches_processed} batches, "
        f"Read={total_records_read} raw records, Validated={total_records_valid} records, "
        f"Inserted={total_records_inserted} relational rows."
    )
    
if __name__ == "__main__":
    run_transform_pipeline()
