from typing import Dict, List, Union

from validate_docbr import CPF


class CPFValueError(Exception):
    """Exception raised when a CPF value is invalid."""

    pass


class CPFValidator:
    def __init__(self, cpf: str):
        self.cpf = cpf
        self.sanitized_cpf = self._sanitize_cpf()

    def _sanitize_cpf(self) -> str:
        sanitized_cpf = (
            self.cpf.replace('.', '').replace('-', '').replace(',', '')
        )

        if not sanitized_cpf.isdigit():
            raise CPFValueError(
                'Invalid CPF format. Ensure it contains only numbers.'
            )

        if len(sanitized_cpf) != 11:
            raise CPFValueError('Invalid CPF length. Ensure it has 11 digits.')

        return sanitized_cpf

    def validate(self) -> bool:
        cpf_validator = CPF()

        if not cpf_validator.validate(self.sanitized_cpf):
            raise CPFValueError('The provided CPF is not valid.')

        return True

    @classmethod
    def validate_cpfs(
        cls, cpfs: List[str]
    ) -> List[Dict[str, Union[str, bool]]]:
        results = []

        for cpf in cpfs:
            result = {'cpf': cpf}
            try:
                cpf_validator = cls(cpf)
                is_valid = cpf_validator.validate()
                result['valid'] = is_valid
                result['reason'] = 'Valid CPF.' if is_valid else 'Invalid CPF.'
            except CPFValueError as e:
                result['valid'] = False
                result['reason'] = str(e)
            except Exception as e:
                result['valid'] = False
                result['reason'] = str(e)

            results.append(result)

        return results
