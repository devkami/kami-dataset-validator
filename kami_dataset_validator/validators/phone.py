from typing import Dict, List, Union

import phonenumbers
from phonenumbers import PhoneNumberType


class PhoneValueError(Exception):
    """Exception raised when a phone number value is invalid."""

    pass


class PhoneValidator:
    def __init__(self, phone_number: str):
        self.phone_number = phone_number
        self.parsed_phone_number = self._parse_phone_number()

    def _parse_phone_number(self) -> phonenumbers.PhoneNumber:
        try:
            return phonenumbers.parse(self.phone_number)
        except phonenumbers.NumberParseException as e:
            raise PhoneValueError(str(e))

    def is_possible_mobile(self) -> bool:
        return (
            phonenumbers.number_type(self.parsed_phone_number)
            == PhoneNumberType.MOBILE
        )

    def validate(self) -> bool:
        is_valid = phonenumbers.is_valid_number(self.parsed_phone_number)
        if not is_valid:
            raise PhoneValueError('The provided phone number is not valid.')
        return True

    @classmethod
    def validate_phone_numbers(
        cls, phone_numbers: List[str]
    ) -> List[Dict[str, Union[str, bool]]]:
        results = []

        for number in phone_numbers:
            result = {'phone_number': number}
            try:
                phone_number_validator = cls(number)
                is_valid = phone_number_validator.validate()
                is_possible_mobile = (
                    phone_number_validator.is_possible_mobile()
                )
                result['valid'] = is_valid
                result['possible_mobile'] = is_possible_mobile
                result['reason'] = (
                    'Valid phone number.'
                    if is_valid
                    else 'Invalid phone number.'
                )
            except PhoneValueError as e:
                result['valid'] = False
                result['possible_mobile'] = False
                result['reason'] = str(e)
            except Exception as e:
                result['valid'] = False
                result['possible_mobile'] = False
                result['reason'] = str(e)

            results.append(result)

        return results
