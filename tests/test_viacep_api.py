import unittest
from unittest.mock import patch, Mock
from viacep_api import ViaCepAPI, CEPFormatError, InvalidAddressInputError, APIRequestError

class TestViaCepAPI(unittest.TestCase):
    
    def setUp(self):
        self.api = ViaCepAPI()
    
    @patch("viacep_api.httpx.get")
    def test_get_address_from_cep_success(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=lambda: {"cep": "12345678", "logradouro": "Sample Street"})
        response = self.api.get_address_from_cep("12345678")
        self.assertEqual(response["cep"], "12345678")
        self.assertEqual(response["logradouro"], "Sample Street")

    def test_sanitize_cep_success(self):
        response = self.api._sanitize_cep("1234-5678")
        self.assertEqual(response, "12345678")

    def test_sanitize_cep_failure_format(self):
        with self.assertRaises(CEPFormatError):
            self.api._sanitize_cep("12345-678")

    def test_sanitize_cep_failure_non_digit(self):
        with self.assertRaises(CEPFormatError):
            self.api._sanitize_cep("123A-5678")

    @patch("viacep_api.httpx.get")
    def test_get_address_from_cep_failure_api_error(self, mock_get):
        mock_get.return_value = Mock(raise_for_status=lambda: self._raise_http_status_error())
        with self.assertRaises(APIRequestError):
            self.api.get_address_from_cep("12345678")
    
    @patch("viacep_api.httpx.get")
    def test_get_cep_from_address_success(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=lambda: [{"cep": "12345678", "logradouro": "Sample Street"}])
        response = self.api.get_cep_from_address("SP", "Sao Paulo", "Sample Street")
        self.assertEqual(response[0]["cep"], "12345678")
        self.assertEqual(response[0]["logradouro"], "Sample Street")
    
    @patch("viacep_api.httpx.get")
    def test_get_cep_from_address_failure_api_error(self, mock_get):
        mock_get.return_value = Mock(raise_for_status=lambda: self._raise_http_status_error())
        with self.assertRaises(APIRequestError):
            self.api.get_cep_from_address("SP", "Sao Paulo", "Sample Street")
    
    def test_filter_get_address_results_success(self):
        search_address = {"street": "Sample"}
        address_list = [{"logradouro": "Sample Street", "bairro": "Sample District", "localidade": "Sample City", "uf": "SP", "ddd": "11"}]
        response = self.api.filter_get_address_results(search_address, address_list)
        self.assertEqual(response[0]["logradouro"], "Sample Street")
    
    def test_filter_get_address_results_failure_invalid_input(self):
        with self.assertRaises(InvalidAddressInputError):
            self.api.filter_get_address_results({}, [])

    def _raise_http_status_error(self):
        raise Exception("HTTPStatusError")

if __name__ == "__main__":
    unittest.main()
