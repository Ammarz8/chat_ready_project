import unittest
from unittest.mock import patch, MagicMock
import requests
from extractor.auth import APIKeyAuthenticator
from extractor.config import ExtractorConfig
from extractor.api import CarsAPIClient

class TestExtractorComponents(unittest.TestCase):
    """
    Unit tests for Ingestion layer components (auth, config, api client).
    Uses unittest and standard mock libraries.
    """

    def test_authenticator_headers(self) -> None:
        """Verifies correct injection of the API-key header."""
        auth = APIKeyAuthenticator("test_api_key_123")
        headers = auth.get_auth_headers()
        self.assertEqual(headers["X-Api-Key"], "test_api_key_123")
        self.assertEqual(headers["Accept"], "application/json")

    def test_authenticator_invalid_key(self) -> None:
        """Ensures exception is raised when instantiating with blank keys."""
        with self.assertRaises(ValueError):
            APIKeyAuthenticator("")

    def test_config_invalid_port(self) -> None:
        """Verifies that non-integer port configurations raise ValueError on load."""
        env_vars = {
            "API_NINJAS_API_KEY": "valid_key",
            "SOURCE_DB_HOST": "localhost",
            "SOURCE_DB_PORT": "invalid_port_value",
            "SOURCE_DB_USER": "test_user",
            "SOURCE_DB_PASSWORD": "test_password",
            "SOURCE_DB_NAME": "test_db"
        }
        with patch.dict("os.environ", env_vars):
            with self.assertRaises(ValueError) as ctx:
                ExtractorConfig.from_env()
            self.assertIn("SOURCE_DB_PORT must be an integer", str(ctx.exception))

    @patch("requests.get")
    def test_client_fetch_success(self, mock_get: MagicMock) -> None:
        """Verifies that client returns list of dicts on successful requests."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {"make": "toyota", "model": "camry", "year": 2020, "cylinders": 4}
        ]
        mock_get.return_value = mock_resp

        auth = APIKeyAuthenticator("dummy_key")
        client = CarsAPIClient(auth)
        result = client.fetch_cars(make="toyota", year=2020)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["make"], "toyota")
        self.assertEqual(result[0]["model"], "camry")
        self.assertEqual(result[0]["year"], 2020)
        mock_get.assert_called_once()

    @patch("time.sleep")
    @patch("requests.get")
    def test_client_fetch_http_error(self, mock_get: MagicMock, mock_sleep: MagicMock) -> None:
        """Ensures that HTTP errors propagate through the client block."""
        # Setup mock to raise HTTPError when raise_for_status() is invoked
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_resp
        )
        mock_get.return_value = mock_resp

        auth = APIKeyAuthenticator("dummy_key")
        client = CarsAPIClient(auth)
        
        with self.assertRaises(requests.exceptions.HTTPError):
            client.fetch_cars(make="toyota", year=2020)
            
        self.assertEqual(mock_get.call_count, 5)
        self.assertEqual(mock_sleep.call_count, 4)
        
if __name__ == "__main__":
    unittest.main()
