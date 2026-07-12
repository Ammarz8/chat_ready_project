import logging
from typing import List, Dict, Any, Optional
import requests
from extractor.auth import APIKeyAuthenticator
from extractor.utils import retry_api_request

logger = logging.getLogger(__name__)

class CarsAPIClient:
    """
    HTTP Client for interacting with the API Ninjas Cars REST API.
    Handles communication, requests, headers injection, and response parsing.
    """
    BASE_URL = "https://api.api-ninjas.com/v1/cars"

    def __init__(self, authenticator: APIKeyAuthenticator, timeout_seconds: int = 15):
        """
        Initializes the client with dependency injection of authenticator.
        
        Args:
            authenticator (APIKeyAuthenticator): Authenticator instance.
            timeout_seconds (int): Maximum timeout threshold for API responses.
        """
        self._authenticator = authenticator
        self._timeout = timeout_seconds

    @retry_api_request(max_retries=5, base_delay=2.0)
    def fetch_cars(
        self, 
        make: str, 
        year: int, 
        model: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetches vehicle specifications from the API Ninjas Cars API.
        
        Args:
            make (str): Manufacturer name (e.g. toyota).
            year (int): Production year (e.g. 2022).
            model (Optional[str]): Specific model name (optional).
            limit (Optional[int]): Max records per request (premium only).
            
        Returns:
            List[Dict[str, Any]]: List of parsed JSON car specification objects.
        """
        headers = self._authenticator.get_auth_headers()
        params = {
            "make": make,
            "year": year
        }
        if limit is not None:
            params["limit"] = limit
        if model:
            params["model"] = model

        logger.info(f"Requesting API Ninjas Cars API: make={make}, year={year}, limit={limit}")
        
        try:
            response = requests.get(
                self.BASE_URL,
                headers=headers,
                params=params,
                timeout=self._timeout
            )
            
            # This raises HTTPError if status code is 4xx or 5xx
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully retrieved {len(data)} records for make={make}, year={year}")
            
            # The API returns an array of objects
            if not isinstance(data, list):
                raise TypeError(f"Expected API JSON response list, got {type(data)}")
                
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP Request failed for make={make}, year={year}: {e}")
            raise
