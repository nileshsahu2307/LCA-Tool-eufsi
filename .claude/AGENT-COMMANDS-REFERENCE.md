# 📋 Agent Commands Reference

Quick reference for all agents and how to use them.

---

## ✅ Agents Already Created

### 1. End Session Summary Agent
**File**: `.claude/agents/end-session-summary.md`

**Purpose**: Document what was accomplished in each session

**When to Use**: At the end of every development session

**Command** (future automation):
```bash
/run end-session-summary
```

**How to Use Now** (Manual):
1. Copy template from `.claude/sessions/session-2026-01-08-docker-fixes.md`
2. Fill in your session details
3. Save to `.claude/sessions/session-YYYY-MM-DD-description.md`

---

### 2. Security & Compliance Agent ⚠️ CRITICAL
**File**: `.claude/agents/security-compliance.md`

**Purpose**: Find and fix security vulnerabilities

**When to Use**:
- **Tomorrow** (Critical!)
- Before every deployment
- Weekly audits
- Before licensing to customers

**Command** (future automation):
```bash
/run security-compliance
/run security-compliance --level strict
/run security-compliance --report-only
```

**How to Use Now** (Manual):
```bash
# 1. Read the guide
code .claude/agents/security-compliance.md

# 2. Generate JWT secret
openssl rand -hex 32

# 3. Update backend/.env with new secret
# Replace: JWT_SECRET_KEY=eufsi-lca-secret-key-change-in-production
# With: JWT_SECRET_KEY=<your-generated-secret>

# 4. Rebuild Docker
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d

# 5. Run security checks (from agent guide)
cd backend
pip install safety bandit
safety check
bandit -r . -ll

cd ../frontend
npm audit
```

---

### 3. Git Session Manager Agent
**File**: `.claude/agents/git-session-manager.md`

**Purpose**: Manage git sessions - commit work, push to GitHub, set up git identity

**When to Use**:
- At the **start** of a new session (to commit previous work)
- At the **end** of a session (to save current work)
- When you have pending changes to commit
- First time setting up git

**Command** (future automation):
```bash
/run git-session-manager
/run git-session-manager --mode commit-and-push
/run git-session-manager --mode setup-only
```

**How to Use Now** (Manual):
Ask Claude:
- "Help me commit my pending changes"
- "Save my session work"
- "Set up my git identity and commit yesterday's work"

**What It Does**:
1. Checks/sets up git identity (name, email)
2. Reviews all pending changes
3. Creates descriptive commit message
4. Commits changes locally
5. Pushes to GitHub
6. Confirms successful backup

**Example**:
```
User: "I have 29 pending changes. Help me commit them."

Agent:
1. Sets up git identity if needed
2. Reviews changes (modified + new files)
3. Creates commit: "Add deployment infrastructure and documentation"
4. Pushes to GitHub
5. Confirms: "✅ 29 files committed and pushed"
```

---

## 🔲 Agents to Create Next

### 4. Test Agent
**File to Create**: `.claude/agents/test-runner.md`

**Purpose**: Run all tests and check coverage

**When to Use**:
- Before every commit
- Before deployment
- After major changes

**Command** (future automation):
```bash
/run test-runner
/run test-runner --coverage
/run test-runner --verbose
```

**How to Use** (Manual - after creating):
```bash
# Backend tests
cd backend
pytest
pytest --cov=. --cov-report=html

# Frontend tests
cd frontend
npm test
npm test -- --coverage
```

---

### 4. Code Quality Agent
**File to Create**: `.claude/agents/code-quality.md`

**Purpose**: Check code follows best practices, run linters

**When to Use**:
- Before every commit
- Weekly code review
- Before releases

**Command** (future automation):
```bash
/run code-quality
/run code-quality --fix
```

**How to Use** (Manual - after creating):
```bash
# Backend
cd backend
pylint *.py
black --check .
mypy .

# Frontend
cd frontend
npm run lint
npm run format:check
```

---

### 5. Documentation Agent
**File to Create**: `.claude/agents/documentation.md`

**Purpose**: Ensure all code is documented

**When to Use**:
- Monthly
- Before releases
- Before customer demos

**Command** (future automation):
```bash
/run documentation
/run documentation --generate
```

**How to Use** (Manual - after creating):
```bash
# Check documentation coverage
# Generate API docs
# Update README
```

---

### 6. Performance Optimization Agent
**File to Create**: `.claude/agents/performance-optimizer.md`

**Purpose**: Profile and optimize app performance

**When to Use**:
- Monthly
- When performance issues reported
- Before scaling

**Command** (future automation):
```bash
/run performance-optimizer
/run performance-optimizer --profile
```

**How to Use** (Manual - after creating):
```bash
# Backend profiling
python -m cProfile server.py

# Frontend profiling
npm run build -- --profile
```

---

### 7. Database Agent
**File to Create**: `.claude/agents/database-optimizer.md`

**Purpose**: Optimize MongoDB queries and indexes

**When to Use**:
- Monthly
- When database slow
- Before scaling

**Command** (future automation):
```bash
/run database-optimizer
/run database-optimizer --analyze
```

**How to Use** (Manual - after creating):
```bash
# Check MongoDB performance
docker-compose exec mongodb mongosh
# Then run: db.projects.stats()
# Check indexes: db.projects.getIndexes()
```

---

### 8. Deployment Agent
**File to Create**: `.claude/agents/deployment.md`

**Purpose**: Deploy safely with pre-deployment checklist

**When to Use**:
- Before every deployment
- Before releases

**Command** (future automation):
```bash
/run deployment
/run deployment --environment production
/run deployment --dry-run
```

**How to Use** (Manual - after creating):
```bash
# Follow deployment checklist
# Run pre-deployment tests
# Deploy to staging
# Deploy to production
```

---

### 9. Infrastructure Agent
**File to Create**: `.claude/agents/infrastructure.md`

**Purpose**: Optimize Docker, servers, resources

**When to Use**:
- Monthly
- When adding infrastructure
- Before scaling

**Command** (future automation):
```bash
/run infrastructure
/run infrastructure --optimize
```

**How to Use** (Manual - after creating):
```bash
# Check Docker resource usage
docker stats

# Optimize images
docker-compose build --no-cache

# Check disk usage
docker system df
```

---

### 10. Frontend UX Agent
**File to Create**: `.claude/agents/frontend-ux.md`

**Purpose**: Check accessibility, responsiveness, UX

**When to Use**:
- Bi-weekly
- Before releases
- After UI changes

**Command** (future automation):
```bash
/run frontend-ux
/run frontend-ux --accessibility
```

**How to Use** (Manual - after creating):
```bash
# Run accessibility audit
npm run lighthouse

# Check responsive design
# Test on different browsers
```

---

### 11. Backend API Agent
**File to Create**: `.claude/agents/backend-api.md`

**Purpose**: Validate API contracts, performance

**When to Use**:
- Weekly
- After API changes
- Before releases

**Command** (future automation):
```bash
/run backend-api
/run backend-api --validate
```

**How to Use** (Manual - after creating):
```bash
# Test API endpoints
pytest tests/api/

# Check API docs
curl http://localhost:8000/docs
```

---

### 12. Licensing Agent
**File to Create**: `.claude/agents/licensing.md`

**Purpose**: Prepare software for customer licensing

**When to Use**:
- Before first customer release
- Before major releases
- When adding dependencies

**Command** (future automation):
```bash
/run licensing
/run licensing --generate-bom
```

**How to Use** (Manual - after creating):
```bash
# Check license compliance
pip-licenses

# Generate software BOM
# Add license headers
```

---

### 13. Release Manager Agent
**File to Create**: `.claude/agents/release-manager.md`

**Purpose**: Create releases, changelogs, version tags

**When to Use**:
- For each release
- Creating changelog

**Command** (future automation):
```bash
/run release-manager --version 1.0.0
/run release-manager --changelog
/run release-manager --tag
```

**How to Use** (Manual - after creating):
```bash
# Create git tag
git tag -a v1.0.0 -m "Release 1.0.0"

# Generate changelog
# Create release notes
```

---

### 14. Error Monitor Agent
**File to Create**: `.claude/agents/error-monitor.md`

**Purpose**: Track and alert on application errors

**When to Use**:
- Runs continuously in background
- Check weekly

**Command** (future automation):
```bash
/run error-monitor --background
/run error-monitor --report
```

**How to Use** (Manual - after creating):
```bash
# Check logs
docker-compose logs backend | grep ERROR

# Monitor errors
tail -f logs/error.log
```

---

### 15. Dependency Update Agent
**File to Create**: `.claude/agents/dependency-updater.md`

**Purpose**: Keep packages up to date

**When to Use**:
- Weekly automated run
- Monthly review

**Command** (future automation):
```bash
/run dependency-updater
/run dependency-updater --check-only
/run dependency-updater --apply
```

**How to Use** (Manual - after creating):
```bash
# Backend
pip list --outdated

# Frontend
npm outdated

# Update dependencies
pip install --upgrade -r requirements.txt
npm update
```

---

## 📅 Recommended Schedule

### Daily
- None (develop as needed)

### Before Every Commit
```bash
/run test-runner
/run code-quality
```

### Weekly
```bash
/run security-compliance
/run backend-api
/run dependency-updater --check-only
```

### Bi-Weekly
```bash
/run frontend-ux
/run database-optimizer
```

### Monthly
```bash
/run performance-optimizer
/run infrastructure
/run documentation
```

### Before Deployment
```bash
/run security-compliance --level strict
/run test-runner --coverage
/run deployment --dry-run
/run deployment --environment production
```

### Before Release
```bash
/run security-compliance --level strict
/run test-runner --coverage
/run code-quality
/run documentation
/run licensing
/run release-manager --version X.Y.Z
```

---

## 🎯 Priority Order for Creation

**Week 1** (This Week):
1. ✅ End Session Summary (Created)
2. ✅ Security & Compliance (Created) **← USE TOMORROW!**
3. ✅ Git Session Manager (Created) **← USE ANYTIME!**
4. 🔲 Test Agent (Create next)

**Week 2**:
5. 🔲 Code Quality Agent
6. 🔲 Deployment Agent

**Week 3**:
7. 🔲 Performance Optimization Agent
8. 🔲 Database Agent

**Week 4**:
9. 🔲 Documentation Agent
10. 🔲 Infrastructure Agent

**Week 5-6**:
11. 🔲 Frontend UX Agent
12. 🔲 Backend API Agent

**Week 7-8**:
13. 🔲 Licensing Agent
14. 🔲 Release Manager Agent
15. 🔲 Error Monitor Agent
16. 🔲 Dependency Update Agent

---

## 🔧 General Commands

### Start App
```bash
cd "C:\My Projects\LCA-Tool-eufsi"
docker-compose up -d
```

### Stop App
```bash
docker-compose down
```

### Rebuild After Changes
```bash
docker-compose build --no-cache backend
docker-compose up -d
```

### View Logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Fresh Start (Deletes Data!)
```bash
docker-compose down -v
docker-compose up -d
```

---

## 📝 Quick Tips

1. **Agents are currently guides** - Read the markdown file and follow steps manually
2. **Future automation** - `/run` commands are placeholders for future automation
3. **Start with security** - Most critical agent to use first
4. **Follow the schedule** - Don't try to run all agents at once
5. **Document each session** - Use end-session-summary agent template

---

## 📂 File Locations

```
.claude/
├── AGENT-STRATEGY.md                    ← Master roadmap
├── AGENT-COMMANDS-REFERENCE.md          ← This file
├── NEXT-STEPS-SUMMARY.md                ← What's next
├── QUICK-START-TOMORROW.md              ← Tomorrow's plan
├── agents/
│   ├── end-session-summary.md           ✅ Created
│   ├── security-compliance.md           ✅ Created (USE TOMORROW!)
│   ├── git-session-manager.md           ✅ Created (USE ANYTIME!)
│   ├── test-runner.md                   🔲 Create next
│   ├── code-quality.md                  🔲 To create
│   ├── documentation.md                 🔲 To create
│   ├── performance-optimizer.md         🔲 To create
│   ├── database-optimizer.md            🔲 To create
│   ├── deployment.md                    🔲 To create
│   ├── infrastructure.md                🔲 To create
│   ├── frontend-ux.md                   🔲 To create
│   ├── backend-api.md                   🔲 To create
│   ├── licensing.md                     🔲 To create
│   ├── release-manager.md               🔲 To create
│   ├── error-monitor.md                 🔲 To create
│   └── dependency-updater.md            🔲 To create
└── sessions/
    └── session-2026-01-08-docker-fixes.md  ✅ Today's session
```

---

## ⚡ Tomorrow's First Task

**Read and follow**: `.claude/agents/security-compliance.md`

**Quick fix** (30 minutes):
```bash
# 1. Generate secret
openssl rand -hex 32

# 2. Update backend/.env
# Replace JWT_SECRET_KEY value

# 3. Rebuild
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d
```

---

**Last Updated**: 2026-01-08
**Next Update**: After creating Test Agent
