import unittest
from unittest.mock import MagicMock, patch

from email_validator import (
    EmailNotValidError,
    EmailSyntaxError,
    EmailUndeliverableError,
)

from kami_dataset_validator.validators.email import EmailValidator


class TestEmailValidator(unittest.TestCase):
    def setUp(self):
        self.valid_email = 'test@example.com'
        self.invalid_email_syntax = 'test@example'
        self.invalid_email_domain = 'test@invalid_domain.com'

        self.mock_valid_response = MagicMock()
        self.mock_valid_response.email = self.valid_email
        self.mock_valid_response.mx = MagicMock()

    @patch('kami_dataset_validator.validators.email.validate_email')
    def test_validate_valid_email(self, mock_validate_email):
        """Test email validation with valid email."""
        mock_validate_email.return_value = self.mock_valid_response
        email_validator = EmailValidator(self.valid_email)
        self.assertTrue(email_validator.validate())
        self.assertTrue(email_validator.deliverability)

    @patch('kami_dataset_validator.validators.email.validate_email')
    def test_validate_invalid_email_syntax(self, mock_validate_email):
        """Test email validation with invalid email syntax."""
        mock_validate_email.side_effect = EmailSyntaxError(
            'Invalid email syntax'
        )
        email_validator = EmailValidator(self.invalid_email_syntax)
        self.assertFalse(email_validator.validate())
        self.assertFalse(email_validator.deliverability)

    @patch('kami_dataset_validator.validators.email.validate_email')
    def test_validate_invalid_email_domain(self, mock_validate_email):
        """Test email validation with invalid email domain (undeliverable)."""
        mock_validate_email.side_effect = EmailUndeliverableError(
            'Invalid email domain'
        )
        email_validator = EmailValidator(self.invalid_email_domain)
        self.assertFalse(email_validator.validate())
        self.assertFalse(email_validator.deliverability)

    @patch('kami_dataset_validator.validators.email.validate_email')
    def test_validate_emails(self, mock_validate_email):
        """Test validation of multiple emails."""
        emails_to_test = [
            self.valid_email,
            self.invalid_email_syntax,
            self.invalid_email_domain,
        ]

        def side_effect_func(email, check_deliverability):
            if email == self.valid_email:
                return MagicMock(email=email, mx=True)
            elif email == self.invalid_email_syntax:
                raise EmailSyntaxError('Invalid email syntax')
            elif email == self.invalid_email_domain:
                raise EmailUndeliverableError('Invalid email domain')
            else:
                raise EmailNotValidError('Email not valid')

        mock_validate_email.side_effect = side_effect_func

        results = EmailValidator.validate_emails(emails_to_test)

        self.assertTrue(results[0]['valid'])
        self.assertFalse(results[1]['valid'])
        self.assertFalse(results[2]['valid'])
        self.assertTrue(results[0]['deliverability'])
        self.assertFalse(results[1].get('deliverability', False))
        self.assertFalse(results[2].get('deliverability', False))


if __name__ == '__main__':
    unittest.main()
