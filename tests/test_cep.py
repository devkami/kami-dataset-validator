import unittest
from unittest.mock import MagicMock, patch

import httpx

from kami_dataset_validator.validators.cep import (
    Address,
    APIConfigError,
    APIRequestError,
    CepAPI,
    CEPFormatError,
    InvalidAddressInputError,
)

mocked_ufs = ['SP', 'RJ']
mocked_cities = {
    'SP': ['SAO PAULO', 'CAMPINAS'],
    'RJ': ['RIO DE JANEIRO', 'NITEROI'],
}


class MockedUFBR:
    list_uf = mocked_ufs

    @staticmethod
    def list_cidades(uf):
        return mocked_cities.get(uf, [])


class TestAddress(unittest.TestCase):
    @patch(
        'kami_dataset_validator.validators.cep.ufbr', new_callable=MockedUFBR
    )
    def setUp(self, mocked_ufbr):
        self.address_dict = {
            'cep': '12345-678',
            'logradouro': 'Street A',
            'complemento': 'Apt 101',
            'bairro': 'Downtown',
            'localidade': 'SAO PAULO',
            'uf': 'SP',
            'ibge': '12345',
            'gia': '123',
            'ddd': '011',
            'siafi': '1234',
        }

    @patch(
        'kami_dataset_validator.validators.cep.ufbr', new_callable=MockedUFBR
    )
    def test_sanitize_cep_success(self, mocked_ufbr):
        address = Address(cep='12345-678')
        self.assertEqual(address.sanitize_cep(), True)

    def test_sanitize_cep_invalid_format(self):
        address = Address(cep='12345-XYZ')
        with self.assertRaises(CEPFormatError):
            address.sanitize_cep()

    def test_sanitize_cep_invalid_length(self):
        address = Address(cep='12345-6')
        with self.assertRaises(CEPFormatError):
            address.sanitize_cep()

    def test_from_dict_success(self):
        address = Address.from_dict(self.address_dict)
        self.assertEqual(address.street, 'Street A')

    def test_from_dict_invalid_cep(self):
        invalid_cep_dict = self.address_dict.copy()
        invalid_cep_dict['cep'] = '12345-XYZ'
        with self.assertRaises(CEPFormatError):
            Address.from_dict(invalid_cep_dict)

    def test_from_dict_missing_keys(self):
        incomplete_dict = {'localidade': 'Bangu'}
        with self.assertRaises(InvalidAddressInputError):
            Address.from_dict(incomplete_dict)

    @patch(
        'kami_dataset_validator.validators.cep.ufbr', new_callable=MockedUFBR
    )
    def test_validate_uf_success(self, mocked_ufbr):
        address = Address(state='SP')
        self.assertTrue(address._validate_uf())

    @patch(
        'kami_dataset_validator.validators.cep.ufbr', new_callable=MockedUFBR
    )
    def test_validate_uf_invalid(self, mocked_ufbr):
        address = Address(state='AB')
        with self.assertRaises(InvalidAddressInputError):
            address._validate_uf()

    @patch(
        'kami_dataset_validator.validators.cep.ufbr', new_callable=MockedUFBR
    )
    def test_validate_locality_success(self, mocked_ufbr):
        address = Address(city='SAO PAULO', state='SP')
        self.assertTrue(address._validate_locality())

    @patch(
        'kami_dataset_validator.validators.cep.ufbr', new_callable=MockedUFBR
    )
    def test_validate_locality_invalid_city(self, mocked_ufbr):
        address = Address(city='UNKNOWN CITY', state='SP')
        with self.assertRaises(InvalidAddressInputError):
            address._validate_locality()


class TestCepAPI(unittest.TestCase):
    def setUp(self):
        self.address1 = Address(cep='01000000', city='São Paulo', state='SP')
        self.address2 = Address(cep='02000000', city='São Paulo', state='SP')

    def test_init_invalid_webservice(self):
        """Test initialization with an invalid webservice."""
        with self.assertRaises(APIConfigError):
            CepAPI(webservice='unknown_api')

    @patch('httpx.Client.get')
    def test_fetch_by_cep_success(self, mock_get):
        """Test successful fetch by CEP."""
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: {'cep': '01000000'}
        )
        api = CepAPI()
        response = api._fetch_by_cep('01000000')
        self.assertEqual(response, {'cep': '01000000'})

    @patch('httpx.Client.get')
    def test_fetch_by_cep_failure(self, mock_get):
        """Test fetch by CEP failure due to HTTP error."""
        mock_get.side_effect = httpx.HTTPStatusError(
            'Not Found', request=MagicMock(), response=MagicMock()
        )
        api = CepAPI()
        with self.assertRaises(APIRequestError):
            api._fetch_by_cep('01000000')

    def test_compute_similarity(self):
        """Test computing similarity between two addresses."""
        api = CepAPI()
        similarity = api._compute_similarity(self.address1, self.address2)
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)

    def test_filter_addresses_by_similarity(self):
        """Test filtering addresses by similarity."""
        api = CepAPI()
        search_addresses = [self.address1, self.address2]
        results = api.filter_addresses_by_similarity(
            self.address1, search_addresses
        )
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1)
        self.assertGreaterEqual(results[0]['similarity_ratio'], 0.0)

    def test_supports_address(self):
        """Test checking if the webservice supports address fetching."""
        api = CepAPI(webservice='viacep')
        self.assertTrue(api._suports_address())

    @patch('kami_dataset_validator.validators.cep.CepAPI._fetch_by_cep')
    def test_validate_address(self, mock_fetch_by_cep):
        """Test validating an address."""
        mock_fetch_by_cep.return_value = {'cep': '01000000'}
        api = CepAPI()
        result = api.validate_address(self.address1)
        self.assertTrue(result['valid'])

    @patch('kami_dataset_validator.validators.cep.CepAPI.validate_address')
    def test_validate_addresses(self, mock_validate_address):
        """Test validating multiple addresses."""
        mock_validate_address.return_value = {
            'valid': True,
            'address': self.address1.to_dict(),
        }
        api = CepAPI(addresses=[self.address1])
        api.validate_addresses()
        self.assertIsInstance(api.results, list)
        self.assertEqual(len(api.results), 1)
        self.assertTrue(api.results[0]['valid'])


if __name__ == '__main__':
    unittest.main()
