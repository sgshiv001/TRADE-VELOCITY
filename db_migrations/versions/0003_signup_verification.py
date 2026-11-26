"""Add signup verification challenges and verified contacts."""

from alembic import op

from stock_engine.signup_verification import SCHEMA


revision = "0003_signup_verification"
down_revision = "0002_admin_activity_index"
branch_labels = None
depends_on = None


def upgrade():
    for statement in SCHEMA:
        op.execute(statement)


def downgrade():
    raise RuntimeError("Preserve verified contacts when rolling back the application.")
