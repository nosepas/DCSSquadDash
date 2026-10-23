"""Discord <-> UCID pairs claimed by agents (verified by DCSServerBot)

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('discord_link_claims',
    sa.Column('server_id', sa.String(length=36), nullable=False),
    sa.Column('ucid', sa.String(), nullable=False),
    sa.Column('discord_id', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('server_id', 'ucid')
    )
    op.create_index(op.f('ix_discord_link_claims_discord_id'), 'discord_link_claims', ['discord_id'], unique=False)
    op.create_index(op.f('ix_discord_link_claims_ucid'), 'discord_link_claims', ['ucid'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_discord_link_claims_ucid'), table_name='discord_link_claims')
    op.drop_index(op.f('ix_discord_link_claims_discord_id'), table_name='discord_link_claims')
    op.drop_table('discord_link_claims')
