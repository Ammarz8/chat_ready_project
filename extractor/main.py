import sys
import logging
from extractor.config import ExtractorConfig
from extractor.logger import setup_logger
from extractor.auth import APIKeyAuthenticator
from extractor.api import CarsAPIClient
from extractor.database import SourceDatabaseClient

logger = logging.getLogger("extractor")

def run_pipeline() -> None:
    """
    Main orchestration function for the Ingestion layer (Extractor).
    Initializes components, loops through targeted criteria, triggers HTTP fetches,
    and commits raw responses to the landing zone database (Bronze layer).
    """
    # 1. Load configurations
    try:
        config = ExtractorConfig.from_env()
    except ValueError as e:
        # Fallback logging if configuration loading fails before logger is initialized
        logging.basicConfig(level=logging.ERROR)
        logging.error(f"Failed to load environment configurations: {e}")
        sys.exit(1)

    # 2. Initialize logging settings
    setup_logger(config.log_level)
    logger.info("Starting API Ninjas Cars Extractor Service Ingestion cycle...")

    # 3. Instantiate authentication and client components
    authenticator = APIKeyAuthenticator(config.api_key)
    api_client = CarsAPIClient(authenticator)
    db_client = SourceDatabaseClient(config)

    # Process metrics
    batches_success = 0
    batches_failure = 0
    records_saved = 0

    logger.info(
        f"Ingestion criteria: target_makes={config.target_makes}, "
        f"target_years={config.target_years}"
    )

    # 4. Open connection context and run the extraction loop
    try:
        with db_client:
            for make in config.target_makes:
                for year in config.target_years:
                    logger.info(f"Extracting batch: make='{make}', year={year}")
                    try:
                        # Query the external Cars API
                        payload = api_client.fetch_cars(make=make, year=year)
                        
                        # Store raw results in Bronze DB (even if list is empty, to verify attempt)
                        db_client.insert_raw_request(
                            endpoint="/v1/cars",
                            parameters={"make": make, "year": year},
                            status_code=200,
                            payload=payload
                        )
                        
                        batches_success += 1
                        records_saved += len(payload)
                        
                    except Exception as api_err:
                        logger.error(
                            f"Extraction batch failed for make='{make}', year={year}: {api_err}"
                        )
                        batches_failure += 1
                        
                        # Determine response status code if available
                        status_code = 500
                        if hasattr(api_err, "response") and api_err.response is not None:
                            status_code = api_err.response.status_code
                            
                        # Record API attempt failure details in raw database for audit trail
                        try:
                            db_client.insert_raw_request(
                                endpoint="/v1/cars",
                                parameters={"make": make, "year": year},
                                status_code=status_code,
                                payload={"error": str(api_err)}
                            )
                        except Exception as db_err:
                            logger.critical(
                                f"Failed to record audit log in Bronze DB: {db_err}"
                            )
                            
    except Exception as db_conn_err:
        logger.critical(
            f"Fatal database connectivity fault. Aborting pipeline: {db_conn_err}"
        )
        sys.exit(1)

    # 5. Log lifecycle stats
    logger.info("Extraction loop complete.")
    logger.info(
        f"Ingestion Ingestion Summary: Success={batches_success} batches, "
        f"Failed={batches_failure} batches, Ingested={records_saved} raw records."
    )
    
    if batches_failure > 0:
        logger.warning("Pipeline run completed with one or more batch errors.")
        sys.exit(1)
    else:
        logger.info("Pipeline run completed successfully.")

if __name__ == "__main__":
    run_pipeline()
