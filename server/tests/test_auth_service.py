def test_auth_service_hash():
    from src.auth.service import hash_password
    from src.auth.dependencies import verify_password
    hashed = hash_password('secret')
    assert verify_password('secret', hashed)
    assert not verify_password('wrong', hashed)
