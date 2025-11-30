"""Initial database schema

Revision ID: 001_initial
Revises:
Create Date: 2025-11-24

Creates the core tables for AI conversation system:
- users: User accounts (MVP: single user)
- sessions: Conversation sessions
- messages: User and AI messages
- charts: Chart configurations from MCP server
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建users表
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('last_active_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_index('idx_users_username', 'users', ['username'])

    # 插入MVP默认用户
    op.execute("""
        INSERT INTO users (id, username, email)
        VALUES (1, 'default_user', 'user@example.com')
    """)

    # 创建sessions表
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('message_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_sessions_user', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Sessions表索引
    op.create_index(
        'idx_sessions_user_updated',
        'sessions',
        ['user_id', sa.text('updated_at DESC')],
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    op.create_index(
        'idx_sessions_deleted',
        'sessions',
        ['deleted_at'],
        postgresql_where=sa.text('deleted_at IS NOT NULL')
    )
    op.create_index(
        'idx_sessions_created_brin',
        'sessions',
        ['created_at'],
        postgresql_using='brin'
    )

    # Sessions表触发器: 自动更新updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_sessions_updated_at
        BEFORE UPDATE ON sessions
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)

    # 创建messages表
    op.create_table(
        'messages',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('session_id', postgresql.UUID(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.CheckConstraint("role IN ('user', 'assistant')", name='check_messages_role'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], name='fk_messages_session', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Messages表索引
    op.create_index(
        'idx_messages_session_sequence',
        'messages',
        ['session_id', sa.text('sequence DESC')]
    )
    op.create_index(
        'idx_messages_session_created',
        'messages',
        ['session_id', sa.text('created_at DESC')]
    )
    op.create_index(
        'idx_messages_created_brin',
        'messages',
        ['created_at'],
        postgresql_using='brin'
    )

    # Messages表触发器: 自动设置sequence和更新session的message_count
    op.execute("""
        CREATE OR REPLACE FUNCTION increment_message_sequence()
        RETURNS TRIGGER AS $$
        BEGIN
            -- 自动设置sequence为当前会话的最大sequence + 1
            SELECT COALESCE(MAX(sequence), -1) + 1
            INTO NEW.sequence
            FROM messages
            WHERE session_id = NEW.session_id;

            -- 更新会话message_count
            UPDATE sessions
            SET message_count = message_count + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.session_id;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_messages_sequence
        BEFORE INSERT ON messages
        FOR EACH ROW
        EXECUTE FUNCTION increment_message_sequence();
    """)

    # 创建charts表
    op.create_table(
        'charts',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('message_id', sa.BigInteger(), nullable=False),
        sa.Column('chart_type', sa.String(length=50), nullable=False),
        sa.Column('chart_config', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('sequence', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], name='fk_charts_message', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Charts表索引
    op.create_index('idx_charts_message', 'charts', ['message_id', 'sequence'])
    op.create_index('idx_charts_type', 'charts', ['chart_type'])


def downgrade() -> None:
    # 删除charts表
    op.drop_index('idx_charts_type', table_name='charts')
    op.drop_index('idx_charts_message', table_name='charts')
    op.drop_table('charts')

    # 删除messages表及触发器
    op.execute('DROP TRIGGER IF EXISTS trigger_messages_sequence ON messages')
    op.execute('DROP FUNCTION IF EXISTS increment_message_sequence()')
    op.drop_index('idx_messages_created_brin', table_name='messages')
    op.drop_index('idx_messages_session_created', table_name='messages')
    op.drop_index('idx_messages_session_sequence', table_name='messages')
    op.drop_table('messages')

    # 删除sessions表及触发器
    op.execute('DROP TRIGGER IF EXISTS trigger_sessions_updated_at ON sessions')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    op.drop_index('idx_sessions_created_brin', table_name='sessions')
    op.drop_index('idx_sessions_deleted', table_name='sessions')
    op.drop_index('idx_sessions_user_updated', table_name='sessions')
    op.drop_table('sessions')

    # 删除users表
    op.drop_index('idx_users_username', table_name='users')
    op.drop_table('users')
