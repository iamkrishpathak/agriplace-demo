"""Initial ML

Revision ID: 001
Revises: 
Create Date: 2026-08-28 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('demand_predictions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('crop_id', sa.String(length=36), nullable=False),
        sa.Column('region', sa.String(length=80), nullable=False),
        sa.Column('horizon_days', sa.Integer(), nullable=False),
        sa.Column('demand_level', sa.String(length=40), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('proxy_basis', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('route_plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('vehicle_id', sa.String(length=36), nullable=False),
        sa.Column('total_distance_km', sa.Float(), nullable=False),
        sa.Column('stops_sequence', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('route_plans')
    op.drop_table('demand_predictions')
