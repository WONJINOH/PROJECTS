---
name: cryptography
description: Verify encryption at-rest, in-transit, and password hashing implementation
user-invocable: true
---

# S12. Cryptography (Baseline)

## Category
DEFEND — Protect data through encryption

## Owner
- **Security_Analyst (R)**: Implement and verify crypto controls
- **Compliance_Expert_KR (C)**: Validate PIPA compliance

---

## Goal
Ensure proper encryption at-rest, in-transit, and secure password hashing for the patient safety incident system.

---

## Cryptography Requirements

### PIPA Art. 29 Requirements
| Requirement | Implementation |
|-------------|----------------|
| Encryption of personal information | AES-256 for data at rest |
| Secure transmission | TLS 1.2+ for data in transit |
| Password protection | bcrypt/Argon2 hashing |

### Healthcare-Specific (KISA Guidelines)
| Category | Minimum Standard |
|----------|------------------|
| Symmetric encryption | AES-128 or higher |
| Hash function | SHA-256 or higher |
| Key length (RSA) | 2048-bit or higher |
| TLS version | 1.2 or higher |

---

## Steps

### 1. Verify Encryption at Rest

**Database Encryption**
```python
# Check SQLAlchemy encrypted columns
# backend/app/models/incident.py

from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

class Incident(Base):
    # Sensitive fields should be encrypted
    patient_info = Column(
        EncryptedType(String, SECRET_KEY, AesEngine, 'pkcs5'),
        nullable=True
    )
```

**File Encryption (Attachments)**
```python
# backend/app/security/crypto.py
from cryptography.fernet import Fernet

class FileEncryption:
    def __init__(self, key: bytes):
        self.fernet = Fernet(key)

    def encrypt_file(self, plaintext: bytes) -> bytes:
        return self.fernet.encrypt(plaintext)

    def decrypt_file(self, ciphertext: bytes) -> bytes:
        return self.fernet.decrypt(ciphertext)
```

**Verification Commands**
```bash
# Check for unencrypted sensitive data in DB
# (should return empty if properly encrypted)
sqlite3 data.db "SELECT patient_info FROM incidents LIMIT 1"
# Should show encrypted blob, not plaintext
```

### 2. Verify Encryption in Transit

**TLS Configuration**
```python
# For development (uvicorn)
# uvicorn main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem

# For production (nginx)
# nginx.conf
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
ssl_prefer_server_ciphers on;
```

**Verification**
```bash
# Check TLS version and ciphers
openssl s_client -connect localhost:443 -tls1_2
nmap --script ssl-enum-ciphers -p 443 localhost
```

### 3. Verify Password Hashing

**Secure Hashing Implementation**
```python
# backend/app/security/password.py
from passlib.context import CryptContext

# Use bcrypt with appropriate cost factor
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Adjust based on performance needs
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

**Argon2 Alternative (Recommended)**
```python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)
```

**Verification**
```bash
# Check stored password format (should be bcrypt/argon2 hash)
# bcrypt: $2b$12$...
# argon2: $argon2id$v=19$...
```

### 4. Key Management

**Environment-Based Keys**
```python
# backend/app/config.py
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Never hardcode keys!
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    DATABASE_ENCRYPTION_KEY: str = os.getenv("DB_ENCRYPTION_KEY")
    FILE_ENCRYPTION_KEY: str = os.getenv("FILE_ENCRYPTION_KEY")

    class Config:
        env_file = ".env"
```

**Key Rotation Procedure**
```markdown
1. Generate new key
2. Re-encrypt data with new key (migration)
3. Update environment variables
4. Verify decryption works
5. Securely dispose of old key
```

### 5. Document Findings

---

## Output

### Files
- `outputs/crypto-review.md`
- `docs/crypto-policy.md`

### Review Template

```markdown
# Cryptography Review

**Date**: YYYY-MM-DD
**Reviewer**: {name}

## Encryption at Rest
| Data Type | Algorithm | Key Length | Status |
|-----------|-----------|------------|--------|
| Database (sensitive columns) | AES-256 | 256-bit | ✓ |
| Attachments | Fernet (AES-128) | 128-bit | ✓ |
| Backups | AES-256 | 256-bit | ✓ |

## Encryption in Transit
| Connection | Protocol | Ciphers | Status |
|------------|----------|---------|--------|
| Client ↔ API | TLS 1.3 | ECDHE+AESGCM | ✓ |
| API ↔ Database | TLS 1.2 | AES256-GCM | ✓ |

## Password Hashing
| Algorithm | Cost Factor | Status |
|-----------|-------------|--------|
| bcrypt | 12 rounds | ✓ |

## Key Management
- [ ] Keys stored in environment variables (not code)
- [ ] Keys not logged or exposed in errors
- [ ] Key rotation procedure documented
- [ ] Backup keys securely stored

## Issues Found
| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 1 | Weak TLS cipher enabled | Medium | Fixed |

## Verification Checklist
- [ ] No plaintext sensitive data in database
- [ ] TLS 1.2+ enforced
- [ ] Weak ciphers disabled
- [ ] Passwords use bcrypt/argon2
- [ ] No hardcoded secrets
- [ ] Key rotation procedure exists

## Recommendations
1.
2.
```

### Crypto Policy Template (docs/crypto-policy.md)

```markdown
# Cryptography Policy

## Approved Algorithms
| Purpose | Algorithm | Minimum Key Size |
|---------|-----------|------------------|
| Symmetric encryption | AES | 128-bit (256 preferred) |
| Asymmetric encryption | RSA | 2048-bit |
| Hashing | SHA-256/SHA-3 | N/A |
| Password hashing | bcrypt/Argon2 | Cost factor 12+ |
| TLS | 1.2+ | N/A |

## Prohibited
- MD5 for any security purpose
- SHA-1 for any security purpose
- DES, 3DES
- RC4
- TLS 1.0, 1.1
- SSL (any version)

## Key Management
- Keys generated using cryptographically secure RNG
- Keys stored in environment variables or secrets manager
- Keys rotated annually or upon compromise
- Old keys securely destroyed

## Implementation
- Use established libraries (cryptography, passlib)
- Never implement custom crypto
- All crypto usage reviewed by Security_Analyst
```

---

## Common Vulnerabilities to Check

| Vulnerability | Check |
|---------------|-------|
| Hardcoded secrets | `grep -r "password\|secret\|key" --include="*.py"` |
| Weak algorithms | Check for MD5, SHA1, DES usage |
| Missing encryption | Sensitive fields stored plaintext |
| Insecure random | Using `random` instead of `secrets` |
| TLS misconfiguration | Weak ciphers, old protocols |

---

## Related Skills
- S3. Secrets Scan (`/secrets-scan`) — Find hardcoded keys
- S7. PIPA Evidence (`/pipa-evidence`) — Crypto as safeguard
- S15. Release Gate (`/release-gate`) — Crypto verification required
