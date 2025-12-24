import pytest
from unittest.mock import Mock
from datetime import datetime
from app.service.user_service import UserService
from app.repository.user_repo import UserRepository
from app.models.entities import User
from app.exceptions import EmailNotAllowedNameExistsError


class TestUserService:
    def setup_method(self):
        """각 테스트 전에 새로운 mock repository와 service 인스턴스 생성"""
        self.mock_repo = Mock(spec=UserRepository)
        self.service = UserService(self.mock_repo)

    def test_create_user_success(self):
        """유저 생성 성공 테스트"""
        # Given
        name = "홍길동"
        email = "hong@example.com"
        mock_user = User(
            id=1, name=name, email=email, created_at=datetime(2023, 1, 1, 12, 0, 0)
        )
        self.mock_repo.save.return_value = mock_user

        # When
        result = self.service.create_user(name, email)

        # Then
        self.mock_repo.save.assert_called_once_with(name=name, email=email)
        assert result["id"] == 1
        assert result["name"] == name
        assert result["email"] == email
        assert result["created_at"] == "2023-01-01 12:00:00"

    def test_create_user_with_invalid_email(self):
        """이메일 검증 실패 테스트"""
        # Given
        self.service._valid_email = Mock(return_value=False)

        # When & Then
        with pytest.raises(ValueError, match="Invalid email format"):
            self.service.create_user("테스트", "invalid_email")

        # Repository save 메서드가 호출되지 않았는지 확인
        self.mock_repo.save.assert_not_called()

    def test_create_user_with_admin_email(self):
        """관리자 이메일로 생성 시 예외 발생 테스트"""
        # Given
        admin_email = "admin@example.com"

        # When & Then
        with pytest.raises(EmailNotAllowedNameExistsError) as exc_info:
            self.service.create_user("관리자", admin_email)

        assert exc_info.value.email == admin_email
        self.mock_repo.save.assert_not_called()

    def test_get_user_success(self):
        """유저 조회 성공 테스트"""
        # Given
        user_id = 1
        mock_user = User(
            id=user_id,
            name="조회테스트",
            email="get@example.com",
            created_at=datetime(2023, 2, 1, 15, 30, 0),
        )
        self.mock_repo.find_by_id.return_value = mock_user

        # When
        result = self.service.get_user(user_id)

        # Then
        self.mock_repo.find_by_id.assert_called_once_with(user_id=user_id)
        assert result["id"] == user_id
        assert result["name"] == "조회테스트"
        assert result["email"] == "get@example.com"
        assert result["created_at"] == "2023-02-01 15:30:00"

    def test_get_user_not_found(self):
        """존재하지 않는 유저 조회 시 AttributeError 발생 테스트"""
        # Given
        user_id = 999
        self.mock_repo.find_by_id.return_value = None

        # When & Then
        with pytest.raises(AttributeError):
            self.service.get_user(user_id)

        self.mock_repo.find_by_id.assert_called_once_with(user_id=user_id)

    def test_valid_email_always_returns_true(self):
        """현재 이메일 검증 로직이 항상 True를 반환하는지 테스트"""
        # When & Then
        assert self.service._valid_email("valid@example.com") is True
        assert self.service._valid_email("invalid-email") is True
        assert self.service._valid_email("") is True

    def test_create_user_email_validation_flow(self):
        """이메일 검증 흐름 전체 테스트"""
        # Given
        name = "검증테스트"
        email = "validation@example.com"
        mock_user = User(id=5, name=name, email=email, created_at=datetime.now())
        self.mock_repo.save.return_value = mock_user

        # When
        result = self.service.create_user(name, email)

        # Then
        # 이메일 검증을 통과했으므로 save가 호출되어야 함
        self.mock_repo.save.assert_called_once()
        assert "id" in result
        assert result["email"] == email

    def test_service_dependency_injection(self):
        """의존성 주입이 올바르게 작동하는지 테스트"""
        # Given
        custom_repo = Mock(spec=UserRepository)
        service = UserService(custom_repo)

        # Then
        assert service.user_repo is custom_repo

    @pytest.mark.parametrize(
        "email,should_raise",
        [
            ("admin@example.com", True),
            ("user@example.com", False),
            ("test@example.com", False),
        ],
    )
    def test_create_user_email_restriction(self, email, should_raise):
        """특정 이메일 제한 정책 파라미터화 테스트"""
        # Given
        mock_user = User(id=1, name="테스트", email=email, created_at=datetime.now())
        self.mock_repo.save.return_value = mock_user

        if should_raise:
            # When & Then - 예외 발생 예상
            with pytest.raises(EmailNotAllowedNameExistsError):
                self.service.create_user("테스트", email)
        else:
            # When & Then - 정상 처리 예상
            result = self.service.create_user("테스트", email)
            assert result["email"] == email
