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
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('plan', sa.String(50), server_default='free', nullable=False),
        sa.Column('widget_color', sa.String(7), server_default='#6366f1', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index('ix_organizations_slug', 'organizations', ['slug'])

    # users
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), server_default='agent', nullable=False),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('invited_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_org', 'users', ['organization_id'])

    # invitations
    op.create_table('invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), server_default='agent', nullable=False),
        sa.Column('token', sa.String(255), nullable=False),
        sa.Column('invited_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
    )
    op.create_index('ix_invitations_org', 'invitations', ['organization_id'])
    op.create_index('ix_invitations_email', 'invitations', ['email'])

    # inboxes
    op.create_table('inboxes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('widget_key', sa.String(255), nullable=True),
        sa.Column('email_address', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('widget_key'),
    )
    op.create_index('ix_inboxes_org', 'inboxes', ['organization_id'])

    # contacts
    op.create_table('contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('external_id', sa.String(255), nullable=True),
        sa.Column('visitor_id', sa.String(255), nullable=True),
        sa.Column('browser', sa.String(100), nullable=True),
        sa.Column('os', sa.String(100), nullable=True),
        sa.Column('timezone', sa.String(100), nullable=True),
        sa.Column('location', postgresql.JSONB(), server_default='{}', nullable=True),
        sa.Column('custom_attributes', postgresql.JSONB(), server_default='{}', nullable=True),
        sa.Column('first_seen_at', sa.DateTime(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_contacts_org', 'contacts', ['organization_id'])
    op.create_index('ix_contacts_visitor_id', 'contacts', ['visitor_id'])

    # sla_policies
    op.create_table('sla_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('first_response_hours', sa.Integer(), nullable=False, server_default='8'),
        sa.Column('resolution_hours', sa.Integer(), nullable=False, server_default='48'),
        sa.Column('business_hours_only', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # conversations
    op.create_table('conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('inbox_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sla_policy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), server_default='open', nullable=False),
        sa.Column('subject', sa.Text(), nullable=True),
        sa.Column('snoozed_until', sa.DateTime(), nullable=True),
        sa.Column('sla_breach', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('first_response_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('summary_cached_at', sa.DateTime(), nullable=True),
        sa.Column('meta', postgresql.JSONB(), server_default='{}', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['inbox_id'], ['inboxes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['sla_policy_id'], ['sla_policies.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_conversations_org_status', 'conversations', ['organization_id', 'status'])
    op.create_index('ix_conversations_org', 'conversations', ['organization_id'])
    op.create_index('ix_conversations_assigned_to', 'conversations', ['assigned_to'])
    op.create_index('ix_conversations_created_at', 'conversations', ['created_at'])

    # messages
    op.create_table('messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_type', sa.String(50), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_type', sa.String(50), server_default='text', nullable=False),
        sa.Column('attachments', postgresql.JSONB(), server_default='[]', nullable=True),
        sa.Column('email_message_id', sa.String(500), nullable=True),
        sa.Column('email_in_reply_to', sa.String(500), nullable=True),
        sa.Column('email_references', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('meta', postgresql.JSONB(), server_default='{}', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_messages_conversation', 'messages', ['conversation_id', 'created_at'])
    op.create_index('ix_messages_email_message_id', 'messages', ['email_message_id'])

    # kb_categories
    op.create_table('kb_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(100), nullable=True),
        sa.Column('position', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_public', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'slug'),
    )

    # kb_articles
    op.create_table('kb_articles',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('slug', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), server_default='draft', nullable=False),
        sa.Column('position', sa.Integer(), server_default='0', nullable=False),
        sa.Column('views', sa.Integer(), server_default='0', nullable=False),
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['kb_categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'slug'),
    )
    op.create_index('ix_kb_articles_search', 'kb_articles', ['search_vector'], postgresql_using='gin')
    op.create_index('ix_kb_articles_org', 'kb_articles', ['organization_id'])

    # canned_responses
    op.create_table('canned_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('shortcut', sa.String(100), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.String()), server_default='{}', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    # webhooks
    op.create_table('webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('secret', sa.String(255), nullable=False),
        sa.Column('events', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('failure_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # webhook_deliveries
    op.create_table('webhook_deliveries',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('webhook_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('attempt_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('next_retry_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['webhook_id'], ['webhooks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_webhook_deliveries_next_retry', 'webhook_deliveries', ['next_retry_at'])

    # api_keys
    op.create_table('api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False),
        sa.Column('key_prefix', sa.String(20), nullable=False),
        sa.Column('scopes', postgresql.ARRAY(sa.String()), server_default='{}', nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash'),
    )
    op.create_index('ix_api_keys_prefix', 'api_keys', ['key_prefix'])

    # custom_domains
    op.create_table('custom_domains',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('verification_token', sa.String(255), nullable=False),
        sa.Column('dns_record_type', sa.String(10), server_default='TXT', nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('last_checked_at', sa.DateTime(), nullable=True),
        sa.Column('ssl_status', sa.String(50), server_default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain'),
    )

    # ai_draft_suggestions
    op.create_table('ai_draft_suggestions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('draft_content', sa.Text(), nullable=False),
        sa.Column('kb_articles_used', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default='{}', nullable=True),
        sa.Column('status', sa.String(50), server_default='pending', nullable=False),
        sa.Column('accepted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['accepted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ai_drafts_conversation', 'ai_draft_suggestions', ['conversation_id'])

    # contact_page_views
    op.create_table('contact_page_views',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('referrer', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_page_views_contact', 'contact_page_views', ['contact_id', 'created_at'])

    # KB full-text search trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION kb_article_search_trigger() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := to_tsvector('english',
                coalesce(NEW.title, '') || ' ' || coalesce(NEW.content_text, ''));
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER kb_article_search_update
            BEFORE INSERT OR UPDATE OF title, content_text
            ON kb_articles
            FOR EACH ROW EXECUTE FUNCTION kb_article_search_trigger();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS kb_article_search_update ON kb_articles")
    op.execute("DROP FUNCTION IF EXISTS kb_article_search_trigger")
    for table in [
        'contact_page_views', 'ai_draft_suggestions', 'custom_domains', 'api_keys',
        'webhook_deliveries', 'webhooks', 'canned_responses',
        'kb_articles', 'kb_categories', 'messages', 'conversations',
        'sla_policies', 'contacts', 'inboxes', 'invitations', 'users', 'organizations',
    ]:
        op.drop_table(table)
