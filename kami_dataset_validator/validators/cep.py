import httpx
from typing import Dict, List, Optional, Union
from difflib import SequenceMatcher
import logging
from kami_logging import benchmark_with, logging_with

viacep_logger = logging.getLogger('CEP Validator')

class CEPFormatError(Exception):
    """Custom exception for invalid CEP format."""
    pass

class InvalidAddressInputError(Exception):
    """Custom exception for invalid address input format or values."""
    pass

class APIRequestError(Exception):
    """Custom exception for errors during the API request."""

    def __init__(self, status_code: int, message: str):
        super().__init__(f"HTTP Error {status_code}: {message}")
        self.status_code = status_code


class ViaCepAPI:
    """
    A class to interface with the ViaCep API to fetch and filter address-related information.
    
    Attributes:
        BASE_URL (str): Base endpoint for the ViaCep API.
        cep (str): Postal code of the address.
        street (str): Street name of the address.
        reference (str): Reference point of the address (not provided by API).
        district (str): District name of the address.
        city (str): City name of the address.
        state (str): State name of the address.
        ibge (str): IBGE code of the address.
        gia (str): GIA code of the address.
        ddd (str): DDD code of the address.
        siafi (str): SIAFI code of the address.
    """
    
    BASE_URL = "https://viacep.com.br/ws"

    def __init__(self):
        """Initialize the ViaCepAPI object with None values for its attributes."""
        self.cep: Optional[str] = None
        self.street: Optional[str] = None
        self.reference: Optional[str] = None
        self.district: Optional[str] = None
        self.city: Optional[str] = None
        self.state: Optional[str] = None
        self.ibge: Optional[str] = None
        self.gia: Optional[str] = None
        self.ddd: Optional[str] = None
        self.siafi: Optional[str] = None

    def _sanitize_cep(self, cep: str) -> str:
        """
        Sanitize and validate the given CEP.
        
        Parameters:
            cep (str): Postal code to be sanitized.
            
        Returns:
            str: Sanitized postal code.
            
        Raises:
            CEPFormatError: If the CEP format is invalid.
        """
        sanitized_cep = cep.replace(".", "").replace("-", "")
        if len(sanitized_cep) != 8:
            raise CEPFormatError("Invalid CEP format. The CEP must have exactly 8 characters.")
        if not sanitized_cep.isdigit():
            raise CEPFormatError("Invalid CEP format. Only numbers are accepted.")
        return sanitized_cep

    @benchmark_with(viacep_logger)
    @logging_with(viacep_logger)
    def _fetch_data_from_url(self, url: str) -> Union[Dict[str, str], List[Dict[str, str]]]:
        """
        Fetch data from the specified URL.
        
        Parameters:
            url (str): The endpoint to fetch data from.
            
        Returns:
            Union[Dict[str, str], List[Dict[str, str]]]: Parsed JSON data from the response.
            
        Raises:
            APIRequestError: If there's an error in the request.
        """
        try:
            response = httpx.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise APIRequestError(e.response.status_code, e.response.text)

    def _compute_similarity(self, search_addr: Dict[str, str], addr: Dict[str, str]) -> float:
        """
        Compute similarity between two address dictionaries.
        
        Parameters:
            search_addr (Dict[str, str]): The reference address dictionary.
            addr (Dict[str, str]): The target address dictionary to compare.
            
        Returns:
            float: The similarity score between the two dictionaries.
        """
        similarities = []
        for key in ["street", "district", "city", "state", "ddd"]:
            search_value = search_addr.get(key)
            value = addr.get(key)
            if search_value and value:
                ratio = SequenceMatcher(None, search_value, value).ratio()
                similarities.append(ratio)
        if not similarities:
            return 0.0
        return round(sum(similarities) / len(similarities), 3)

    @benchmark_with(viacep_logger)
    @logging_with(viacep_logger)
    def filter_get_address_results(self, search_address: Dict[str, str], address_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Filter and sort the address list based on similarity scores.
        
        Parameters:
            search_address (Dict[str, str]): The reference address dictionary to filter upon.
            address_list (List[Dict[str, str]]): The list of address dictionaries to be filtered.
            
        Returns:
            List[Dict[str, str]]: Filtered and sorted address list based on similarity scores.
            
        Raises:
            InvalidAddressInputError: If the search address is invalid.
        """
        if not isinstance(search_address, dict) or all(v is None for v in search_address.values()):
            raise InvalidAddressInputError("Invalid search address input. At least one key must have a value.")

        for addr in address_list:
            addr['tx_similarity'] = self._compute_similarity(search_address, addr)
        
        sorted_filtered_addresses = sorted([addr for addr in address_list if addr['tx_similarity'] > 0], key=lambda x: x['tx_similarity'], reverse=True)
        return sorted_filtered_addresses

    @benchmark_with(viacep_logger)
    @logging_with(viacep_logger)
    def get_address_from_cep(self, cep: str) -> Optional[Dict[str, str]]:
        """
        Get the address for a specific CEP.
        
        Parameters:
            cep (str): Postal code to search for.
            
        Returns:
            Optional[Dict[str, str]]: Address dictionary corresponding to the CEP or None if not found.
        """
        sanitized_cep = self._sanitize_cep(cep)
        url = f"{self.BASE_URL}/{sanitized_cep}/json"
        data = self._fetch_data_from_url(url)
        if data and "erro" not in data:
            self.cep = data.get("cep")
            self.street = data.get("logradouro")
            self.district = data.get("bairro")
            self.city = data.get("localidade")
            self.state = data.get("uf")
            self.ibge = data.get("ibge")
            self.gia = data.get("gia")
            self.ddd = data.get("ddd")
            self.siafi = data.get("siafi")
            viacep_logger.info(f"Address obtained for CEP: {cep}")
            return data
        viacep_logger.info(f"No address found for CEP: {cep}")
        return None

    @benchmark_with(viacep_logger)
    @logging_with(viacep_logger)
    def get_cep_from_address(self, state: str, city: str, address: str) -> List[Dict[str, str]]:
        """
        Get a list of CEPs for a given address.
        
        Parameters:
            state (str): The state of the address.
            city (str): The city of the address.
            address (str): The specific address or street.
            
        Returns:
            List[Dict[str, str]]: List of address dictionaries corresponding to the provided details.
        """
        url = f"{self.BASE_URL}/{state}/{city}/{address}/json"
        data = self._fetch_data_from_url(url)
        if data:
            viacep_logger.info(f"Addresses obtained for {state} {city} {address}")
            return data
        viacep_logger.info(f"No addresses found for {state} {city} {address}")
        return []