"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # organizations
    op.create_table('organizations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )

    # users
    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('role', sa.String(), server_default='agent', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'email'),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # invitations
    op.create_table('invitations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('role', sa.String(), server_default='agent', nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('invited_by_id', sa.String(), nullable=True),
        sa.Column('is_accepted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invited_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
    )

    # inboxes
    op.create_table('inboxes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('widget_key', sa.String(), nullable=True),
        sa.Column('email_address', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('settings', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('widget_key'),
    )

    # contacts
    op.create_table('contacts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_contacts_org_email', 'contacts', ['organization_id', 'email'])

    # sla_policies
    op.create_table('sla_policies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('first_response_hours', sa.Integer(), nullable=False),
        sa.Column('resolution_hours', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # conversations
    op.create_table('conversations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('inbox_id', sa.String(), nullable=True),
        sa.Column('contact_id', sa.String(), nullable=False),
        sa.Column('assigned_to_id', sa.String(), nullable=True),
        sa.Column('sla_policy_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), server_default='open', nullable=False),
        sa.Column('channel', sa.String(), server_default='chat', nullable=False),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('email_thread_id', sa.String(), nullable=True),
        sa.Column('last_message_id', sa.String(), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('first_response_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('snoozed_until', sa.DateTime(), nullable=True),
        sa.Column('sla_first_response_due', sa.DateTime(), nullable=True),
        sa.Column('sla_resolution_due', sa.DateTime(), nullable=True),
        sa.Column('sla_breached', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['inbox_id'], ['inboxes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['sla_policy_id'], ['sla_policies.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_conversations_org_status', 'conversations', ['organization_id', 'status'])
    op.create_index('ix_conversations_contact', 'conversations', ['contact_id'])

    # messages
    op.create_table('messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('sender_type', sa.String(), nullable=False),
        sa.Column('sender_id', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_type', sa.String(), server_default='text', nullable=False),
        sa.Column('attachments', postgresql.JSONB(), server_default='[]', nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('email_message_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_messages_conversation', 'messages', ['conversation_id', 'created_at'])

    # kb_categories
    op.create_table('kb_categories',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('position', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # kb_articles
    op.create_table('kb_articles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('category_id', sa.String(), nullable=True),
        sa.Column('author_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), server_default='draft', nullable=False),
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        sa.Column('view_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['kb_categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'slug'),
    )
    op.create_index('ix_kb_articles_search', 'kb_articles', ['search_vector'], postgresql_using='gin')

    # canned_responses
    op.create_table('canned_responses',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('shortcut', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_by_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    # webhooks
    op.create_table('webhooks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('events', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
        sa.Column('secret', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('failure_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_delivery_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # webhook_deliveries
    op.create_table('webhook_deliveries',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('webhook_id', sa.String(), nullable=False),
        sa.Column('event', sa.String(), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('status', sa.String(), server_default='pending', nullable=False),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('attempt_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('next_retry_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['webhook_id'], ['webhooks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_webhook_deliveries_retry', 'webhook_deliveries', ['status', 'next_retry_at'])

    # api_keys
    op.create_table('api_keys',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('key_hash', sa.String(), nullable=False),
        sa.Column('key_prefix', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash'),
    )

    # custom_domains
    op.create_table('custom_domains',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('domain', sa.String(), nullable=False),
        sa.Column('txt_record', sa.String(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain'),
    )

    # ai_drafts
    op.create_table('ai_drafts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('kb_sources', postgresql.JSONB(), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # page_views
    op.create_table('page_views',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('contact_id', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('referrer', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_page_views_contact', 'page_views', ['contact_id', 'created_at'])

    # KB article search trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION kb_article_search_trigger() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := to_tsvector('english', coalesce(NEW.title, '') || ' ' || coalesce(NEW.content, ''));
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER kb_article_search_update
            BEFORE INSERT OR UPDATE OF title, content
            ON kb_articles
            FOR EACH ROW EXECUTE FUNCTION kb_article_search_trigger();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS kb_article_search_update ON kb_articles")
    op.execute("DROP FUNCTION IF EXISTS kb_article_search_trigger")

    for table in [
        'page_views', 'ai_drafts', 'custom_domains', 'api_keys',
        'webhook_deliveries', 'webhooks', 'canned_responses',
        'kb_articles', 'kb_categories', 'messages', 'conversations',
        'sla_policies', 'contacts', 'inboxes', 'invitations', 'users', 'organizations',
    ]:
        op.drop_table(table)
