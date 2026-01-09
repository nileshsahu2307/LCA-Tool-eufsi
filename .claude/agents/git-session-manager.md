# Git Session Manager Agent

## Purpose
Manage git sessions by setting up git identity, reviewing pending changes, committing work, and pushing to GitHub. Perfect for starting/ending development sessions.

## When to Use
- At the **start** of a new session (to commit previous session's work)
- At the **end** of a session (to save current work)
- When you have pending changes and want to save them
- When switching between different tasks or branches

---

## Usage

### Future Automation (Planned)
```bash
# In Claude Code CLI
/run git-session-manager
/run git-session-manager --mode commit-and-push
/run git-session-manager --mode setup-only
/run git-session-manager --mode review-only
```

### Current Usage (Manual)
Ask Claude: "Help me commit my session work" or "Save my git session"

---

## What This Agent Does

### 1. Verify Git Configuration
**Checks**:
- Git user name is configured
- Git user email is configured
- Repository is connected to remote (GitHub)
- Current branch information

**Actions**:
- If not configured, prompts for user name and email
- Sets up git identity using GitHub's private no-reply email
- Recommends format: `username@users.noreply.github.com`

**Example**:
```bash
# Check current config
git config user.name
git config user.email
git remote -v

# Set up if missing
git config --global user.name "Your Name"
git config --global user.email "username@users.noreply.github.com"
```

---

### 2. Review Pending Changes
**Checks**:
- List all modified files
- List all untracked (new) files
- Show summary statistics of changes
- Display recent commit history for context

**Actions**:
```bash
# View status
git status

# See change summary
git diff --stat

# View recent commits
git log -3 --oneline
```

**Output Example**:
```
Modified files:
- README.md (282 additions)
- backend/server.py (335 changes)

New files:
- docker-compose.yml
- DEPLOYMENT.md
- startup scripts (.sh, .bat)

Total: 29 files changed
```

---

### 3. Generate Descriptive Commit Message
**Analyzes**:
- Types of changes (features, fixes, docs, config)
- Scope of changes (which parts of codebase)
- Purpose of changes (what problem solved)

**Creates**:
- Clear, descriptive commit message
- Multi-line format with summary and details
- Follows conventional commit style
- Includes co-author attribution

**Example Commit Message**:
```
Add deployment infrastructure and documentation

- Add Docker configuration for frontend and backend services
- Create docker-compose.yml for local development
- Add deployment guides (DEPLOYMENT.md, DEPLOY-QUICK-START.md)
- Add platform deployment configs (Render, Vercel)
- Create cross-platform startup scripts (.bat and .sh)
- Update README with deployment instructions
- Refactor backend server.py for better organization

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

### 4. Stage and Commit Changes
**Actions**:
```bash
# Stage all changes
git add .

# Commit with message
git commit -m "$(cat <<'EOF'
[Descriptive commit message here]

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"

# Verify commit
git status
```

**Handles**:
- Line ending warnings (LF/CRLF) - normal on Windows
- Empty commits (skips if nothing to commit)
- Commit verification

---

### 5. Push to GitHub
**Actions**:
```bash
# Push to remote
git push

# Verify push
git status
```

**Output**:
```
To https://github.com/username/repo-name
   abc1234..def5678  main -> main
```

**Notes**:
- Only pushes after successful local commit
- Verifies remote connection first
- Reports push status clearly

---

## Step-by-Step Workflow

### Starting a New Session (Commit Yesterday's Work)

1. **Check Git Config**
   - Verify identity is set up
   - If not, prompt user for name/email
   - Set up using private email format

2. **Review Pending Changes**
   - Run `git status` to see all changes
   - Run `git diff --stat` to see change summary
   - Show recent commits for context

3. **Explain What's Pending**
   - Count total files changed
   - Categorize changes (modified vs new)
   - Summarize what the changes represent

4. **Commit Changes**
   - Stage all changes with `git add .`
   - Create descriptive commit message
   - Commit locally

5. **Push to GitHub**
   - Push to remote repository
   - Confirm successful backup

6. **Confirm Success**
   - Report commit hash
   - Report push status
   - Confirm working tree is clean

---

## Configuration Options

### Git Identity Setup

**Recommended**: Use GitHub's private no-reply email
```
Name: Your Name
Email: your-github-username@users.noreply.github.com
```

**Benefits**:
- Keeps personal email private
- Still links to your GitHub profile
- No spam or unwanted contact
- Standard privacy practice

**Alternative**: Use your actual email
```
Name: Your Name
Email: your.email@example.com
```

---

## Troubleshooting

### Issue 1: Git Identity Not Set
**Error**:
```
Author identity unknown
```

**Solution**:
```bash
git config --global user.name "Your Name"
git config --global user.email "username@users.noreply.github.com"
```

---

### Issue 2: No Remote Configured
**Error**:
```
fatal: No configured push destination
```

**Solution**:
```bash
# Add remote
git remote add origin https://github.com/username/repo-name.git

# Verify
git remote -v
```

---

### Issue 3: Authentication Failed
**Error**:
```
fatal: Authentication failed
```

**Solution**:
- Use Personal Access Token (PAT) instead of password
- Generate PAT at: https://github.com/settings/tokens
- Use PAT as password when prompted

---

### Issue 4: Diverged Branches
**Error**:
```
Your branch and 'origin/main' have diverged
```

**Solution**:
```bash
# Pull remote changes first
git pull --rebase

# Then push
git push
```

---

## Understanding Git Concepts

### What Are "Pending Changes"?
Files you've modified, created, or deleted but haven't saved to git history yet.

**Think of it like**:
- **Working files** = Your current files (what you see)
- **Pending changes** = Differences from last saved snapshot
- **Git history** = All your saved snapshots over time

---

### What Happens When You Commit?
A commit creates a permanent snapshot of your work with a description.

**Before commit**: Changes only exist on your computer, can be easily lost

**After commit**: Changes are saved in git history with a message describing what you did

**After push**: Changes are uploaded to GitHub as a backup

---

### Commit vs Push

**Commit** = Save snapshot **locally** on your computer
- Creates a checkpoint in git history
- Can be undone if needed
- Not visible on GitHub yet

**Push** = Upload commits to **GitHub** (remote server)
- Backs up your work online
- Makes it visible to others
- Syncs your local changes to remote

**Important**: Committing does NOT upload to GitHub automatically!

---

## Example Session

### User: "I have 29 pending changes from yesterday. Help me commit them."

**Agent Actions**:

1. **Check git config**:
   ```bash
   git config user.name
   git config user.email
   git remote -v
   ```

2. **If config missing, prompt**:
   - "What name would you like to use?"
   - Recommend: Use GitHub username or full name
   - "What email should be used?"
   - Recommend: Use `username@users.noreply.github.com`

3. **Set up config**:
   ```bash
   git config --global user.name "Naveen Kumar"
   git config --global user.email "naveenkumar29nl@users.noreply.github.com"
   ```

4. **Review changes**:
   ```bash
   git status
   git diff --stat
   git log -3 --oneline
   ```

5. **Explain what's pending**:
   ```
   Modified files:
   - README.md - Major updates (282 additions)
   - backend/server.py - Refactored code
   - frontend/public/index.html - Simplified

   New files:
   - Deployment documentation
   - Docker configuration
   - Startup scripts

   Total: 29 files
   ```

6. **Commit all changes**:
   ```bash
   git add .
   git commit -m "..."
   ```

7. **Push to GitHub**:
   ```bash
   git push
   ```

8. **Confirm success**:
   ```
   ✅ Committed 29 files
   ✅ Pushed to GitHub
   ✅ Working tree is clean
   ✅ Your work is backed up at: https://github.com/username/repo
   ```

---

## Success Criteria

After running this agent, verify:
- [x] Git identity is configured
- [x] All changes are committed
- [x] Commit has descriptive message
- [x] Changes are pushed to GitHub
- [x] Working tree is clean (no pending changes)
- [x] Repository status shows "up to date with origin/main"

---

## Tips for Good Commits

### 1. Commit Related Changes Together
Group related work in the same commit. Don't mix unrelated changes.

**Good**:
```
Commit 1: "Add user authentication"
Commit 2: "Fix database connection bug"
```

**Bad**:
```
Commit 1: "Add user auth, fix database bug, update README, add Docker"
```

---

### 2. Write Clear Commit Messages
Explain **what** changed and **why**, not **how**.

**Good**:
```
Fix login error when password contains special characters

- Escape special characters in password validation
- Add test cases for special character passwords
```

**Bad**:
```
Fixed stuff
Update code
Changes
```

---

### 3. Commit Often
Don't wait until end of day. Commit after completing each logical unit of work.

**Good practice**:
- Commit after completing a feature
- Commit after fixing a bug
- Commit before switching tasks

**Bad practice**:
- Commit once per day with 100 file changes
- Commit with message "end of day work"

---

### 4. Don't Commit Secrets
Never commit passwords, API keys, or sensitive data.

**Check before committing**:
- .env files (should be in .gitignore)
- API keys or tokens
- Database passwords
- Private keys

**If you accidentally commit secrets**:
1. Change the secret immediately
2. Remove from git history (use `git filter-branch`)
3. Force push updated history

---

## Integration with Other Agents

### Works Well With:

**1. End Session Summary Agent**
- Use git-session-manager FIRST to commit changes
- Then use end-session-summary to document what was done

**2. Security Compliance Agent**
- Git-session-manager checks for secrets before committing
- Warns if sensitive files detected
- Integrates with security scanning

**3. Test Agent** (Future)
- Runs tests before allowing commit
- Prevents committing broken code
- Ensures quality gates

---

## Future Enhancements

### Planned Features:
1. **Automated testing before commit**
   - Run tests automatically
   - Block commit if tests fail

2. **Branch management**
   - Create feature branches automatically
   - Merge branches after review

3. **Pre-commit hooks**
   - Run linters automatically
   - Format code before commit
   - Scan for secrets

4. **Interactive commit**
   - Choose which files to commit
   - Split large changes into multiple commits
   - Review each change before committing

5. **Commit message templates**
   - Choose from predefined templates
   - Follow conventional commits standard
   - Auto-generate based on changes

---

## CLI Commands Reference

### Check Status
```bash
git status                    # See all changes
git diff --stat              # Summary of changes
git log --oneline -5         # Recent commits
```

### Configure Git
```bash
git config --global user.name "Your Name"
git config --global user.email "email@example.com"
git config --list            # View all config
```

### Stage Changes
```bash
git add .                    # Stage all changes
git add file.txt             # Stage specific file
git add *.py                 # Stage all Python files
```

### Commit
```bash
git commit -m "message"      # Simple commit
git commit                   # Opens editor for message
git commit --amend           # Modify last commit
```

### Push
```bash
git push                     # Push to remote
git push origin main         # Push specific branch
git push -f                  # Force push (DANGEROUS!)
```

### Undo Changes
```bash
git restore file.txt         # Discard local changes
git restore --staged file.txt # Unstage file
git reset HEAD~1             # Undo last commit (keep changes)
git reset --hard HEAD~1      # Undo last commit (lose changes)
```

---

## Quick Start Commands

### Save Your Session Work
```bash
# Ask Claude
"Help me commit my pending changes and push to GitHub"
"Save my session work"
"I want to commit yesterday's work"
```

### Start Fresh Session
```bash
# Commit old work, start clean
"Start a new session and save my previous session"
"Commit yesterday's work so I can start fresh"
```

---

## Common Scenarios

### Scenario 1: First Time Setup
**User**: "This is my first time using git"

**Agent does**:
1. Explain git basics
2. Set up git identity
3. Verify remote connection
4. Walk through first commit

---

### Scenario 2: End of Day
**User**: "I'm done for today, save everything"

**Agent does**:
1. Review all changes
2. Commit with descriptive message
3. Push to GitHub
4. Confirm backup successful

---

### Scenario 3: Multiple Sessions
**User**: "I have work from yesterday and today. Save separately"

**Agent suggests**:
1. Commit yesterday's work first
2. Create descriptive commit for that session
3. Keep today's work as pending
4. Or commit today's work separately

---

### Scenario 4: Forgot to Commit Yesterday
**User**: "I forgot to commit yesterday, now have 2 days of work"

**Agent does**:
1. Review all changes
2. Group by session if possible
3. Create comprehensive commit message
4. Recommend committing more frequently

---

## Best Practices

1. **Commit at end of each session** - Don't accumulate days of changes
2. **Use descriptive messages** - Help future you understand what was done
3. **Push regularly** - Don't rely on local-only commits
4. **Keep git identity consistent** - Use same email across projects
5. **Review before committing** - Check what you're committing
6. **Never commit secrets** - Use .gitignore and environment variables

---

## File Locations

**Agent Documentation**:
- `.claude/agents/git-session-manager.md` - This file

**Git Configuration**:
- `~/.gitconfig` - Global git config
- `.git/config` - Repository git config

**Related Files**:
- `.gitignore` - Files to never commit
- `.claude/sessions/` - Session documentation

---

## Related Documentation

- [End Session Summary Agent](.claude/agents/end-session-summary.md)
- [Security Compliance Agent](.claude/agents/security-compliance.md)
- [Agent Commands Reference](.claude/AGENT-COMMANDS-REFERENCE.md)

---

**Last Updated**: 2026-01-08
**Version**: 1.0
**Status**: ✅ Ready to use
