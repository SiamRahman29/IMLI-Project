"""Add password reset OTP fields to users table

Revision ID: add_password_reset_otp
Revises: 
Create Date: 2025-01-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_password_reset_otp'
down_revision = None
head = None
branch_labels = None
depends_on = None

def upgrade():
    # Add OTP fields to users table
    op.add_column('users', sa.Column('reset_otp', sa.String(), nullable=True))
    op.add_column('users', sa.Column('reset_otp_expires', sa.DateTime(), nullable=True))

def downgrade():
    # Remove OTP fields from users table
    op.drop_column('users', 'reset_otp_expires')
    op.drop_column('users', 'reset_otp')
