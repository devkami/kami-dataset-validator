import time
from typing import Dict, List

import polars as pl
from validate_docbr import CNPJ, CPF

from kami_dataset_validator.validators.cep import Address, CepAPI
from kami_dataset_validator.validators.cnpj import CnpjAPI
from kami_dataset_validator.validators.cpf import CPFValidator
from kami_dataset_validator.validators.phone import PhoneValidator


class CustomerDataValidator:
    def __init__(self, dataset: pl.DataFrame):
        self.dataset = dataset

    def _create_cep_validation_dataset(
        self,
        addresses: List[Dict],
        time_step: int = 120,
        time_delay: float = 0.5,
    ):
        cep_api = CepAPI(webservice='opencep')
        start_time = time.time()

        for addr in addresses:
            address = Address.from_dict(addr['address'])
            result = cep_api.validate_address(address)
            addr['cep'] = address.cep
            addr['cep_validation'] = result['valid']
            addr['cep_validation_reason'] = result['reason']
            elapsed_time = time.time() - start_time

            if elapsed_time >= time_step:
                time.sleep(time_delay)
                start_time = time.time()
        return addresses

    def validate_address_from_cep(self) -> pl.DataFrame:

        addresses = [
            {
                'cod_cliente': row['cod_cliente'],
                'address': Address(
                    cep=row['cep'],
                    street=row['endereco'],
                    city=row['cidade'],
                    state=row['uf'],
                ),
            }
            for row in self.dataset.to_dicts()
        ]

        cep_validation_result = self._create_cep_validation_dataset(
            addresses=addresses
        )
        address_df = pl.DataFrame(cep_validation_result)
        address_df = address_df.select(
            ['cod_cliente', 'cep', 'cep_validation', 'cep_validation_reason']
        )
        return address_df

    def _create_cnpj_validation_dataset(
        self, cnpjs: List[Dict], time_step: int = 120, time_delay: float = 0.3
    ):
        cnpj_api = CnpjAPI()
        start_time = time.time()

        for cnpj_data in cnpjs:
            result = cnpj_api.validate_cnpj(cnpj_data['cnpj'])
            cnpj_data['cnpj_validation'] = result['valid']
            cnpj_data['cnpj_validation_reason'] = result['reason']
            elapsed_time = time.time() - start_time

            if elapsed_time >= time_step:
                time.sleep(time_delay)
                start_time = time.time()
        return cnpjs

    def validate_cnpj(self) -> pl.DataFrame:
        cnpjs = [
            {'cod_cliente': row['cod_cliente'], 'cnpj': row['cnpj']}
            for row in self.dataset.to_dicts()
        ]

        cnpj_validation_result = self._create_cnpj_validation_dataset(
            cnpjs=cnpjs
        )
        cnpj_df = pl.DataFrame(cnpj_validation_result)
        cnpj_df = cnpj_df[
            [
                'cod_cliente',
                'cnpj',
                'cnpj_validation',
                'cnpj_validation_reason',
            ]
        ]
        return cnpj_df

    def _create_cpf_validation_dataset(self, cpfs: List[Dict]):
        cpf_validation_results = CPFValidator.validate_cpfs(
            [cpf_data['cpf'] for cpf_data in cpfs]
        )

        for i, cpf_data in enumerate(cpfs):
            cpf_data['cpf_validation'] = cpf_validation_results[i]['valid']
            cpf_data['cpf_validation_reason'] = cpf_validation_results[i][
                'reason'
            ]

        return cpfs

    def validate_cpf(self) -> pl.DataFrame:
        cpfs = [
            {'cod_cliente': row['cod_cliente'], 'cpf': row['cpf']}
            for row in self.dataset.to_dicts()
        ]

        cpf_validation_result = self._create_cpf_validation_dataset(cpfs=cpfs)
        cpf_df = pl.DataFrame(cpf_validation_result)
        cpf_df = cpf_df[
            ['cod_cliente', 'cpf', 'cpf_validation', 'cpf_validation_reason']
        ]
        return cpf_df

    def _create_phone_validation_dataset(self, phones: List[Dict]) -> List[Dict]:
        phone_validation_results = PhoneValidator.validate_phones(
            [phone_data['phone'] for phone_data in phones]
        )

        for i, phone_data in enumerate(phones):
            validation_result = phone_validation_results[i]
            phone_data['phone_validation'] = validation_result['valid']
            phone_data['phone_validation_reason'] = validation_result['reason']            
            phone_data['possible_mobile'] = validation_result.get('possible_mobile', False)

        return phones

    def validate_phone(self) -> pl.DataFrame:
        phones = [
            {'cod_cliente': row['cod_cliente'], 'phone': row['phone']}
            for row in self.dataset.to_dicts()
        ]

        phone_validation_result = self._create_phone_validation_dataset(phones=phones)
        phone_df = pl.DataFrame(phone_validation_result)
        phone_df = phone_df.select(
            ['cod_cliente', 'phone', 'phone_validation', 'phone_validation_reason', 'possible_mobile']
        )
        return phone_df

    def validate_dataset(self) -> pl.DataFrame:        
        cep_df = self.validate_address_from_cep()
        cpf_df = self.validate_cpf()        
        cnpj_df = self.validate_cnpj()        
        phone_df = self.validate_phone()
        
        combined_df = cep_df.join(cpf_df, on='cod_cliente', how='outer')
        combined_df = combined_df.join(cnpj_df, on='cod_cliente', how='outer')
        combined_df = combined_df.join(phone_df, on='cod_cliente', how='outer')

        combined_df = combined_df.select(
            [
                'cod_cliente',
                'cep',
                'cep_validation',
                'cep_validation_reason',
                'cnpj',
                'cnpj_validation',
                'cnpj_validation_reason',
                'cpf',
                'cpf_validation',
                'cpf_validation_reason',
                'phone',
                'phone_validation',
                'phone_validation_reason',
                'possible_mobile'
            ]
        )        

        combined_df = combined_df.fill_none('').lazy().collect()
        return combined_df
