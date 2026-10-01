"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-01 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('hospital_name', sa.String(length=200), server_default='University Medical Center', nullable=False),
        sa.Column('role', sa.String(length=50), server_default='doctor', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. Create diagnosis_records table
    op.create_table(
        'diagnosis_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('modality', sa.String(length=50), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('image_path', sa.String(length=500), nullable=False),
        sa.Column('predicted_class', sa.String(length=100), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('class_probabilities', sa.JSON(), nullable=False),
        sa.Column('symptom_data', sa.JSON(), nullable=False),
        sa.Column('gradcam_path', sa.String(length=500), nullable=False),
        sa.Column('image_prediction', sa.String(length=100), nullable=True),
        sa.Column('image_confidence', sa.Float(), nullable=True),
        sa.Column('fusion_prediction', sa.String(length=100), nullable=True),
        sa.Column('fusion_confidence', sa.Float(), nullable=True),
        sa.Column('model_version', sa.String(length=50), server_default='densenet121-multimodal-v1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_diagnosis_records_id'), 'diagnosis_records', ['id'], unique=False)
    op.create_index(op.f('ix_diagnosis_records_user_id'), 'diagnosis_records', ['user_id'], unique=False)
    op.create_index(op.f('ix_diagnosis_records_modality'), 'diagnosis_records', ['modality'], unique=False)
    op.create_index(op.f('ix_diagnosis_records_created_at'), 'diagnosis_records', ['created_at'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_diagnosis_records_created_at'), table_name='diagnosis_records')
    op.drop_index(op.f('ix_diagnosis_records_modality'), table_name='diagnosis_records')
    op.drop_index(op.f('ix_diagnosis_records_user_id'), table_name='diagnosis_records')
    op.drop_index(op.f('ix_diagnosis_records_id'), table_name='diagnosis_records')
    op.drop_table('diagnosis_records')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
