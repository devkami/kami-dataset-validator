import unittest
from unittest.mock import patch

from kami_dataset_validator.validators.phone import (
    PhoneValidator,
    PhoneValueError,
)


class TestPhoneNumberValidator(unittest.TestCase):
    @patch('kami_dataset_validator.validators.phone.phonenumbers.parse')
    @patch(
        'kami_dataset_validator.validators.phone.phonenumbers.is_valid_number'
    )
    @patch('kami_dataset_validator.validators.phone.phonenumbers.number_type')
    def test_validate_valid_phone_number(
        self, mock_number_type, mock_is_valid_number, mock_parse
    ):
        mock_parse.return_value = True
        mock_is_valid_number.return_value = True
        mock_number_type.return_value = True

        phone_validator = PhoneValidator('+11234567890')
        self.assertTrue(phone_validator.validate())
        self.assertTrue(phone_validator.is_possible_mobile())

    @patch('kami_dataset_validator.validators.phone.phonenumbers.parse')
    def test_validate_invalid_phone_number_format(self, mock_parse):
        mock_parse.side_effect = PhoneValueError(
            'Invalid phone number format.'
        )

        with self.assertRaises(PhoneValueError):
            PhoneValidator('invalid_phone_number').validate()

    @patch('kami_dataset_validator.validators.phone.phonenumbers.parse')
    @patch(
        'kami_dataset_validator.validators.phone.phonenumbers.is_valid_number'
    )
    def test_validate_invalid_phone_number(
        self, mock_is_valid_number, mock_parse
    ):
        mock_parse.return_value = True
        mock_is_valid_number.return_value = False

        with self.assertRaises(PhoneValueError):
            phone_validator = PhoneValidator('+11234567890')
            phone_validator.validate()

    @patch('kami_dataset_validator.validators.phone.phonenumbers.parse')
    @patch(
        'kami_dataset_validator.validators.phone.phonenumbers.is_valid_number'
    )
    @patch('kami_dataset_validator.validators.phone.phonenumbers.number_type')
    def test_validate_non_mobile_phone_number(
        self, mock_number_type, mock_is_valid_number, mock_parse
    ):
        mock_parse.return_value = True
        mock_is_valid_number.return_value = True
        mock_number_type.return_value = False

        phone_validator = PhoneValidator('+11234567890')
        self.assertTrue(phone_validator.validate())
        self.assertFalse(phone_validator.is_possible_mobile())

    @patch('kami_dataset_validator.validators.phone.phonenumbers.parse')
    @patch(
        'kami_dataset_validator.validators.phone.phonenumbers.is_valid_number'
    )
    @patch('kami_dataset_validator.validators.phone.phonenumbers.number_type')
    def test_validate_phone_numbers(
        self, mock_number_type, mock_is_valid_number, mock_parse
    ):
        mock_parse.return_value = True
        mock_is_valid_number.return_value = True
        mock_number_type.side_effect = [True, False]
        phone_numbers = ['+11234567890', '+14155552671']
        results = PhoneValidator.validate_phone_numbers(phone_numbers)

        for res in results:
            self.assertTrue(res['valid'])
            self.assertIn(res['possible_mobile'], [True, False])


if __name__ == '__main__':
    unittest.main()
