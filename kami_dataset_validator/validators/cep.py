import json
import logging
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Union

import httpx
from kami_logging import benchmark_with, logging_with
from pyUFbr.baseuf import ufbr

from kami_dataset_validator.constants import KEY_TRANSLATIONS

cepapi_logger = logging.getLogger('Address Validator')


class CEPFormatError(Exception):
    """Raised when find a invalid CEP format."""

    pass


class InvalidAddressInputError(Exception):
    """
    Raised when the input data for an address is invalid or insufficient.
    """

    pass


class APIRequestError(Exception):
    """Custom exception for errors during the API request."""

    pass


class APIConfigError(Exception):
    """Exception raised for invalid API configurations."""

    pass


class Address:
    def __init__(
        self,
        cep: Optional[str] = None,
        street: Optional[str] = None,
        complement: Optional[str] = None,
        district: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        ibge: Optional[str] = None,
        gia: Optional[str] = None,
        ddd: Optional[str] = None,
        siafi: Optional[str] = None,
    ):
        self.cep = cep
        self.street = street
        self.complement = complement
        self.district = district
        self.city = city
        self.state = state
        self.ibge = ibge
        self.gia = gia
        self.ddd = ddd
        self.siafi = siafi

    @classmethod
    def _sanitize_cep(cls, cep: str) -> str:
        """
        Sanitize the CEP number.

        Returns:
            str: Sanitized CEP number.

        Raises:
            CEPFormatError: If the CEP is invalid.
        """
        if not cep:
            raise CEPFormatError('CEP cannot be empty.')

        sanitized_cep = cep.replace('-', '').replace('.', '').replace(' ', '')

        if len(sanitized_cep) != 8:
            raise CEPFormatError(
                f'Invalid CEP: {cep}. A valid CEP must have 8 numbers.'
            )

        if not sanitized_cep.isdigit():
            raise CEPFormatError(
                f'Invalid CEP: {cep}. A CEP must contain only numbers.'
            )

        return sanitized_cep

    @classmethod
    def from_dict(cls, addr_dict: Dict[str, str]) -> 'Address':
        """
        Create an Address instance from a dictionary.

        Args:
            addr_dict (Dict[str, str]): Dictionary representing an address.

        Returns:
            Address: An Address instance.
        """
        if 'cep' in addr_dict:
            addr_dict['cep'] = cls._sanitize_cep(addr_dict['cep'])
        elif (
            'logradouro' in addr_dict
            and 'localidade' in addr_dict
            and 'uf' in addr_dict
        ):
            cls._validate_locality(addr_dict['localidade'], addr_dict['uf'])
        else:
            raise InvalidAddressInputError(
                "Address dictionary must have either 'cep' or 'logradouro', 'localidade', and 'uf'."
            )

        translated_dict = cls._translate_keys(addr_dict, KEY_TRANSLATIONS)
        return cls(**translated_dict)

    @staticmethod
    def _translate_keys(
        input_dict: Dict[str, str], translation_dict: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Translate dictionary keys based on a given translation dictionary.

        Args:
            input_dict (Dict[str, str]): Dictionary to translate.
            translation_dict (Dict[str, str]): Dictionary for key translations.

        Returns:
            Dict[str, str]: Translated dictionary.
        """
        return {
            translation_dict.get(key, key): value
            for key, value in input_dict.items()
        }

    def sanitize_cep(self) -> bool:
        """
        Sanitize the CEP number.

        Returns:
            bool: True if the CEP is valid, False otherwise.
        """
        try:
            self.cep = Address._sanitize_cep(self.cep)
        except CEPFormatError as e:
            raise e
        except Exception as e:
            raise e
        return True

    def _validate_uf(self) -> bool:
        """
        Validate if the given UF is valid.

        Args:
            uf (str): State abbreviation.

        Returns:
            bool: True if valid, False otherwise.
        """
        valid_ufs = ufbr.list_uf

        if not self.state:
            raise InvalidAddressInputError('State cannot be empty.')

        if self.state not in valid_ufs:
            raise InvalidAddressInputError(f'Invalid State: {self.state}.')

        return True

    def _validate_locality(self) -> bool:
        self.city = str.upper(self.city)
        self.state = str.upper(self.state)
        """
        Validate if the given locality (city) exists in the provided UF.

        Args:
            locality (str): Name of the city.
            uf (str): State abbreviation (optional).

        Returns:
            bool: True if valid, False otherwise.
        """
        if not self.state:
            raise InvalidAddressInputError('UF cannot be empty.')

        if not self.city:
            raise InvalidAddressInputError('Locality cannot be empty.')

        self._validate_uf()
        cities_in_uf = ufbr.list_cidades(self.state)

        if self.city not in cities_in_uf:
            raise InvalidAddressInputError(
                f'Invalid City: {self.city} for State: {self.state}.'
            )

        else:
            valid_ufs = ufbr.list_uf
            valid = any(
                self.city in ufbr.list_cidades(current_uf)
                for current_uf in valid_ufs
            )

            if not valid:
                raise InvalidAddressInputError(
                    f'Invalid locality: {self.city}. Not found in any UF.'
                )

        return True

    def validate_cep(self) -> Dict[str, any]:
        """
        Validate the CEP number without using external API.

        Returns:
            Dict[str, any]: A dictionary containing the validation result and reason.
        """
        result = {
            'cep': self.cep,
            'valid': False,
            'reason': 'Invalid CEP format.',
        }

        try:
            if self.cep:
                if self._sanitize_cep(self.cep):
                    result['valid'] = True
                    result['reason'] = 'Valid CEP format.'
            else:
                result['reason'] = 'CEP not provided.'
        except CEPFormatError as e:
            result['reason'] = str(e)
        except Exception as e:
            result['reason'] = f'An unexpected error occurred: {str(e)}'

        return result

    def to_dict(self) -> Dict[str, str]:
        """
        Convert Address instance to dictionary with keys in Portuguese.

        Returns:
            Dict[str, str]: Dictionary representation of the address.
        """
        address_dict = {
            'cep': self.cep,
            'logradouro': self.street,
            'complemento': self.complement,
            'bairro': self.district,
            'localidade': self.city,
            'uf': self.state,
            'ibge': self.ibge,
            'gia': self.gia,
            'ddd': self.ddd,
            'siafi': self.siafi,
        }

        reverse_translation = {v: k for k, v in KEY_TRANSLATIONS.items()}
        return self._translate_keys(address_dict, reverse_translation)


CEP_WEBSERVICES = {
    'viacep': {
        'name': 'ViaCEP',
        'BASE_URL': 'https://viacep.com.br/ws/{}/json/',
        'supports_address': True,
    },
    'brasilaberto': {
        'name': 'Brasil_Aberto',
        'BASE_URL': 'https://brasilaberto.com/api/v1/zipcode/{}',
        'supports_address': False,
    },
    'opencep': {
        'name': 'OpenCEP',
        'BASE_URL': 'https://opencep.com/v1/{}',
        'supports_address': False,
    },
    'brasilapi': {
        'name': 'BrasilAPI',
        'BASE_URL': 'https://brasilapi.com.br/api/cep/v2/{}',
        'supports_address': False,
    },
}


class CepAPI:
    available_webservices = [
        str.lower(webservice['name'])
        for webservice in CEP_WEBSERVICES.values()
    ]

    def __init__(
        self, addresses: List[Address] = [], webservice: str = 'brasilapi'
    ):
        if webservice not in CEP_WEBSERVICES:
            raise APIConfigError(
                f"Unsupported webservice '{webservice}'. Supported services are: {list(CEP_WEBSERVICES.keys())}"
            )
        self.addresses = addresses
        self.results = []
        self.webservice = webservice
        self.base_url = CEP_WEBSERVICES[webservice]['BASE_URL']

    def _fetch_by_cep(self, cep: str) -> Union[Dict[str, str], None]:
        with httpx.Client() as client:
            url = self.base_url.format(cep)
            cepapi_logger.info(
                f'Fetching data from {str.upper(self.webservice)} for CEP: {cep}'
            )
            cepapi_logger.info(f'URL: {url}')
            try:
                response = client.get(url)
                if response.status_code != 200:
                    raise APIRequestError(
                        f'Failed to fetch data from {url} of {str.upper(self.webservice)}.'
                    )
                response.raise_for_status()
                return response.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                raise APIRequestError(
                    f"An error occurred while requesting '{url}' from {str.upper(self.webservice)}: {exc}"
                ) from exc

    def _compute_similarity(self, addr1: Address, addr2: Address) -> float:
        attributes = [
            'cep',
            'street',
            'complement',
            'district',
            'city',
            'state',
            'ibge',
            'gia',
            'ddd',
            'siafi',
        ]
        ratios = []

        for attr in attributes:
            attr1, attr2 = getattr(addr1, attr, ''), getattr(addr2, attr, '')
            if attr1 and attr2:
                similarity = SequenceMatcher(None, attr1, attr2).ratio()
                ratios.append(similarity)

        if not ratios:
            return 0

        return round(sum(ratios) / len(ratios), 3)

    @benchmark_with(cepapi_logger)
    @logging_with(cepapi_logger)
    def filter_addresses_by_similarity(
        self, target_address: Address, search_addresses: List[Address]
    ) -> List[Dict]:
        similarities = []

        for address in search_addresses:
            similarity_ratio = self._compute_similarity(
                target_address, address
            )
            if similarity_ratio > 0:
                similarities.append(
                    {
                        'similarity_ratio': similarity_ratio,
                        'address': address.to_dict(),
                    }
                )

        return sorted(
            similarities, key=lambda x: x['similarity_ratio'], reverse=True
        )

    def _suports_address(self) -> bool:
        return CEP_WEBSERVICES[self.webservice]['supports_address']

    @benchmark_with(cepapi_logger)
    @logging_with(cepapi_logger)
    def validate_address(
        self, address: Address, suggest_cep: bool = False
    ) -> Dict:
        result = {
            'address': address.to_dict(),
            'valid': False,
            'reason': '',
        }

        try:
            if address.sanitize_cep():
                data = self._fetch_by_cep(address.cep)
                if data['cep']:
                    result['valid'] = True
                    result['reason'] = 'Valid CEP.'
            elif (
                address.street
                and address.city
                and address.state
                and self._suports_address()
            ):
                data = self._fetch_by_address(
                    address.state, address.city, address.street
                )
                if data:
                    if len(data) == 1:
                        found_address = Address.from_dict(data[0])
                        result['valid'] = True
                        result[
                            'reason'
                        ] = f'The only CEP suggested for this address was: {found_address.cep}'
                    elif len(data) > 1:
                        valid_count = len(
                            self.filter_addresses_by_similarity(
                                address,
                                [Address.from_dict(item) for item in data],
                            )
                        )
                        if valid_count > 0:
                            result['valid'] = True
                            result[
                                'reason'
                            ] = f'{valid_count} valid CEPs were found for this address.'
                            if suggest_cep:
                                result[
                                    'reason'
                                ] += f' Addresses: {json.dumps(data)}'
                        else:
                            result[
                                'reason'
                            ] = 'No valid CEPs found for this address.'
                else:
                    result['reason'] = 'No data found for the given address.'
            elif address.cep and not address.sanitize_cep():
                result['reason'] = 'Invalid CEP.'
            else:
                result['reason'] = 'Insufficient address information.'
        except (
            CEPFormatError,
            InvalidAddressInputError,
            APIRequestError,
        ) as e:
            result['reason'] = str(e)

        return result

    @benchmark_with(cepapi_logger)
    @logging_with(cepapi_logger)
    def validate_addresses(self, suggest_cep: bool = False) -> None:
        self.results = [
            self.validate_address(address, suggest_cep)
            for address in self.addresses
        ]
