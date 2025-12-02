# Render Database Setup Guide

If you're running QuantumReview on Render Postgres, run these SQL queries to set up the database schema.

## Initial Schema (Migration 001)

```sql
-- Create organizations table
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    github_org_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_organizations_github_org_id ON organizations(github_org_id);
CREATE INDEX ix_organizations_name ON organizations(name);

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    github_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    avatar_url VARCHAR(512),
    github_token VARCHAR(1024),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_users_github_id ON users(github_id);
CREATE INDEX ix_users_username ON users(username);

-- Create repos table
CREATE TABLE repos (
    id SERIAL PRIMARY KEY,
    repo_full_name VARCHAR(512) NOT NULL UNIQUE,
    installation_id BIGINT,
    is_installed BOOLEAN DEFAULT FALSE,
    owner_org_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (owner_org_id) REFERENCES organizations(id) ON DELETE SET NULL
);

CREATE INDEX ix_repos_repo_full_name ON repos(repo_full_name);
CREATE INDEX ix_repos_installation_id ON repos(installation_id);

-- Create user_repo_roles table
CREATE TABLE user_repo_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    repo_id INTEGER NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (repo_id) REFERENCES repos(id) ON DELETE CASCADE
);

CREATE INDEX ix_user_repo_roles_user_id ON user_repo_roles(user_id);
CREATE INDEX ix_user_repo_roles_repo_id ON user_repo_roles(repo_id);

-- Create issues table
CREATE TABLE issues (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    issue_number INTEGER NOT NULL,
    title VARCHAR(512) NOT NULL,
    body TEXT,
    checklist_json JSONB,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (repo_id) REFERENCES repos(id) ON DELETE CASCADE
);

CREATE INDEX ix_issues_repo_id ON issues(repo_id);
CREATE INDEX ix_issues_issue_number ON issues(issue_number);

-- Create checklist_items table
CREATE TABLE checklist_items (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL,
    item_id VARCHAR(50) NOT NULL,
    text TEXT NOT NULL,
    required VARCHAR(50) DEFAULT 'false' NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    linked_test_ids JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE
);

CREATE INDEX ix_checklist_items_issue_id ON checklist_items(issue_id);

-- Create pull_requests table
CREATE TABLE pull_requests (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    pr_number INTEGER NOT NULL,
    head_sha VARCHAR(40),
    linked_issue_id INTEGER,
    test_manifest JSONB,
    validation_status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (repo_id) REFERENCES repos(id) ON DELETE CASCADE,
    FOREIGN KEY (linked_issue_id) REFERENCES issues(id) ON DELETE SET NULL
);

CREATE INDEX ix_pull_requests_repo_id ON pull_requests(repo_id);
CREATE INDEX ix_pull_requests_pr_number ON pull_requests(pr_number);

-- Create test_results table
CREATE TABLE test_results (
    id SERIAL PRIMARY KEY,
    pr_id INTEGER NOT NULL,
    test_id VARCHAR(255) NOT NULL,
    name VARCHAR(512) NOT NULL,
    status VARCHAR(50) NOT NULL,
    log_url VARCHAR(512),
    checklist_ids JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (pr_id) REFERENCES pull_requests(id) ON DELETE CASCADE
);

CREATE INDEX ix_test_results_pr_id ON test_results(pr_id);
CREATE INDEX ix_test_results_test_id ON test_results(test_id);

-- Create code_health table
CREATE TABLE code_health (
    id SERIAL PRIMARY KEY,
    pr_id INTEGER NOT NULL UNIQUE,
    score INTEGER NOT NULL,
    findings JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (pr_id) REFERENCES pull_requests(id) ON DELETE CASCADE
);

CREATE INDEX ix_code_health_pr_id ON code_health(pr_id);

-- Create reports table
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    pr_id INTEGER NOT NULL,
    report_content TEXT,
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (pr_id) REFERENCES pull_requests(id) ON DELETE CASCADE
);

CREATE INDEX ix_reports_pr_id ON reports(pr_id);

-- Create notifications table
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    repo_id INTEGER NOT NULL,
    kind VARCHAR(100) NOT NULL,
    payload JSONB,
    read BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (repo_id) REFERENCES repos(id) ON DELETE CASCADE
);

CREATE INDEX ix_notifications_user_id ON notifications(user_id);
CREATE INDEX ix_notifications_repo_id ON notifications(repo_id);
CREATE INDEX ix_notifications_read ON notifications(read);

-- Create audit_logs table
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    actor_user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id INTEGER NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX ix_audit_logs_actor_user_id ON audit_logs(actor_user_id);
CREATE INDEX ix_audit_logs_action ON audit_logs(action);
CREATE INDEX ix_audit_logs_target_type ON audit_logs(target_type);
CREATE INDEX ix_audit_logs_target_id ON audit_logs(target_id);
```

## Migration 002: Add GitHub Token Support

This migration adds the `github_token` column to the `users` table, enabling the backend to fetch GitHub App installations on behalf of users.

```sql
-- Add github_token column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS github_token VARCHAR(1024);
```

## Setup Instructions

1. **Connect to Render Postgres**
   - Navigate to your Render Postgres instance in the Render dashboard
   - Click "Connect"
   - Use the internal or external connection string

2. **Run the SQL Queries**
   - Copy all SQL queries above (both Migration 001 and 002 if this is a fresh database)
   - Paste into your database client (psql, pgAdmin, or Render's SQL editor)
   - Run the queries

3. **Verify the Schema**
   ```sql
   -- List all tables
   SELECT tablename FROM pg_tables WHERE schemaname = 'public';
   
   -- Check users table columns
   \d users;
   ```

## Troubleshooting

**Error: "table already exists"**
- This means the schema was already created. Skip migration 001 and only run migration 002.

**Error: "column already exists"**
- The column has been added previously. No action needed.

**GitHub App installations not showing**
- Ensure the `github_token` column exists in the `users` table.
- Verify the backend is storing the OAuth token during login (check the updated auth callback in the backend code).

