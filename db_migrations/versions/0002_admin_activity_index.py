"""Index the admin activity list without changing trader records."""

from alembic import op

revision = "0002_admin_activity_index"
down_revision = "0001_persistent_books"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE INDEX IF NOT EXISTS trader_accounts_activity
        ON trader_accounts (last_active_at DESC NULLS LAST, username)
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS trader_accounts_activity")
