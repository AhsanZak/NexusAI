"""Password hashes and login tokens do not need a database."""

from app.auth.passwords import hash_password, verify_password
from app.auth.tokens import TokenError, issue_token, read_token
from app.seed import SEED_ACCOUNTS


def test_password_round_trip() -> None:
    stored = hash_password("NexusAdmin-local")
    assert verify_password("NexusAdmin-local", stored)
    assert verify_password("wrong", stored) is False


def test_token_carries_the_user() -> None:
    token = issue_token("user-1", "admin@nexusai.local", "super_admin", "secret", 60)
    payload = read_token(token, "secret")
    assert payload["sub"] == "user-1"
    assert payload["role"] == "super_admin"


def test_token_rejects_a_different_secret() -> None:
    token = issue_token("user-1", "admin@nexusai.local", "member", "secret", 60)
    try:
        read_token(token, "other")
    except TokenError:
        return
    raise AssertionError("token signed with another secret was accepted")


def test_seed_accounts_are_distinct_users() -> None:
    emails = [account.email for account in SEED_ACCOUNTS]
    assert len(emails) == len(set(emails)) == 3
    roles = {account.email: account.role for account in SEED_ACCOUNTS}
    assert roles["admin@nexusai.local"] == "super_admin"
    assert roles["amina@nexusai.local"] == "member"
    assert roles["luis@nexusai.local"] == "member"
