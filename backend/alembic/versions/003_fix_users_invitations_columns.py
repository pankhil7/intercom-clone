"""fix users and invitations columns to match models

Revision ID: 003
Revises: 002
Create Date: 2026-08-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def _col_exists(table, column):
    result = op.get_bind().execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name=:t AND column_name=:c"
        ),
        {"t": table, "c": column},
    ).fetchone()
    return result is not None


def upgrade():
    # --- users ---
    # hashed_password -> password_hash
    if _col_exists('users', 'hashed_password'):
        op.alter_column('users', 'hashed_password', new_column_name='password_hash')

    # Add invited_by (FK to users.id) if missing
    if not _col_exists('users', 'invited_by'):
        op.add_column('users', sa.Column('invited_by', UUID(as_uuid=True), nullable=True))

    # Add last_seen_at if missing
    if not _col_exists('users', 'last_seen_at'):
        op.add_column('users', sa.Column('last_seen_at', sa.DateTime(), nullable=True))

    # --- invitations ---
    # invited_by_id -> invited_by
    if _col_exists('invitations', 'invited_by_id'):
        op.alter_column('invitations', 'invited_by_id', new_column_name='invited_by')

    # is_accepted (bool) -> accepted_at (datetime)
    if _col_exists('invitations', 'is_accepted') and not _col_exists('invitations', 'accepted_at'):
        op.add_column('invitations', sa.Column('accepted_at', sa.DateTime(), nullable=True))
        op.drop_column('invitations', 'is_accepted')


def downgrade():
    if _col_exists('users', 'password_hash'):
        op.alter_column('users', 'password_hash', new_column_name='hashed_password')
    if _col_exists('invitations', 'invited_by'):
        op.alter_column('invitations', 'invited_by', new_column_name='invited_by_id')
