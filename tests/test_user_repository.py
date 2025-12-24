from datetime import datetime
from app.repository.user_repo import UserRepository


class TestUserRepository:
    def setup_method(self):
        """각 테스트 전에 새로운 UserRepository 인스턴스 생성"""
        self.repo = UserRepository()

    def test_save_user_success(self):
        """유저 저장 성공 테스트"""
        # Given
        name = "홍길동"
        email = "hong@example.com"

        # When
        user = self.repo.save(name, email)

        # Then
        assert user.id == 1
        assert user.name == name
        assert user.email == email
        assert isinstance(user.created_at, datetime)

    def test_save_multiple_users_increments_id(self):
        """여러 유저 저장 시 ID 자동 증가 테스트"""
        # Given
        user1_name, user1_email = "유저1", "user1@example.com"
        user2_name, user2_email = "유저2", "user2@example.com"

        # When
        user1 = self.repo.save(user1_name, user1_email)
        user2 = self.repo.save(user2_name, user2_email)

        # Then
        assert user1.id == 1
        assert user2.id == 2
        assert user1.name == user1_name
        assert user2.name == user2_name

    def test_find_by_id_existing_user(self):
        """존재하는 유저 ID로 검색 성공 테스트"""
        # Given
        saved_user = self.repo.save("테스트유저", "test@example.com")

        # When
        found_user = self.repo.find_by_id(saved_user.id)

        # Then
        assert found_user is not None
        assert found_user.id == saved_user.id
        assert found_user.name == saved_user.name
        assert found_user.email == saved_user.email

    def test_find_by_id_non_existing_user(self):
        """존재하지 않는 유저 ID로 검색 시 None 반환 테스트"""
        # When
        found_user = self.repo.find_by_id(999)

        # Then
        assert found_user is None

    def test_find_by_email_existing_user(self):
        """존재하는 이메일로 검색 성공 테스트"""
        # Given
        email = "find@example.com"
        saved_user = self.repo.save("찾기테스트", email)

        # When
        found_user = self.repo.find_by_email(email)

        # Then
        assert found_user is not None
        assert found_user.email == email
        assert found_user.id == saved_user.id

    def test_find_by_email_non_existing_user(self):
        """존재하지 않는 이메일로 검색 시 None 반환 테스트"""
        # When
        found_user = self.repo.find_by_email("notfound@example.com")

        # Then
        assert found_user is None

    def test_find_all_empty(self):
        """빈 저장소에서 전체 조회 테스트"""
        # When
        users = self.repo.find_all()

        # Then
        assert users == []

    def test_find_all_with_users(self):
        """유저들이 있는 상태에서 전체 조회 테스트"""
        # Given
        user1 = self.repo.save("유저1", "user1@example.com")
        user2 = self.repo.save("유저2", "user2@example.com")

        # When
        users = self.repo.find_all()

        # Then
        assert len(users) == 2
        assert user1 in users
        assert user2 in users

    def test_delete_existing_user(self):
        """존재하는 유저 삭제 성공 테스트"""
        # Given
        saved_user = self.repo.save("삭제테스트", "delete@example.com")

        # When
        result = self.repo.delete(saved_user.id)

        # Then
        assert result is True
        assert self.repo.find_by_id(saved_user.id) is None

    def test_delete_non_existing_user(self):
        """존재하지 않는 유저 삭제 시 False 반환 테스트"""
        # When
        result = self.repo.delete(999)

        # Then
        assert result is False
