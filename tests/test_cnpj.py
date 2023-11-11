import unittest
from unittest.mock import MagicMock, Mock, patch

import httpx

from kami_dataset_validator.validators.cnpj import (
    APIConfigError,
    APIRequestError,
    CnpjAPI,
    CNPJValidator,
    CNPJValueError,
)


class TestCNPJValidator(unittest.TestCase):
    def test_init_valid_cnpj(self):
        """Test initialization with a valid CNPJ."""
        cnpj = '00.000.000/0000-00'  # Use a valid CNPJ format
        validator = CNPJValidator(cnpj)
        self.assertEqual(validator.cnpj, cnpj)

    def test_sanitize_cnpj(self):
        """Test the CNPJ sanitization process."""
        cnpj = '00.000.000/0000-00'
        expected_sanitized_cnpj = '00000000000000'
        validator = CNPJValidator(cnpj)
        self.assertEqual(validator.sanitized_cnpj, expected_sanitized_cnpj)

    def test_validate_cnpj(self):
        """Test CNPJ validation process."""
        cnpj = '11.222.333/0001-81'  # Use a valid CNPJ number
        validator = CNPJValidator(cnpj)
        self.assertTrue(validator.validate())

    def test_validate_cnpj_invalid_format(self):
        """Test CNPJ validation with invalid format."""
        cnpj = 'invalid_cnpj_format'
        with self.assertRaises(CNPJValueError):
            CNPJValidator(cnpj)

    def test_validate_cnpj_invalid_length(self):
        """Test CNPJ validation with invalid length."""
        cnpj = '1234567890'
        with self.assertRaises(CNPJValueError):
            CNPJValidator(cnpj)


class TestConsultaCnpjAPI(unittest.TestCase):
    def test_init_invalid_webservice(self):
        """Test initialization with an invalid webservice."""
        with self.assertRaises(APIConfigError):
            CnpjAPI(webservice='unknown_api')

    @patch('httpx.Client.get')
    def test_fetch_company_info_success(self, mock_get):
        """Test successful fetch of company info."""
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: {'cnpj': '12345678000195'}
        )
        api = CnpjAPI(cnpj_list=['12.345.678/0001-95'])
        response = api.fetch_company_info('12345678000195')
        self.assertEqual(response, {'cnpj': '12345678000195'})

    @patch('httpx.Client.get')
    def test_fetch_company_info_failure(self, mock_get):
        """Test fetch company info failure due to HTTP error."""
        mock_get.side_effect = httpx.HTTPStatusError(
            'Not Found', request=MagicMock(), response=MagicMock()
        )
        api = CnpjAPI(cnpj_list=['12345678901234'])
        with self.assertRaises(APIRequestError):
            api.fetch_company_info('12345678901234')

    def test_cnpj_match(self):
        """Test CNPJ matching process."""
        api = CnpjAPI()
        self.assertTrue(
            api._cnpj_match('12.345.678/0001-95', {'cnpj': '12345678000195'})
        )

    @patch.object(
        CnpjAPI, 'fetch_company_info', return_value={'cnpj': '12345678000195'}
    )
    @patch.object(CNPJValidator, 'validate', return_value=True)
    def test_validate_cnpj(self, mock_validate, mock_fetch):
        """Test CNPJ validation process."""
        api = CnpjAPI(cnpj_list=['12.345.678/0001-95'])
        result = api.validate_cnpj('12.345.678/0001-95')
        self.assertTrue(result['valid'])

    @patch.object(CnpjAPI, 'validate_cnpj')
    def test_validate_cnpjs(self, mock_validate_cnpj):
        """Test CNPJ validation for multiple CNPJs."""
        mock_validate_cnpj.side_effect = lambda cnpj: {
            'cnpj': cnpj,
            'valid': True,
        }
        cnpjs = ['12.345.678/0001-95', '98.765.432/0001-10']
        api = CnpjAPI(cnpj_list=cnpjs)
        results = api.validate_cnpjs()
        self.assertEqual(len(results), len(cnpjs))
        for result in results:
            self.assertTrue(result['valid'])


if __name__ == '__main__':
    unittest.main()
