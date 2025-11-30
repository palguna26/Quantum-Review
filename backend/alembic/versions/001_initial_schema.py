"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-15 10:00:00.000000

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
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('github_org_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_github_org_id'), 'organizations', ['github_org_id'], unique=True)
    op.create_index(op.f('ix_organizations_name'), 'organizations', ['name'], unique=False)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('github_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_github_id'), 'users', ['github_id'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)

    # Create repos table
    op.create_table(
        'repos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repo_full_name', sa.String(length=512), nullable=False),
        sa.Column('installation_id', sa.BigInteger(), nullable=True),
        sa.Column('is_installed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('owner_org_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_org_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_repos_repo_full_name'), 'repos', ['repo_full_name'], unique=True)
    op.create_index(op.f('ix_repos_installation_id'), 'repos', ['installation_id'], unique=False)

    # Create user_repo_roles table
    op.create_table(
        'user_repo_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('repo_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repo_id'], ['repos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_repo_roles_user_id'), 'user_repo_roles', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_repo_roles_repo_id'), 'user_repo_roles', ['repo_id'], unique=False)

    # Create issues table
    op.create_table(
        'issues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repo_id', sa.Integer(), nullable=False),
        sa.Column('issue_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('checklist_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['repo_id'], ['repos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_issues_repo_id'), 'issues', ['repo_id'], unique=False)
    op.create_index(op.f('ix_issues_issue_number'), 'issues', ['issue_number'], unique=False)

    # Create checklist_items table
    op.create_table(
        'checklist_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.String(length=50), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('required', sa.String(length=50), nullable=False, server_default='false'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('linked_test_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_checklist_items_issue_id'), 'checklist_items', ['issue_id'], unique=False)

    # Create pull_requests table
    op.create_table(
        'pull_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repo_id', sa.Integer(), nullable=False),
        sa.Column('pr_number', sa.Integer(), nullable=False),
        sa.Column('head_sha', sa.String(length=40), nullable=True),
        sa.Column('linked_issue_id', sa.Integer(), nullable=True),
        sa.Column('test_manifest', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('validation_status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['repo_id'], ['repos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['linked_issue_id'], ['issues.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pull_requests_repo_id'), 'pull_requests', ['repo_id'], unique=False)
    op.create_index(op.f('ix_pull_requests_pr_number'), 'pull_requests', ['pr_number'], unique=False)

    # Create test_results table
    op.create_table(
        'test_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pr_id', sa.Integer(), nullable=False),
        sa.Column('test_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=512), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('log_url', sa.String(length=512), nullable=True),
        sa.Column('checklist_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['pr_id'], ['pull_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_test_results_pr_id'), 'test_results', ['pr_id'], unique=False)
    op.create_index(op.f('ix_test_results_test_id'), 'test_results', ['test_id'], unique=False)

    # Create code_health table
    op.create_table(
        'code_health',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pr_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('findings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['pr_id'], ['pull_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pr_id')
    )
    op.create_index(op.f('ix_code_health_pr_id'), 'code_health', ['pr_id'], unique=True)

    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pr_id', sa.Integer(), nullable=False),
        sa.Column('report_content', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['pr_id'], ['pull_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_pr_id'), 'reports', ['pr_id'], unique=False)

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('repo_id', sa.Integer(), nullable=False),
        sa.Column('kind', sa.String(length=100), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repo_id'], ['repos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_notifications_repo_id'), 'notifications', ['repo_id'], unique=False)
    op.create_index(op.f('ix_notifications_read'), 'notifications', ['read'], unique=False)

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actor_user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_actor_user_id'), 'audit_logs', ['actor_user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_target_type'), 'audit_logs', ['target_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_target_id'), 'audit_logs', ['target_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_logs_target_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_target_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_actor_user_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_notifications_read'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_repo_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_table('notifications')
    op.drop_index(op.f('ix_reports_pr_id'), table_name='reports')
    op.drop_table('reports')
    op.drop_index(op.f('ix_code_health_pr_id'), table_name='code_health')
    op.drop_table('code_health')
    op.drop_index(op.f('ix_test_results_test_id'), table_name='test_results')
    op.drop_index(op.f('ix_test_results_pr_id'), table_name='test_results')
    op.drop_table('test_results')
    op.drop_index(op.f('ix_pull_requests_pr_number'), table_name='pull_requests')
    op.drop_index(op.f('ix_pull_requests_repo_id'), table_name='pull_requests')
    op.drop_table('pull_requests')
    op.drop_index(op.f('ix_checklist_items_issue_id'), table_name='checklist_items')
    op.drop_table('checklist_items')
    op.drop_index(op.f('ix_issues_issue_number'), table_name='issues')
    op.drop_index(op.f('ix_issues_repo_id'), table_name='issues')
    op.drop_table('issues')
    op.drop_index(op.f('ix_user_repo_roles_repo_id'), table_name='user_repo_roles')
    op.drop_index(op.f('ix_user_repo_roles_user_id'), table_name='user_repo_roles')
    op.drop_table('user_repo_roles')
    op.drop_index(op.f('ix_repos_installation_id'), table_name='repos')
    op.drop_index(op.f('ix_repos_repo_full_name'), table_name='repos')
    op.drop_table('repos')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_github_id'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_organizations_name'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_github_org_id'), table_name='organizations')
    op.drop_table('organizations')

