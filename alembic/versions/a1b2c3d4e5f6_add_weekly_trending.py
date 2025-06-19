"""Add weekly trending summary table

Revision ID: a1b2c3d4e5f6
Revises: e54222444f09
Create Date: 2025-06-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'e54222444f09'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create weekly trending phrases table
    op.create_table('weekly_trending_phrases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('week_start', sa.Date(), nullable=False),
        sa.Column('week_end', sa.Date(), nullable=False),
        sa.Column('phrase', sa.String(), nullable=False),
        sa.Column('total_score', sa.Float(), nullable=False),
        sa.Column('average_score', sa.Float(), nullable=False),
        sa.Column('total_frequency', sa.Integer(), nullable=False),
        sa.Column('appearance_days', sa.Integer(), nullable=False),
        sa.Column('phrase_type', sa.String(), nullable=False),
        sa.Column('dominant_source', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_weekly_trending_phrases_week_start'), 'weekly_trending_phrases', ['week_start'], unique=False)
    op.create_index(op.f('ix_weekly_trending_phrases_id'), 'weekly_trending_phrases', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_weekly_trending_phrases_id'), table_name='weekly_trending_phrases')
    op.drop_index(op.f('ix_weekly_trending_phrases_week_start'), table_name='weekly_trending_phrases')
    op.drop_table('weekly_trending_phrases')
