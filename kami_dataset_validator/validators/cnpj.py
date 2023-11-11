import logging
from typing import Dict, List

import httpx
from kami_logging import benchmark_with, logging_with
from validate_docbr import CNPJ

from kami_dataset_validator.constants import CNPJ_WEBSERVICES

cnpjapi_logger = logging.getLogger('CNPJ Validator')


class CNPJValueError(Exception):
    """Exception raised when a CNPJ value is invalid."""

    pass


class APIRequestError(Exception):
    """Exception raised for failures during API requests."""

    pass


class APIConfigError(Exception):
    """Exception raised for invalid API configurations."""

    pass


class CNPJValidator:
    def __init__(self, cnpj: str):
        self.cnpj = cnpj
        self.sanitized_cnpj = self._sanitize_cnpj()

    def _sanitize_cnpj(self) -> str:
        sanitized_cnpj = (
            self.cnpj.replace('.', '')
            .replace('/', '')
            .replace('-', '')
            .replace(',', '')
        )

        if not sanitized_cnpj.isdigit():
            raise CNPJValueError(
                'Invalid CNPJ format. Ensure it contains only numbers.'
            )

        if len(sanitized_cnpj) != 14:
            raise CNPJValueError(
                'Invalid CNPJ length. Ensure it has 14 digits.'
            )

        return sanitized_cnpj

    def validate(self) -> bool:
        cnpj_validator = CNPJ()

        if not cnpj_validator.validate(self.sanitized_cnpj):
            raise CNPJValueError('The provided CNPJ is not valid.')

        return True


class CnpjAPI:
    def __init__(
        self,
        cnpj_list: List[str] = [],
        webservice: str = 'brasilapi',
    ):
        if webservice not in CNPJ_WEBSERVICES:
            raise APIConfigError(
                f"Unsupported webservice '{webservice}'. Supported services are: {list(CNPJ_WEBSERVICES.keys())}"
            )
        self.cnpj_list = cnpj_list
        self.results = []
        self.webservice = webservice
        self.base_url = CNPJ_WEBSERVICES[webservice]['BASE_URL']

    def fetch_company_info(self, cnpj: str) -> Dict:
        with httpx.Client() as client:
            url = self.base_url.format(cnpj)
            cnpjapi_logger.info(
                f'Fetching data from {str.upper(self.webservice)} for CNPJ: {cnpj}'
            )
            cnpjapi_logger.info(f'URL: {url}')
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

    def _sanitize_cnpj(self, cnpj: str) -> str:
        return (
            cnpj.replace('.', '')
            .replace('/', '')
            .replace('-', '')
            .replace(',', '')
        )

    def _cnpj_match(self, cnpj: str, response: Dict) -> bool:
        validator = CNPJValidator(cnpj)

        if self.webservice in ['brasilapi', 'receitaws']:
            response_cnpj = response.get('cnpj', '')
            sanitized_response_cnpj = self._sanitize_cnpj(response_cnpj)
            return validator.sanitized_cnpj == sanitized_response_cnpj
        elif self.webservice == 'brasilaberto':
            base_cnpj = response.get('result', {}).get('baseCnpj', '')
            return validator.sanitized_cnpj[:8] == base_cnpj[:8]
        return False

    def validate_cnpj(self, cnpj_str: str) -> Dict:
        result = {'cnpj': cnpj_str}
        try:
            validator = CNPJValidator(cnpj_str)
            if not validator.validate():
                result['valid'] = False
                result['reason'] = 'Invalid CNPJ.'
                return result

            company_info = self.fetch_company_info(validator.sanitized_cnpj)
            if not self._cnpj_match(validator.sanitized_cnpj, company_info):
                result['valid'] = False
                result[
                    'reason'
                ] = f'This CNPJ was not found in the API base {self.webservice}.'
            result['company_info'] = company_info
            result['valid'] = True
            result['reason'] = 'Valid CNPJ.'
        except (CNPJValueError, APIRequestError) as e:
            result['valid'] = False
            result['reason'] = str(e)
        except Exception as e:
            result['valid'] = False
            result['reason'] = str(e)
        finally:
            return result

    def validate_cnpjs(self) -> List[Dict]:
        results = []
        for cnpj in self.cnpj_list:
            result = self.validate_cnpj(cnpj)
            results.append(result)

        return results
