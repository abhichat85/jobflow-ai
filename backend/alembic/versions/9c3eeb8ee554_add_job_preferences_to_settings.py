"""add_job_preferences_to_settings

Revision ID: 9c3eeb8ee554
Revises: 7c7afa3e752a
Create Date: 2026-05-17 00:18:40.083080

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c3eeb8ee554'
down_revision: Union[str, None] = '7c7afa3e752a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_settings", sa.Column("job_titles", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("user_settings", sa.Column("locations", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("user_settings", sa.Column("remote_preference", sa.String(20), nullable=False, server_default="any"))
    op.add_column("user_settings", sa.Column("seniority_levels", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("user_settings", sa.Column("company_stage", sa.String(20), nullable=False, server_default="any"))
    op.add_column("user_settings", sa.Column("min_salary", sa.Integer(), nullable=True))
    op.add_column("user_settings", sa.Column("linkedin_auth_status", sa.String(20), nullable=False, server_default="disconnected"))
    op.add_column("user_settings", sa.Column("linkedin_search_urls", sa.Text(), nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("user_settings", "linkedin_search_urls")
    op.drop_column("user_settings", "linkedin_auth_status")
    op.drop_column("user_settings", "min_salary")
    op.drop_column("user_settings", "company_stage")
    op.drop_column("user_settings", "seniority_levels")
    op.drop_column("user_settings", "remote_preference")
    op.drop_column("user_settings", "locations")
    op.drop_column("user_settings", "job_titles")
