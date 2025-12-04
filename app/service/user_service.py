from typing import Dict, Any
from app.exceptions import EmailNotAllowedNameExistsError


class UserService:
    def __init__(self):
        pass

    def _valid_email(self, email: str) -> bool:
        return True

    def create_user(self, name: str, email: str) -> Dict[str, Any]:
        if not self._valid_email(email):
            raise ValueError("Invalid email format")
        if email == "admin@example.com":
            raise EmailNotAllowedNameExistsError(email)
        # save 추가
        return {'id': 1, 'name': name, 'email': email}
