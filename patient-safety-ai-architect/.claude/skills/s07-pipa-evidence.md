---
name: pipa-evidence
description: Generate PIPA compliance evidence package for Korean healthcare QI system
user-invocable: true
---

# S7. PIPA Evidence Package

## Category
DESCRIBE — Produce auditable compliance evidence

## Owner
- **Compliance_Expert_KR (R/A)**: Create and approve evidence
- **Security_Analyst (C)**: Technical implementation review

---

## Goal
Create auditable proof that incident reporting data is handled in compliance with Korea's Personal Information Protection Act (개인정보보호법).

---

## PIPA Key Requirements (Healthcare Context)

| Article | Requirement | Evidence Needed |
|---------|-------------|-----------------|
| Art. 15 | Consent for collection | Consent form / legal basis |
| Art. 17 | Third-party disclosure limits | Disclosure policy |
| Art. 20 | Access rights | Access request procedure |
| Art. 21 | Retention limits | Retention schedule |
| Art. 23 | Sensitive info (health data) | Additional safeguards |
| Art. 29 | Security measures | Technical controls |
| Art. 30 | Privacy policy | Published policy |

---

## Steps

### 1. Identify Personal Information

**In Patient Safety Incident System:**
| Data Field | PI Type | Sensitivity | Retention |
|------------|---------|-------------|-----------|
| reporter_name | Identifier | Normal | Incident + 3 years |
| patient_info | Health-related | Sensitive (Art. 23) | Medical record retention |
| location | Context | Normal | Incident lifecycle |
| incident_description | May contain PI | Mixed | Review before archive |

### 2. Document Legal Basis

```markdown
## Legal Basis for Processing

### Collection (Art. 15)
- **Basis**: Legal obligation (의료법 시행규칙 제42조 - 환자안전사고 보고)
- **Purpose**: Quality improvement, patient safety, regulatory compliance

### Sensitive Data (Art. 23)
- **Type**: Health information (incident details)
- **Additional Safeguard**: Role-based access, audit logging, encryption
```

### 3. Create Evidence Documents

---

## Output

### Required Files (for Release Gate)
- `docs/pipa-checklist.md`
- `docs/pipa-retention-disposal.md`
- `docs/pipa-access-control.md`
- `docs/pipa-audit-logging.md`

---

## Document Templates

### docs/pipa-checklist.md

```markdown
# PIPA Compliance Checklist

**System**: Patient Safety Incident Reporting (환자안전사고보고시스템)
**Version**: {version}
**Last Updated**: YYYY-MM-DD
**Reviewer**: {name}

## 1. Collection (수집)
- [ ] Legal basis documented
- [ ] Minimum necessary data only
- [ ] Purpose clearly defined
- [ ] Consent mechanism (if required)

## 2. Use & Processing (이용)
- [ ] Used only for stated purpose
- [ ] No unauthorized secondary use
- [ ] Processing records maintained

## 3. Third-Party Provision (제3자 제공)
- [ ] No external sharing without consent/legal basis
- [ ] Data sharing agreements (if applicable)
- [ ] Transfer records maintained

## 4. Storage & Retention (보관)
- [ ] Retention periods defined
- [ ] Secure storage (encryption at rest)
- [ ] Access controls implemented

## 5. Disposal (파기)
- [ ] Disposal procedures documented
- [ ] Secure deletion methods
- [ ] Disposal records maintained

## 6. Security Measures (안전조치)
- [ ] Access control (RBAC)
- [ ] Audit logging
- [ ] Encryption (at rest & in transit)
- [ ] Backup procedures

## 7. Data Subject Rights (정보주체 권리)
- [ ] Access request procedure
- [ ] Correction request procedure
- [ ] Deletion request procedure
- [ ] Processing suspension procedure

## Approval
- [ ] Compliance_Expert_KR reviewed
- [ ] DPO approved (if required)
```

### docs/pipa-retention-disposal.md

```markdown
# Retention & Disposal Policy

## Retention Schedule
| Data Category | Retention Period | Legal Basis | Disposal Method |
|---------------|------------------|-------------|-----------------|
| Incident records | 3 years after closure | 의료법 | Secure delete |
| Attachments | Same as incident | 의료법 | Secure delete |
| Audit logs | 5 years | PIPA Art. 29 | Archive then delete |
| Reporter info | Incident lifecycle | PIPA Art. 21 | Pseudonymize |

## Disposal Procedures
1. Identify data past retention period
2. Verify no legal hold
3. Execute secure deletion
4. Record disposal in audit log
5. Generate disposal certificate

## Disposal Methods
| Data Type | Method |
|-----------|--------|
| Database records | Cryptographic erasure |
| Files | Secure overwrite (3-pass) |
| Backups | Encrypted backup rotation |
```

### docs/pipa-access-control.md

```markdown
# Access Control Policy

## Roles & Permissions
| Role | View | Create | Edit | Delete | Export | Approve |
|------|------|--------|------|--------|--------|---------|
| Reporter | Own | Yes | Own | No | No | No |
| QPS Staff | Dept | Yes | Dept | No | Dept | L1 |
| Vice Chair | All | Yes | All | No | All | L2 |
| Director | All | Yes | All | Archive | All | L3 |
| Admin | Config | No | Config | No | Audit | No |

## Access Request Procedure
1. Submit access request form
2. Manager approval
3. IT provisioning
4. Quarterly access review

## Evidence
- Access control matrix implemented in `backend/app/security/rbac.py`
- Test cases in `backend/tests/test_access_control.py`
```

### docs/pipa-audit-logging.md

```markdown
# Audit Logging Policy

## Logged Events
| Event | Data Captured | Retention |
|-------|---------------|-----------|
| Login | user_id, timestamp, IP, result | 5 years |
| View incident | user_id, incident_id, timestamp | 5 years |
| Edit incident | user_id, incident_id, field, old/new | 5 years |
| Export | user_id, query, count, timestamp | 5 years |
| Attachment download | user_id, file_id, timestamp | 5 years |

## Log Protection
- Append-only storage
- Tamper detection (hash chain)
- Separate access control from main data

## Evidence
- Audit schema in `backend/app/models/audit.py`
- Implementation in `backend/app/security/audit.py`
```

---

## Escalation

If ANY of these apply, escalate to DPO/Legal:
- Uncertainty about retention period
- Third-party data sharing request
- Data breach incident
- Cross-border transfer
- Regulatory inquiry

---

## Related Skills
- S10. Access Control (`/access-control`) — RBAC implementation
- S11. Audit Logging (`/audit-logging`) — Technical logging
- S15. Release Gate (`/release-gate`) — Evidence required for pass
