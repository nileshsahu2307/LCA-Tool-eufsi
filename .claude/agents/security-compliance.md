# Security & Compliance Agent

## Purpose
Identify and fix security vulnerabilities and ensure compliance with industry standards before deploying to production or licensing to customers.

## Priority: P0 (Critical for Production)

---

## When to Use
- Before every production deployment
- Weekly security audits
- Before licensing to new customers
- After adding new dependencies
- After major code changes

---

## Usage
```bash
# In Claude Code CLI
/run security-compliance

# With specific mode
/run security-compliance --level strict
/run security-compliance --report-only
```

---

## Security Checks Performed

### 1. Dependency Vulnerabilities
**Tools**: npm audit, safety (Python)

**Checks**:
- Scan all npm packages for known vulnerabilities
- Scan all Python packages for known vulnerabilities
- Check for outdated dependencies with security patches
- Identify packages with high/critical CVEs

**Actions**:
- Generate vulnerability report
- Suggest safe upgrade paths
- Flag critical issues requiring immediate attention

---

### 2. Secrets & Credentials
**What to Check**:
- Hardcoded API keys
- Hardcoded passwords
- Hardcoded JWT secrets
- Database connection strings with credentials
- AWS/Cloud credentials
- Private keys committed to git

**Current Issues Found**:
```python
# backend/.env (and docker-compose.yml)
JWT_SECRET_KEY=eufsi-lca-secret-key-change-in-production  # ⚠️ MUST CHANGE!
```

**Required Actions**:
1. Generate strong random JWT secret (use: `openssl rand -hex 32`)
2. Move to environment variables (never commit to git)
3. Use different secrets for dev/staging/production
4. Rotate secrets regularly

---

### 3. Input Validation
**What to Check**:
- API endpoints accept user input
- Form inputs from frontend
- File uploads
- Query parameters

**Required Checks**:
- Validate all input types
- Sanitize user inputs
- Check for SQL/NoSQL injection
- Validate file types and sizes
- Check for XSS vulnerabilities

**Current Status**: ⚠️ Limited validation in place

**Required Actions**:
```python
# Example fixes needed in backend/server.py

from pydantic import validator, Field

class LCAProject(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

    @validator('name')
    def validate_name(cls, v):
        # Sanitize input
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
            raise ValueError('Invalid project name')
        return v.strip()

# Add input validation to all endpoints
@app.post("/api/projects")
async def create_project(project: LCAProject):  # Uses Pydantic validation
    # ...
```

---

### 4. Authentication & Authorization
**What to Check**:
- Password hashing strength (bcrypt settings)
- JWT token expiration
- Session management
- Password complexity requirements
- Account lockout policies
- API endpoint protection

**Current Issues**:
```python
# backend/server.py - Line ~70
# Check bcrypt work factor
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Should specify rounds: bcrypt__default_rounds=12
```

**Required Actions**:
1. Set bcrypt rounds to 12+ for password hashing
2. Add JWT token expiration (currently missing?)
3. Add rate limiting on login endpoint
4. Implement password complexity rules
5. Add account lockout after failed attempts

---

### 5. API Security
**What to Check**:
- Rate limiting
- CORS configuration
- API versioning
- Request size limits
- Timeout settings

**Current Issues**:
```python
# backend/server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ TOO PERMISSIVE!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Required Actions**:
```python
# Fix CORS
origins = os.getenv("CORS_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Specific methods
    allow_headers=["*"],
)

# Add rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/auth/login")
@limiter.limit("5/minute")  # Max 5 login attempts per minute
async def login(request: Request, user: UserLogin):
    # ...
```

---

### 6. Data Protection
**What to Check**:
- Sensitive data in logs
- Database encryption at rest
- HTTPS enforcement
- Secure cookie settings
- Data backup encryption

**Current Issues**:
- Running on HTTP in development (OK for dev, not prod)
- No encryption at rest configured
- Logs may contain sensitive data

**Required Actions for Production**:
1. **HTTPS Only**:
```python
# Force HTTPS in production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["your-domain.com"]
    )
```

2. **Secure Cookies**:
```python
# JWT cookie settings
response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,  # Prevent XSS
    secure=True,    # HTTPS only
    samesite="strict"  # CSRF protection
)
```

3. **MongoDB Encryption**:
```yaml
# docker-compose.yml production
mongodb:
  command: mongod --setParameter enableEncryption=true
```

---

### 7. Error Handling
**What to Check**:
- Verbose error messages exposing internals
- Stack traces visible to users
- Database errors exposing schema

**Current Issues**:
```python
# backend/server.py
# Some endpoints return full error details
except Exception as e:
    return {"error": str(e)}  # ⚠️ May expose internals!
```

**Required Actions**:
```python
# Safe error handling
except ValueError as e:
    # User-facing error
    raise HTTPException(status_code=400, detail="Invalid input")
except Exception as e:
    # Log full error for debugging
    logger.error(f"Internal error: {e}", exc_info=True)
    # Return generic message to user
    raise HTTPException(
        status_code=500,
        detail="An error occurred. Please contact support."
    )
```

---

### 8. File Upload Security
**What to Check** (if file uploads are added):
- File type validation
- File size limits
- Virus scanning
- Safe file storage

**Not applicable yet**, but important for future features.

---

### 9. MongoDB Security
**What to Check**:
- NoSQL injection prevention
- Database access controls
- Connection encryption
- Query parameter validation

**Current Status**: Basic protection via Motor/PyMongo

**Required Actions**:
```python
# Prevent NoSQL injection
from bson.objectid import ObjectId

# BAD:
db.projects.find({"_id": user_input})  # ⚠️ Injection risk

# GOOD:
try:
    project_id = ObjectId(user_input)
    db.projects.find({"_id": project_id})
except:
    raise HTTPException(status_code=400, detail="Invalid ID")
```

---

### 10. Compliance Checks

#### GDPR (If serving EU customers)
- [ ] Privacy policy in place
- [ ] Cookie consent banner
- [ ] User data export capability
- [ ] Right to deletion implemented
- [ ] Data retention policies
- [ ] Data processing agreements

#### OWASP Top 10 (2021)
- [ ] A01: Broken Access Control
- [ ] A02: Cryptographic Failures
- [ ] A03: Injection
- [ ] A04: Insecure Design
- [ ] A05: Security Misconfiguration
- [ ] A06: Vulnerable Components
- [ ] A07: Identification/Authentication Failures
- [ ] A08: Software/Data Integrity Failures
- [ ] A09: Security Logging Failures
- [ ] A10: Server-Side Request Forgery

---

## Security Checklist

### Before First Production Deployment

#### Critical (P0) - Must Fix
- [ ] Change JWT_SECRET_KEY to random value
- [ ] Move all secrets to environment variables
- [ ] Add .env to .gitignore (verify not committed)
- [ ] Configure specific CORS origins (no wildcards)
- [ ] Add rate limiting to auth endpoints
- [ ] Set up HTTPS/SSL
- [ ] Add input validation to all endpoints
- [ ] Implement proper error handling (no stack traces)
- [ ] Set bcrypt work factor to 12+
- [ ] Add JWT expiration time

#### High Priority (P1) - Should Fix
- [ ] Run npm audit and fix vulnerabilities
- [ ] Run Python safety check and fix vulnerabilities
- [ ] Add request size limits
- [ ] Add timeout configurations
- [ ] Implement account lockout policy
- [ ] Add security headers (CSP, X-Frame-Options, etc.)
- [ ] Enable MongoDB authentication
- [ ] Set up database backups
- [ ] Configure logging without sensitive data
- [ ] Add API versioning

#### Medium Priority (P2) - Nice to Have
- [ ] Implement 2FA for admin users
- [ ] Add security audit logging
- [ ] Set up intrusion detection
- [ ] Implement WAF (Web Application Firewall)
- [ ] Add CAPTCHA to forms
- [ ] Implement CSRF tokens
- [ ] Add content security policy
- [ ] Set up automated security scanning

---

## Security Report Format

```markdown
# Security Audit Report
**Date**: YYYY-MM-DD
**Agent Version**: 1.0
**Audit Level**: Standard/Strict

## Summary
- **Critical Issues**: X
- **High Priority**: Y
- **Medium Priority**: Z
- **Low Priority**: W

## Critical Issues (Must Fix Immediately)

### Issue 1: Hardcoded JWT Secret
**Severity**: Critical
**Location**: `docker-compose.yml:36`, `backend/.env:3`
**Description**: JWT secret is hardcoded and publicly visible
**Impact**: Attackers can forge authentication tokens
**Fix**:
```bash
# Generate new secret
openssl rand -hex 32

# Set in environment (not in code)
export JWT_SECRET_KEY=<generated-secret>
```
**Effort**: 5 minutes
**Status**: ⚠️ Open

---

## Vulnerability Scan Results

### NPM Audit
```
found 3 vulnerabilities (1 moderate, 2 high)
```

**Details**:
1. Package: `xyz`
   - Severity: High
   - Fix: Update to version X.Y.Z

---

## Compliance Status

### GDPR Compliance: ⚠️ Not Compliant
Missing:
- Privacy policy
- Cookie consent
- Data export feature

### OWASP Top 10: ⚠️ 40% Compliant
Passing: 4/10
Failing: 6/10

---

## Recommendations

1. **Immediate**:
   - Fix critical issues listed above
   - Run dependency updates

2. **Short Term** (This Week):
   - Implement rate limiting
   - Add input validation
   - Configure HTTPS

3. **Medium Term** (This Month):
   - Complete OWASP compliance
   - Set up security monitoring
   - Implement automated scans

---

## Next Audit
Recommended: 1 week from today
```

---

## Tools Used

1. **npm audit** - JavaScript dependency scanning
2. **safety** - Python dependency scanning
3. **bandit** - Python security linter
4. **eslint-plugin-security** - JavaScript security linting
5. **git-secrets** - Prevent committing secrets
6. **OWASP ZAP** - Web application security scanner

---

## Implementation

To implement this agent:

1. **Install Security Tools**:
```bash
# Python
pip install safety bandit

# Node.js
npm install -g npm-audit-html
npm install --save-dev eslint-plugin-security
```

2. **Create Security Scripts**:
```bash
# backend/security-scan.sh
safety check --json
bandit -r . -f json

# frontend/security-scan.sh
npm audit --json
```

3. **Run Agent**:
The agent will execute all checks and generate report.

---

## Quick Fixes for EUFSI LCA Tool

### 1. Fix JWT Secret (2 minutes)
```bash
# Generate new secret
NEW_SECRET=$(openssl rand -hex 32)

# Update .env file
echo "JWT_SECRET_KEY=$NEW_SECRET" >> backend/.env

# Update docker-compose.yml
# Replace JWT_SECRET_KEY value with $NEW_SECRET
```

### 2. Fix CORS (1 minute)
```python
# backend/server.py
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Changed from ["*"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 3. Add Rate Limiting (5 minutes)
```bash
# Install slowapi
pip install slowapi

# Add to requirements.txt
echo "slowapi==0.1.9" >> backend/requirements.txt
```

```python
# backend/server.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: UserLogin):
    # existing code
```

---

## Success Criteria

After implementing security fixes, verify:
- [ ] No hardcoded secrets in codebase
- [ ] All dependencies have no known vulnerabilities
- [ ] CORS configured for specific domains
- [ ] Rate limiting active on auth endpoints
- [ ] Input validation on all API endpoints
- [ ] HTTPS configured (production)
- [ ] Error messages don't expose internals
- [ ] Security headers configured

---

**Remember**: Security is not a one-time task. Run this agent regularly and after every significant change.
