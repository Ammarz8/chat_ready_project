class APIKeyAuthenticator:
    """
    Handles API Ninjas authentication. 
    Prepares and injects the authorization headers for REST requests.
    """
    def __init__(self, api_key: str):
        if not api_key or not isinstance(api_key, str):
            raise ValueError("A valid API key string must be provided.")
        self._api_key = api_key

    def get_auth_headers(self) -> dict:
        """
        Generates the headers dictionary with authentication credentials.
        
        Returns:
            dict: The HTTP headers containing the X-Api-Key.
        """
        return {
            "X-Api-Key": self._api_key,
            "Accept": "application/json"
        }
