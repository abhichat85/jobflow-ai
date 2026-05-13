from app.services.crypto import encrypt, decrypt


def test_round_trip():
    plain = "li_at=AQEDATXXXXXXXXXXXXXXXXX"
    enc = encrypt(plain)
    assert enc != plain
    assert isinstance(enc, str)
    assert decrypt(enc) == plain


def test_decrypt_empty_returns_empty():
    assert decrypt("") == ""
    assert decrypt(None) == ""


def test_encrypt_empty_returns_empty():
    assert encrypt("") == ""
    assert encrypt(None) == ""
