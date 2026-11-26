"""Email verification for hosted account registration."""

from hashlib import sha256
import hmac
import json
import os
import secrets
from urllib.error import URLError
from urllib.request import Request, urlopen


VERIFICATION_SECONDS = 600
MAX_CHECKS = 5

SCHEMA = (
    """CREATE TABLE IF NOT EXISTS signup_verifications (
        token_digest TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        email_sid TEXT NOT NULL,
        sms_sid TEXT NOT NULL,
        email_verified BOOLEAN NOT NULL DEFAULT FALSE,
        sms_verified BOOLEAN NOT NULL DEFAULT FALSE,
        attempts INTEGER NOT NULL DEFAULT 0,
        expires_at TIMESTAMPTZ NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS signup_verifications_expiration ON signup_verifications (expires_at)",
    """CREATE TABLE IF NOT EXISTS trader_verified_contacts (
        username TEXT PRIMARY KEY REFERENCES trader_accounts(username) ON DELETE CASCADE,
        email TEXT NOT NULL UNIQUE,
        phone TEXT NOT NULL UNIQUE,
        verified_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
)


class DeliveryUnavailable(Exception):
    pass


class VerificationRequired(Exception):
    pass


def normalize_email(email: str) -> str:
    from email_validator import EmailNotValidError, validate_email

    try:
        address = validate_email(email.strip(), check_deliverability=False, allow_smtputf8=False)
    except EmailNotValidError:
        raise ValueError("Enter a valid email address") from None
    return address.ascii_email.lower()


def digest(value: str) -> str:
    return sha256(value.encode()).hexdigest()


class BrevoEmail:
    def __init__(self, api_key: str, sender: str):
        if not api_key or not sender:
            raise ValueError("Set the Brevo API key and verified sender before enabling signup verification")
        self.api_key = api_key
        self.sender = normalize_email(sender)

    @classmethod
    def from_environment(cls):
        return cls(os.getenv("BREVO_API_KEY", "").strip(), os.getenv("BREVO_SENDER_EMAIL", "").strip())

    def send_code(self, email: str, code: str):
        body = {
            "sender": {"name": "TradeVelocity", "email": self.sender},
            "to": [{"email": email, "removeTrackingPixel": True}],
            "subject": "Verify your TradeVelocity email",
            "textContent": f"Your TradeVelocity signup code is {code}. It expires in 10 minutes.\n\n"
                           "If you did not request a TradeVelocity account, you can ignore this email.",
        }
        request = Request("https://api.brevo.com/v3/smtp/email", data=json.dumps(body).encode(), headers={
            "api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        try:
            with urlopen(request, timeout=5) as response:
                payload = json.load(response)
        except (URLError, TimeoutError, ValueError):
            raise DeliveryUnavailable from None
        if not isinstance(payload, dict) or not payload.get("messageId"):
            raise DeliveryUnavailable


class SignupVerification:
    def __init__(self, store, provider: BrevoEmail, signing_key: bytes):
        if len(signing_key) < 32:
            raise ValueError("Set TRADEVELOCITY_SIGNUP_OTP_SECRET to a random secret of at least 32 bytes")
        self.store = store
        self.provider = provider
        self.signing_key = signing_key

    def code_digest(self, token: str, code: str) -> str:
        return hmac.new(self.signing_key, f"{token}:{code}".encode(), sha256).hexdigest()

    def start(self, username: str, email: str) -> str:
        token = secrets.token_urlsafe(32)
        code = f"{secrets.randbelow(1_000_000):06d}"
        with self.store.connect() as connection:
            connection.execute("DELETE FROM signup_verifications WHERE expires_at <= now()")
            connection.execute("""
                INSERT INTO signup_verifications (token_digest, username, email, email_code_digest, expires_at)
                VALUES (%s, %s, %s, %s, now() + %s * interval '1 second')
            """, (digest(token), username, email, self.code_digest(token, code), VERIFICATION_SECONDS))
        self.provider.send_code(email, code)
        return token

    def verify(self, username: str, token: str, email_code: str):
        with self.store.connect() as connection:
            row = connection.execute("""
                SELECT email_code_digest, attempts
                FROM signup_verifications WHERE token_digest = %s AND username = %s AND expires_at > now()
                FOR UPDATE
            """, (digest(token), username)).fetchone()
            if not row or not row[0]:
                raise VerificationRequired("Request a new email code and try again")
            expected_digest, attempts = row
            if attempts >= MAX_CHECKS:
                raise VerificationRequired("Too many attempts. Request a new email code")
            valid = hmac.compare_digest(expected_digest, self.code_digest(token, email_code))
            connection.execute("""
                UPDATE signup_verifications SET email_verified = email_verified OR %s,
                    attempts = attempts + 1 WHERE token_digest = %s
            """, (valid, digest(token)))
        if not valid:
            raise VerificationRequired("Check your email code and try again")

    @staticmethod
    def consume(connection, username: str, token: str):
        contact = connection.execute("""
            DELETE FROM signup_verifications
            WHERE token_digest = %s AND username = %s AND email_verified
                AND email_code_digest IS NOT NULL AND expires_at > now()
            RETURNING email
        """, (digest(token), username)).fetchone()
        if not contact:
            raise VerificationRequired("Request a new email code and try again")
        return contact[0]
