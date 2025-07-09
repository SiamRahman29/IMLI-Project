"""merge_migrations

Revision ID: 599bca21adbd
Revises: 094727eeafe8, add_password_reset_otp
Create Date: 2025-07-07 18:48:42.046250

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '599bca21adbd'
down_revision: Union[str, None] = ('094727eeafe8', 'add_password_reset_otp')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
