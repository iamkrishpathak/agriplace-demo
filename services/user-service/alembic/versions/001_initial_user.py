"""Initial User profiles

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
    op.create_table('locations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('label', sa.String(length=160), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('district', sa.String(length=120), nullable=False),
        sa.Column('state', sa.String(length=120), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('location_type', sa.String(length=80), nullable=False),
        sa.Column('data_classification', sa.String(length=40), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_locations_user_id'), 'locations', ['user_id'], unique=False)
    
    op.create_table('farmer_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('village', sa.String(length=120), nullable=False),
        sa.Column('district', sa.String(length=120), nullable=False),
        sa.Column('state', sa.String(length=120), nullable=False),
        sa.Column('land_acres', sa.Float(), nullable=False),
        sa.Column('fpo_id', sa.String(length=36), nullable=True),
        sa.Column('verification_status', sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    op.create_table('buyer_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('buyer_type', sa.String(length=80), nullable=False),
        sa.Column('business_name', sa.String(length=160), nullable=False),
        sa.Column('gstin', sa.String(length=32), nullable=True),
        sa.Column('verification_status', sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    op.create_table('transporter_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('company_name', sa.String(length=160), nullable=False),
        sa.Column('license_number', sa.String(length=80), nullable=False),
        sa.Column('verification_status', sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    op.create_table('vehicles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transporter_id', sa.String(length=36), nullable=False),
        sa.Column('registration_number', sa.String(length=40), nullable=False),
        sa.Column('vehicle_type', sa.String(length=80), nullable=False),
        sa.Column('capacity_kg', sa.Float(), nullable=False),
        sa.Column('cold_chain', sa.Boolean(), nullable=False),
        sa.Column('document_status', sa.String(length=40), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('registration_number')
    )

def downgrade() -> None:
    op.drop_table('vehicles')
    op.drop_table('transporter_profiles')
    op.drop_table('buyer_profiles')
    op.drop_table('farmer_profiles')
    op.drop_index(op.f('ix_locations_user_id'), table_name='locations')
    op.drop_table('locations')
