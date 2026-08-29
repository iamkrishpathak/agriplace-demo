"""Initial Marketplace

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
    op.create_table('crops',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('hindi_name', sa.String(length=120), nullable=False),
        sa.Column('perishability', sa.String(length=40), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table('produce_listings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('farmer_id', sa.String(length=36), nullable=False),
        sa.Column('crop_id', sa.String(length=36), nullable=False),
        sa.Column('location_id', sa.String(length=36), nullable=False),
        sa.Column('quantity_kg', sa.Float(), nullable=False),
        sa.Column('available_date', sa.Date(), nullable=False),
        sa.Column('grade', sa.String(length=40), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('expected_price_per_kg', sa.Float(), nullable=False),
        sa.Column('image_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['crop_id'], ['crops.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('buyer_requirements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('buyer_id', sa.String(length=36), nullable=False),
        sa.Column('crop_id', sa.String(length=36), nullable=False),
        sa.Column('destination_location_id', sa.String(length=36), nullable=False),
        sa.Column('required_quantity_kg', sa.Float(), nullable=False),
        sa.Column('grade', sa.String(length=40), nullable=False),
        sa.Column('needed_by', sa.Date(), nullable=False),
        sa.Column('max_price_per_kg', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('recurring', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['crop_id'], ['crops.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('order_matches',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('requirement_id', sa.String(length=36), nullable=False),
        sa.Column('listing_id', sa.String(length=36), nullable=False),
        sa.Column('quantity_kg', sa.Float(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('score_breakdown', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['listing_id'], ['produce_listings.id'], ),
        sa.ForeignKeyConstraint(['requirement_id'], ['buyer_requirements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('order_matches')
    op.drop_table('buyer_requirements')
    op.drop_table('produce_listings')
    op.drop_table('crops')
