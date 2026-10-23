import pytest

from fox3_agent.diagnose.redact import redact_text, safe_error

UCID = "aabbccddeeff00112233445566778899"


@pytest.mark.parametrize("raw, gone", [
    (r"C:\Users\Jane Pilot\Saved Games\DCS", "Jane"),
    (r"c:\USERS\bob\Documents", "bob"),
    ("C:/Users/alice/Saved Games", "alice"),
    ("/home/carol/.config", "carol"),
    (r"\\server\share\Users\dave\x", "dave"),
    (f"ucid {UCID} seen", UCID),
    (f"ucid {UCID.upper()} seen", UCID.upper()),
    ("id 0123456789abcdef0123 end", "0123456789abcdef0123"),
    ("mail me at john.doe+fox@example.com now", "john.doe"),
    ("postgresql+psycopg://fox3ro:S3cr3t!@db.local:5432/bot", "S3cr3t"),
    ("https://user:pass@host.example.org/x", "pass"),
    ("https://onlytoken@host.example.org/x", "onlytoken"),
    ("Authorization: Bearer abc.def.ghi", "abc.def"),
    ("api_key=hunter2 next", "hunter2"),
    ("password: letmein", "letmein"),
    ("550e8400-e29b-41d4-a716-446655440000", "550e8400"),
])
def test_hostile_inputs_are_redacted(raw, gone):
    out = redact_text(raw)
    assert gone not in out, out


def test_user_path_keeps_the_rest_of_the_path():
    assert redact_text(r"C:\Users\bob\Saved Games\DCS.server") == r"C:\Users\<user>\Saved Games\DCS.server"


def test_ordinary_text_is_untouched():
    text = "Tacview-20240501-180000-DCS.zip.acmi 12.3 MB age 3600 s coalition=blue x=1.5"
    assert redact_text(text) == text


def test_redaction_is_idempotent():
    once = redact_text(rf"C:\Users\bob\x {UCID} a@b.org")
    assert redact_text(once) == once


def test_extra_names_are_masked_as_whole_words_only():
    out = redact_text("owner enric ran enricher", extra_names=("enric",))
    assert out == "owner <user> ran enricher"


def test_short_extra_names_ignored():
    assert redact_text("a b ab", extra_names=("ab",)) == "a b ab"


def test_safe_error_hides_file_names_and_users():
    exc = PermissionError(13, "Access denied", r"C:\Users\bob\secret.lua")
    out = safe_error(exc)
    assert out == "PermissionError: Access denied" and "bob" not in out and "secret" not in out


def test_safe_error_truncates_and_redacts_message():
    out = safe_error(ValueError(f"bad value {UCID} " + "x" * 500))
    assert UCID not in out and len(out) <= 170
