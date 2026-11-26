"""Allow new traders to verify an email without supplying a phone number."""

from alembic import op


revision = "0004_email_only_signup"
down_revision = "0003_signup_verification"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE signup_verifications
        ADD COLUMN email_code_digest TEXT,
        ALTER COLUMN phone DROP NOT NULL,
        ALTER COLUMN email_sid DROP NOT NULL,
        ALTER COLUMN sms_sid DROP NOT NULL
    """)
    op.execute("ALTER TABLE trader_verified_contacts ALTER COLUMN phone DROP NOT NULL")


def downgrade():
    raise RuntimeError("Preserve verified email addresses when rolling back the application.")
