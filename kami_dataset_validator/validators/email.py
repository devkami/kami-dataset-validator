from typing import Dict, List, Union

from email_validator import (
    EmailNotValidError,
    EmailSyntaxError,
    EmailUndeliverableError,
    validate_email,
)


class EmailValidator:
    def __init__(self, email: str):
        self.email = email
        self.validated_email = ''
        self.deliverability = False
        self.validate()

    def validate(self) -> bool:
        try:
            validation_result = validate_email(
                self.email, check_deliverability=True
            )
            self.validated_email = validation_result.email
            self.deliverability = validation_result.mx is not None
            return True
        except EmailNotValidError:
            return False

    @classmethod
    def validate_emails(
        cls, emails: List[str]
    ) -> List[Dict[str, Union[str, bool]]]:
        results = []

        for email in emails:
            email_validator = cls(email)
            result = {
                'email': email,
                'valid': email_validator.validated_email != '',
                'deliverability': email_validator.deliverability,
                'reason': 'Valid email.'
                if email_validator.validated_email != ''
                else 'Invalid email.',
            }

            if not result['valid']:
                try:
                    validate_email(email, check_deliverability=True)
                except EmailSyntaxError as e:
                    result['reason'] = str(e)
                except EmailUndeliverableError as e:
                    result['reason'] = str(e)
                except EmailNotValidError as e:
                    result['reason'] = str(e)

            results.append(result)

        return results
