"""Add buffer_activity table

Revision ID: f8a2c3d4e5b6
Revises: 421388cbdc75
Create Date: 2025-06-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8a2c3d4e5b6'
down_revision = '421388cbdc75'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'buffer_activity',
        sa.Column('buffer_activity_id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(),
                   sa.ForeignKey('user.user_id'), index=True),
        sa.Column('time', sa.DateTime()),
        sa.Column('tokens', sa.Integer()),
        sa.Column('description', sa.String(200), nullable=True),
    )


def downgrade():
    op.drop_table('buffer_activity')
