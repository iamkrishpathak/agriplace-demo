"""Initial Logistics

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
    op.create_table('deliveries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('order_id', sa.String(length=36), nullable=False),
        sa.Column('transporter_id', sa.String(length=36), nullable=True),
        sa.Column('vehicle_id', sa.String(length=36), nullable=True),
        sa.Column('route_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('cargo_kg', sa.Float(), nullable=False),
        sa.Column('estimated_distance_km', sa.Float(), nullable=False),
        sa.Column('estimated_duration_hours', sa.Float(), nullable=False),
        sa.Column('estimated_earnings', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('delivery_stops',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('delivery_id', sa.String(length=36), nullable=False),
        sa.Column('location_id', sa.String(length=36), nullable=False),
        sa.Column('stop_type', sa.String(length=40), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('planned_quantity_kg', sa.Float(), nullable=False),
        sa.Column('actual_quantity_kg', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(['delivery_id'], ['deliveries.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('incidents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('delivery_id', sa.String(length=36), nullable=False),
        sa.Column('reported_by_id', sa.String(length=36), nullable=False),
        sa.Column('incident_type', sa.String(length=80), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('evidence_urls', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['delivery_id'], ['deliveries.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('incidents')
    op.drop_table('delivery_stops')
    op.drop_table('deliveries')
