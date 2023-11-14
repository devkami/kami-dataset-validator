import logging
import time
from typing import Dict, List, Optional

import polars as pl

from kami_dataset_validator.validators.cep import Address, CepAPI
from kami_dataset_validator.validators.cnpj import CnpjAPI, CNPJValidator
from kami_dataset_validator.validators.cpf import CPFValidator
from kami_dataset_validator.validators.email import EmailValidator
from kami_dataset_validator.validators.phone import PhoneValidator

validate_costumer_logger = logging.getLogger('Customer Validator')
default_validation = [
    {'name': 'CEP', 'external': True, 'webservice': 'opencep'},
    {'name': 'CNPJ', 'external': True, 'webservice': 'brasilapi'},
    {'name': 'CPF', 'external': False},
    {'name': 'Phone', 'external': False},
    {'name': 'Email', 'external': False},
]


class CustomerDataValidatorError(Exception):
    """Custom exception to be raised when there are issues with the data validation."""

    pass


class CustomerDataValidator:
    """A class to validate different aspects of customer data in a dataset.

    Attributes:
        dataset (pl.DataFrame): The dataset containing customer data.
        customer_id_colname (Optional[str]): Column name for customer ID.
        cep_colname (Optional[str]): Column name for CEP.
        street_colname (Optional[str]): Column name for street address.
        city_colname (Optional[str]): Column name for city.
        state_colname (Optional[str]): Column name for state.
        cpf_colname (Optional[str]): Column name for CPF.
        cnpj_colname (Optional[str]): Column name for CNPJ.
        phone_colname (Optional[str]): Column name for phone number.
        email_colnames (Optional[str]): List of column names for emails.

    Methods:
        _check_dataset: Checks if the dataset is valid.
        _check_column_existence: Checks if the required columns exist in the dataset.
        _create_cep_validation_dataset: Validates CEP using either an external API or internal logic.
        _check_address_validate: Checks if address validation can proceed.
        validate_address_from_cep: Validates addresses using CEP information.
        _create_cnpj_validation_dataset: Validates CNPJ using either an external API or internal logic.
        _check_cnpj_validate: Checks if CNPJ validation can proceed.
        validate_cnpjs: Validates CNPJ numbers in the dataset.
        _create_cpf_validation_dataset: Validates CPF numbers in the dataset.
        _check_cpf_validate: Checks if CPF validation can proceed.
        validate_cpfs: Validates CPF numbers in the dataset.
        _create_phone_validation_dataset: Validates phone numbers in the dataset.
        _check_phone_validate: Checks if phone number validation can proceed.
        validate_phones: Validates phone numbers in the dataset.
        _check_email_validate: Checks if email validation can proceed.
        _create_email_validation_dataset: Validates email addresses in the dataset.
        _validate_emails: Helper method for email validation.
        validate_emails: Validates email addresses in the dataset.
        validate_dataset: Validates the entire dataset and returns a combined DataFrame with validation results.
    """

    def __init__(
        self,
        dataset: pl.DataFrame,
        customer_id_colname: Optional[str],
        cep_colname: Optional[str],
        street_colname: Optional[str],
        city_colname: Optional[str],
        state_colname: Optional[str],
        cpf_colname: Optional[str],
        cnpj_colname: Optional[str],
        phone_colname: Optional[str],
        email_colnames: Optional[List[str]],
    ):
        """Initializes an instance of the CustomerDataValidator class, setting up the
        necessary attributes for subsequent data validation processes.

        Args:
            dataset (pl.DataFrame): The dataset containing customer data to be validated.
            customer_id_colname (Optional[str]): The name of the column in the dataset that contains customer IDs.
            cep_colname (Optional[str]): The name of the column in the dataset that contains CEP (Postal Code) values.
            street_colname (Optional[str]): The name of the column in the dataset that contains street address information.
            city_colname (Optional[str]): The name of the column in the dataset that contains city names.
            state_colname (Optional[str]): The name of the column in the dataset that contains state names or abbreviations.
            cpf_colname (Optional[str]): The name of the column in the dataset that contains CPF (Brazilian individual taxpayer registry) numbers.
            cnpj_colname (Optional[str]): The name of the column in the dataset that contains CNPJ (Brazilian main corporate tax identification) numbers.
            phone_colname (Optional[str]): The name of the column in the dataset that contains phone numbers.
            email_colnames (Optional[List[str]]): A list of column names in the dataset that contain email addresses.
        """
        self.dataset = dataset
        self.customer_id_colname = customer_id_colname
        self.cep_colname = cep_colname
        self.street_colname = street_colname
        self.city_colname = city_colname
        self.state_colname = state_colname
        self.cpf_colname = cpf_colname
        self.cnpj_colname = cnpj_colname
        self.phone_colname = phone_colname
        self.email_colnames = email_colnames

    def _check_dataset(self):
        """Checks if the dataset is valid, not empty or null, and raises an error if not.
        Raises:
            CustomerDataValidatorError: If the dataset is invalid.
        """

        if not isinstance(self.dataset, pl.DataFrame):
            raise CustomerDataValidatorError(
                'The dataset must be a polars DataFrame.'
            )

        if len(self.dataset) == 0:
            raise CustomerDataValidatorError('The dataset is empty.')

        if not self.customer_id_colname:
            raise CustomerDataValidatorError(
                'Customer id column name is not defined.'
            )

        if self.customer_id_colname not in self.dataset.columns:
            raise CustomerDataValidatorError(
                f'The dataset does not contain the customer id column: {self.customer_id_colname}'
            )

        return True

    def _check_column_existence(self, colnames: List[str]):
        """Checks if the required columns exist in the dataset and raises an error if not.

        Args:
            colnames (List[str]): A list of column names to check for in the dataset.

        Raises:
            CustomerDataValidatorError: If required columns are missing.
        """

        missing_columns = [
            col for col in colnames if col not in self.dataset.columns
        ]
        if missing_columns:
            raise CustomerDataValidatorError(
                f"The dataset does not contain the required column(s): {', '.join(missing_columns)}"
            )

    def _create_cep_validation_dataset(
        self,
        addresses: List[Dict],
        external: bool = False,
        webservice: str = 'opencep',
        time_step: int = 120,
        time_delay: float = 0.5,
    ) -> List[Dict]:
        start_time = time.time()
        results = []

        for addr in addresses:
            address = addr['address']
            result = {
                self.customer_id_colname: addr[self.customer_id_colname],
                'cep': address.cep,
                'cep_validation': False,
                'cep_validation_reason': 'Unknown error',
            }

            if external:
                cep_api = CepAPI(webservice=webservice)
                api_result = cep_api.validate_address(address)
                result['cep_validation'] = api_result['valid']
                result['cep_validation_reason'] = api_result['reason']
            else:
                result['cep_validation'] = address.validate_cep()['valid']
                result['cep_validation_reason'] = (
                    'Valid CEP.'
                    if result['cep_validation']
                    else 'Invalid CEP format.'
                )

            results.append(result)

            elapsed_time = time.time() - start_time
            if elapsed_time >= time_step:
                time.sleep(time_delay)
                start_time = time.time()

        return results

    def _check_address_validate(self):

        if not self.cep_colname:
            raise CustomerDataValidatorError('CEP column name is not defined.')

        if not self.street_colname:
            raise CustomerDataValidatorError(
                'Street column name is not defined.'
            )

        if not self.city_colname:
            raise CustomerDataValidatorError(
                'City column name is not defined.'
            )

        if not self.state_colname:
            raise CustomerDataValidatorError(
                'State column name is not defined.'
            )

        required_columns = [
            self.customer_id_colname,
            self.cep_colname,
            self.street_colname,
            self.city_colname,
            self.state_colname,
        ]
        self._check_column_existence(required_columns)

    def validate_address_from_cep(
        self, external: bool = True, webservice: str = 'opencep'
    ) -> pl.DataFrame:
        """Validates address data in the dataset based on CEP information.

        This method utilizes the CEP column specified during initialization to validate
        the address data. If the address validation flag is enabled and the required columns
        are present in the dataset, it will validate each address and return the results
        in a new DataFrame.

        Returns:
            pl.DataFrame: A DataFrame containing the original customer ID and CEP columns,
            along with two new columns: 'cep_validation' indicating if the CEP is valid,
            and 'cep_validation_reason' providing the reason for the validation result.
        """

        self._check_dataset()
        self._check_address_validate()
        address_df = pl.DataFrame()

        try:
            addresses = [
                {
                    self.customer_id_colname: row[self.customer_id_colname],
                    self.cep_colname: row[self.cep_colname],
                    'address': Address(
                        cep=row[self.cep_colname],
                        street=row[self.street_colname],
                        city=row[self.city_colname],
                        state=row[self.state_colname],
                    ),
                }
                for row in self.dataset.to_dicts()
            ]

            cep_validation_result = self._create_cep_validation_dataset(
                addresses=addresses,
                external=external,
                webservice=webservice,
            )
            address_df = pl.DataFrame(cep_validation_result)

        except Exception as e:
            validate_costumer_logger.exception(
                f'Error validating address: {e}'
            )
            raise CustomerDataValidatorError(f'Address validation failed: {e}')

        return address_df

    def _create_cnpj_validation_dataset(
        self,
        cnpjs: List[Dict],
        external: bool = False,
        webservice: str = 'brasilapi',
        time_step: int = 120,
        time_delay: float = 0.3,
    ) -> List[Dict]:
        result = {'cnpj_validation': False, 'cnpj_validation_reason': ''}
        start_time = time.time()

        for cnpj_data in cnpjs:
            cnpj_validator = CNPJValidator(cnpj_data['cnpj'])
            if external:
                cnpj_api = CnpjAPI(webservice=webservice)
                result = cnpj_api.validate_cnpj(cnpj_validator.sanitized_cnpj)
            else:
                result = cnpj_validator.validate()

            cnpj_data['cnpj_validation'] = result['valid']
            cnpj_data['cnpj_validation_reason'] = result['reason']
            elapsed_time = time.time() - start_time

            if elapsed_time >= time_step:
                time.sleep(time_delay)
                start_time = time.time()

        return cnpjs

    def _check_cnpj_validate(self):
        if not self.cnpj_colname:
            raise CustomerDataValidatorError(
                'CNPJ column name is not defined.'
            )
        required_columns = [self.customer_id_colname, self.cnpj_colname]
        self._check_column_existence(required_columns)

    def validate_cnpjs(
        self, external: bool = True, webservice: str = 'brasilapi'
    ) -> pl.DataFrame:
        """Validates CNPJ numbers in the dataset.

        This method checks the CNPJ column specified during initialization to ensure that
        the CNPJ numbers are valid according to the defined rules. If CNPJ validation is
        enabled and the necessary columns are present, it will validate each CNPJ and return
        the results in a new DataFrame.

        Returns:
            pl.DataFrame: A DataFrame containing the original customer ID and CNPJ columns,
            along with two new columns: 'cnpj_validation' indicating if the CNPJ is valid,
            and 'cnpj_validation_reason' providing the reason for the validation result.
        """

        self._check_dataset()
        self._check_cnpj_validate()
        cnpj_df = pl.DataFrame()

        try:

            cnpjs = [
                {
                    self.customer_id_colname: row[self.customer_id_colname],
                    'cnpj': row[self.cnpj_colname],
                }
                for row in self.dataset.to_dicts()
            ]

            cnpj_validation_result = self._create_cnpj_validation_dataset(
                cnpjs=cnpjs,
                external=external,
                webservice=webservice,
            )
            cnpj_df = pl.DataFrame(cnpj_validation_result)

        except Exception as e:
            validate_costumer_logger.exception(f'Error validating CNPJ: {e}')
            raise CustomerDataValidatorError(f'CNPJ validation failed: {e}')

        return cnpj_df

    def _create_cpf_validation_dataset(self, cpfs: List[Dict]):
        cpf_validation_results = CPFValidator.validate_cpfs(
            [cpf_data['cpf'] for cpf_data in cpfs]
        )

        for i, cpf_data in enumerate(cpfs):
            cpf_validation_result = cpf_validation_results[i]
            cpf_data['cpf_validation'] = cpf_validation_result['valid']
            cpf_data['cpf_validation_reason'] = cpf_validation_result['reason']

        return cpfs

    def _check_cpf_validate(self):

        if not self.cpf_colname:
            raise CustomerDataValidatorError('CPF column name is not defined.')

        required_columns = [self.customer_id_colname, self.cpf_colname]
        self._check_column_existence(required_columns)

    def validate_cpfs(self, external: bool = False) -> pl.DataFrame:
        """Validates CPF numbers in the dataset.

        This method leverages the CPF column specified during initialization to validate
        CPF numbers. If CPF validation is enabled and the required columns are available,
        it will validate each CPF and compile the results in a new DataFrame.

        Returns:
            pl.DataFrame: A DataFrame containing the original customer ID and CPF columns,
            along with two new columns: 'cpf_validation' indicating if the CPF is valid,
            and 'cpf_validation_reason' providing the reason for the validation result.
        """

        self._check_dataset()
        self._check_cpf_validate()
        cpf_df = pl.DataFrame()

        try:
            cpfs = [
                {
                    self.customer_id_colname: row[self.customer_id_colname],
                    'cpf': row[self.cpf_colname],
                }
                for row in self.dataset.to_dicts()
            ]

            cpf_validation_result = self._create_cpf_validation_dataset(
                cpfs=cpfs
            )
            cpf_df = pl.DataFrame(cpf_validation_result)

        except Exception as e:
            validate_costumer_logger.exception(f'Error validating CPF: {e}')
            raise CustomerDataValidatorError(f'CPF validation failed: {e}')

        return cpf_df

    def _create_phone_validation_dataset(
        self, phones: List[Dict]
    ) -> List[Dict]:
        phone_validation_results = PhoneValidator.validate_phone_numbers(
            [phone_data['phone'] for phone_data in phones]
        )

        for i, phone_data in enumerate(phones):
            phone_validation_result = phone_validation_results[i]
            phone_data['phone_validation'] = phone_validation_result['valid']
            phone_data['phone_validation_reason'] = phone_validation_result[
                'reason'
            ]
            phone_data['possible_mobile'] = phone_validation_result.get(
                'possible_mobile', False
            )

        return phones

    def _check_phone_validate(self):

        if not self.phone_colname:
            raise CustomerDataValidatorError(
                'Phone column name is not defined.'
            )
        required_columns = [self.customer_id_colname, self.phone_colname]
        self._check_column_existence(required_columns)

    def validate_phones(self, external: bool = False) -> pl.DataFrame:
        """Validates phone numbers in the dataset.

        Utilizing the phone column designated at initialization, this method validates
        the phone numbers. If phone validation is activated and the necessary columns
        exist, it will validate each phone number and assemble the results in a new DataFrame.

        Returns:
            pl.DataFrame: A DataFrame containing the original customer ID and phone columns,
            along with two new columns: 'phone_validation' indicating if the phone number is valid,
            and 'phone_validation_reason' providing the reason for the validation result.
        """
        self._check_dataset()
        self._check_phone_validate()
        phone_df = pl.DataFrame()

        try:
            phones = [
                {
                    self.customer_id_colname: row[self.customer_id_colname],
                    'phone': row[self.phone_colname],
                }
                for row in self.dataset.to_dicts()
            ]

            phone_validation_result = self._create_phone_validation_dataset(
                phones=phones
            )
            phone_df = pl.DataFrame(phone_validation_result)
            phone_df = phone_df.select(
                [
                    self.customer_id_colname,
                    'phone',
                    'phone_validation',
                    'phone_validation_reason',
                    'possible_mobile',
                ]
            )
        except Exception as e:
            validate_costumer_logger.exception(f'Error validating phone: {e}')
            raise CustomerDataValidatorError(f'Phone validation failed: {e}')

        return phone_df

    def _check_email_validate(self):

        if not self.email_colnames:
            raise CustomerDataValidatorError(
                'Email column name is not defined.'
            )

        required_columns = self.email_colnames + [self.customer_id_colname]
        self._check_column_existence(required_columns)

    def _create_email_validation_dataset(
        self, emails: List[Dict], email_colname: str = 'email'
    ) -> List[Dict]:
        email_validation_results = EmailValidator.validate_emails(
            [email_data['email'] for email_data in emails]
        )

        for i, email_data in enumerate(emails):
            email_validation_result = email_validation_results[i]
            email_data[
                f'{email_colname}_validation'
            ] = email_validation_result['valid']
            email_data[
                f'{email_colname}_validation_reason'
            ] = email_validation_result['reason']
            email_data[
                f'{email_colname}_deliverability'
            ] = email_validation_result['deliverability']

        return emails

    def _validate_emails(self, email_colname: str = 'email') -> pl.DataFrame:
        self._check_dataset()
        self._check_email_validate()
        email_df = pl.DataFrame()

        try:
            emails = [
                {
                    self.customer_id_colname: row[self.customer_id_colname],
                    'email': row[email_colname],
                }
                for row in self.dataset.to_dicts()
            ]

            email_validation_result = self._create_email_validation_dataset(
                emails=emails, email_colname=email_colname
            )
            email_df = pl.DataFrame(email_validation_result)

        except Exception as e:
            validate_costumer_logger.exception(f'Error validating email: {e}')
            raise CustomerDataValidatorError(f'E-mail validation failed: {e}')

        return email_df

    def validate_emails(self, external: bool = False) -> pl.DataFrame:
        """Validates email addresses in the dataset.

        This method checks one or more email columns as specified during initialization. If
        email validation is enabled and the required columns are present, it will validate
        each email address and return the results in a new DataFrame.

        Returns:
            pl.DataFrame: A DataFrame with the original customer ID and email columns,
            along with new columns for each email: '{email_colname}_validation' indicating
            if the email is valid, and '{email_colname}_validation_reason' providing the
            reason for the validation result. Here, '{email_colname}' is the name of each
            email column passed during initialization.
        """

        email_df_list = []
        emails_df = pl.DataFrame()

        try:
            for email_colname in self.email_colnames:
                email_df_list.append(self._validate_emails(email_colname))
            emails_df = pl.concat(email_df_list, how='horizontal')
        except Exception as e:
            validate_costumer_logger.exception(f'Error validating email: {e}')
            raise

        return emails_df

    def _check_fields(
        self, fields: List[Dict], available_webservices: List = []
    ):
        for field in fields:
            if field['name'] == 'CEP':
                available_webservices = CepAPI.available_webservices
            elif field['name'] == 'CNPJ':
                available_webservices = CnpjAPI.available_webservices

            if field['external'] and not field.get('webservice'):
                raise CustomerDataValidatorError(
                    f"{field.get('webservice')} Web service  for'{field.get('name')}' is not defined."
                    f'Available web services: {available_webservices}'
                )
            if (
                field['external']
                and field.get('webservice') not in available_webservices
            ):
                raise CustomerDataValidatorError(
                    f"Unsupported web service '{field.get('webservice')}' for '{field.get('name')}'."
                    f'Available web services: {available_webservices}'
                )

    def validate_dataset(
        self, fields: List[Dict] = default_validation
    ) -> pl.DataFrame:
        """
        Validates the entire dataset based on the enabled flags for each type of validation and
        external validation configurations.

        Args:
            fields (List[Dict]): A list of dictionaries, each containing
                'name' (str): the name of the field to validate,
                'external' (bool): whether to use external validation,
                'webservice' (str, optional): the name of the web service to use for validation.

        Returns:
            pl.DataFrame: A DataFrame that includes the original customer ID column and all
            validation results, with a separate column for each validation status and reason.

        Raises:
            CustomerDataValidatorError: If the 'external' key is True and 'webservice' is not provided,
            or if an invalid webservice is provided.
        """
        combined_df = self.dataset.select([self.customer_id_colname])
        self._check_fields(fields=fields)

        try:
            for field in fields:
                field_name = field['name'].lower()
                if 'cep' == field_name:
                    cep_df = self.validate_address_from_cep(
                        external=field.get('external'),
                        webservice=field.get('webservice'),
                    )
                    combined_df = combined_df.join(
                        cep_df, on=self.customer_id_colname, how='outer'
                    )
                if 'cpf' == field_name:
                    cpf_df = self.validate_cpfs()
                    combined_df = combined_df.join(
                        cpf_df, on=self.customer_id_colname, how='outer'
                    )
                if 'cnpj' == field_name:
                    cnpj_df = self.validate_cnpjs(
                        external=field.get('external'),
                        webservice=field.get('webservice'),
                    )
                    combined_df = combined_df.join(
                        cnpj_df, on=self.customer_id_colname, how='outer'
                    )
                if 'phone' == field_name:
                    phone_df = self.validate_phones()
                    combined_df = combined_df.join(
                        phone_df, on=self.customer_id_colname, how='outer'
                    )
                if 'email' == field_name:
                    email_df = self.validate_emails()
                    combined_df = combined_df.join(
                        email_df, on=self.customer_id_colname, how='outer'
                    )
        except CustomerDataValidatorError as e:
            validate_costumer_logger.error(f'Validation error: {e}')
            raise

        return combined_df
