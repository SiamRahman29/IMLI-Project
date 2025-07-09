"""add_unique_constraint_to_trending_phrases_simple

Revision ID: simple_constraint
Revises: 599bca21adbd
Create Date: 2025-07-07 18:53:20.956130

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'simple_constraint'
down_revision: Union[str, None] = '599bca21adbd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraint to trending_phrases table."""
    # Add unique constraint to prevent duplicate phrases
    op.create_unique_constraint(
        'uq_phrase_date_type_source', 
        'trending_phrases', 
        ['date', 'phrase', 'phrase_type', 'source']
    )


def downgrade() -> None:
    """Remove unique constraint from trending_phrases table."""
    op.drop_constraint('uq_phrase_date_type_source', 'trending_phrases', type_='unique')
