"""Add github_token column to users table.

Revision ID: 002
Revises: 001
Create Date: 2025-12-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add github_token column to users table
    op.add_column('users', sa.Column('github_token', sa.String(1024), nullable=True))


def downgrade() -> None:
    # Remove github_token column from users table
    op.drop_column('users', 'github_token')
