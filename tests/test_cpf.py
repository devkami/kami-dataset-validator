import unittest

from kami_dataset_validator.validators.cpf import CPFValidator, CPFValueError


class TestCPFValidator(unittest.TestCase):
    def test_init_valid_cpf(self):
        """Test initialization with a valid CPF."""
        cpf = '123.456.789-09'
        validator = CPFValidator(cpf)
        self.assertEqual(validator.cpf, cpf)

    def test_sanitize_cpf(self):
        """Test the CPF sanitization process."""
        cpf = '123.456.789-09'
        expected_sanitized_cpf = '12345678909'
        validator = CPFValidator(cpf)
        self.assertEqual(validator.sanitized_cpf, expected_sanitized_cpf)

    def test_validate_cpf(self):
        """Test CPF validation process."""
        cpf = '111.444.777-35'
        validator = CPFValidator(cpf)
        self.assertTrue(validator.validate())

    def test_validate_cpf_invalid_format(self):
        """Test CPF validation with invalid format."""
        cpf = 'invalid_cpf_format'
        with self.assertRaises(CPFValueError):
            CPFValidator(cpf)

    def test_validate_cpf_invalid_length(self):
        """Test CPF validation with invalid length."""
        cpf = '1234567890'
        with self.assertRaises(CPFValueError):
            CPFValidator(cpf)

    def test_validate_cpfs(self):
        """Test CPF validation for multiple CPFs."""
        valid_cpfs = ['11144477735', '39053344705', '12345678909']
        invalid_cpfs = [
            {
                'cpf': '12345',
                'reason': 'Invalid CPF length. Ensure it has 11 digits.',
            },
            {
                'cpf': 'abcdefg',
                'reason': 'Invalid CPF format. Ensure it contains only numbers.',
            },
        ]

        results = CPFValidator.validate_cpfs(
            [cpf for cpf in valid_cpfs] + [inv['cpf'] for inv in invalid_cpfs]
        )

        for cpf in valid_cpfs:
            self.assertIn(
                {'cpf': cpf, 'valid': True, 'reason': 'Valid CPF.'}, results
            )

        for inv_cpf in invalid_cpfs:
            self.assertIn(
                {
                    'cpf': inv_cpf['cpf'],
                    'valid': False,
                    'reason': inv_cpf['reason'],
                },
                results,
            )


if __name__ == '__main__':
    unittest.main()
