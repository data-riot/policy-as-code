# Security Threat Model - Policy as Code Platform

## Executive Summary

This document outlines the security threat model for the Policy as Code platform, following STRIDE methodology. The platform handles sensitive government decision logic with legal compliance requirements, making security paramount.

## System Overview

**Core Components:**
- Decision Function Registry (signed releases)
- Immutable Trace Ledger (PostgreSQL with chain hashing)
- Legal Reference Validation (Finlex/EUR-Lex IRIs)
- Explanation API (citizen-facing)
- Audit Service (independent verification)
- Agentic AI Layer (LLM integration)

**Trust Boundaries:**
- External callers → API Gateway
- API Gateway → Decision Engine
- Decision Engine → Trace Ledger
- Audit Service → Trace Ledger (read-only)
- Citizens → Explanation API

## STRIDE Threat Analysis

### 1. Spoofing (Identity)

**Threat:** Unauthorized actors masquerading as legitimate callers or system components.

**Attack Vectors:**
- Forged JWT tokens
- Certificate spoofing in mTLS
- API key theft/leakage
- Internal service impersonation

**Controls Implemented:**
- JWT with RS256 signatures from trusted issuer
- mTLS with certificate pinning
- API key rotation and revocation
- Service-to-service authentication tokens

**Controls Needed:**
- Certificate transparency monitoring
- JWT token blacklisting
- Caller identity verification in trace records
- Hardware security module (HSM) for key storage

### 2. Tampering (Data Integrity)

**Threat:** Unauthorized modification of decision functions, trace records, or legal references.

**Attack Vectors:**
- Code injection in decision functions
- Trace record manipulation
- Legal reference substitution
- Release signature forgery

**Controls Implemented:**
- Immutable trace ledger with SHA256 chain hashing
- Digital signatures on releases (owner + reviewer)
- Legal reference IRI validation
- Function code hashing and verification

**Controls Needed:**
- Tamper-evident logging with immediate alerts
- Code static analysis in CI/CD
- Legal reference freshness checks
- Hardware-backed key storage

### 3. Repudiation (Non-repudiation)

**Threat:** Denial of actions or inability to prove who performed specific operations.

**Attack Vectors:**
- Log deletion or modification
- Signature key compromise
- Timestamp manipulation
- Audit trail gaps

**Controls Implemented:**
- Immutable append-only ledger
- Cryptographic signatures on all releases
- UTC timestamps with clock skew protection
- Independent audit service

**Controls Needed:**
- Digital signatures on trace records
- External timestamping service integration
- Audit log integrity verification
- Legal hold capabilities

### 4. Information Disclosure (Confidentiality)

**Threat:** Unauthorized access to sensitive decision logic, citizen data, or legal information.

**Attack Vectors:**
- SQL injection in trace queries
- Privilege escalation
- Side-channel attacks
- Data exfiltration

**Controls Implemented:**
- Role-based access control (RBAC)
- Input sanitization and validation
- PII redaction in explanations
- Encrypted data at rest

**Controls Needed:**
- Field-level encryption for sensitive data
- Declarative redaction policies per decision function
- Data loss prevention (DLP) monitoring
- Zero-trust network architecture

### 5. Denial of Service (Availability)

**Threat:** System unavailability preventing government service delivery.

**Attack Vectors:**
- Resource exhaustion attacks
- Database connection flooding
- Malicious decision functions
- Infrastructure attacks

**Controls Implemented:**
- Rate limiting per caller
- Circuit breakers on external dependencies
- Resource quotas and timeouts
- Horizontal scaling capabilities

**Controls Needed:**
- DDoS protection and mitigation
- Load testing and capacity planning
- Graceful degradation modes
- Disaster recovery procedures

### 6. Elevation of Privilege (Authorization)

**Threat:** Unauthorized access to administrative functions or sensitive operations.

**Attack Vectors:**
- Privilege escalation bugs
- Misconfigured access controls
- Token manipulation
- Insider threats

**Controls Implemented:**
- Principle of least privilege
- Function-level access controls
- Separation of duties (owner/reviewer)
- Audit logging of all administrative actions

**Controls Needed:**
- Just-in-time (JIT) access provisioning
- Privileged access management (PAM)
- Regular access reviews and certification
- Behavioral analytics for insider threat detection

## Specific Security Controls

### Cryptographic Controls

**Key Management:**
- AWS KMS/GCP KMS for key storage and rotation
- Hardware security modules (HSM) for root keys
- Key escrow for legal compliance
- Certificate transparency monitoring

**Digital Signatures:**
- RS256 signatures for JWT tokens
- ECDSA signatures for release signing
- Timestamping for signature validity
- Signature verification in audit service

### Network Security

**Transport Security:**
- TLS 1.3 for all communications
- mTLS for service-to-service communication
- Certificate pinning for critical endpoints
- Perfect forward secrecy

**Network Segmentation:**
- DMZ for external-facing APIs
- Internal network segmentation
- Zero-trust network architecture
- Network monitoring and anomaly detection

### Application Security

**Input Validation:**
- JSON Schema validation for all inputs
- SQL injection prevention
- XSS protection in explanation API
- File upload restrictions

**Authentication & Authorization:**
- Multi-factor authentication for administrators
- JWT tokens with short expiration
- Role-based access control
- Function-level permissions

### Data Protection

**Encryption:**
- AES-256 encryption at rest
- TLS 1.3 encryption in transit
- Field-level encryption for PII
- Key rotation policies

**Data Handling:**
- Declarative redaction policies
- Data minimization principles
- Retention period enforcement
- Secure data disposal

## Compliance Requirements

### Finnish/EU Legal Requirements

**Data Protection (GDPR):**
- Lawful basis for processing
- Data subject rights implementation
- Privacy by design principles
- Data protection impact assessments (DPIA)

**Public Sector Requirements:**
- Transparency obligations
- Citizen appeal mechanisms
- Audit trail requirements
- Data retention policies

**Security Standards:**
- ISO 27001 compliance
- Common Criteria evaluation
- FISMA compliance (if applicable)
- SOC 2 Type II certification

## Incident Response

### Security Incident Classification

**Severity Levels:**
- **Critical:** System compromise, data breach, service unavailability
- **High:** Unauthorized access, privilege escalation, tampering
- **Medium:** Policy violations, configuration errors
- **Low:** Minor security issues, false positives

### Response Procedures

**Detection:**
- Automated monitoring and alerting
- Security information and event management (SIEM)
- Threat intelligence integration
- User behavior analytics

**Response:**
- Incident response team activation
- Evidence preservation and collection
- Containment and eradication
- Recovery and lessons learned

**Communication:**
- Internal stakeholder notification
- External authority reporting (if required)
- Public disclosure (if necessary)
- Post-incident reviews

## Security Metrics and Monitoring

### Key Performance Indicators (KPIs)

**Security Metrics:**
- Mean time to detection (MTTD)
- Mean time to response (MTTR)
- False positive rate
- Security control effectiveness

**Compliance Metrics:**
- Audit findings resolution time
- Policy compliance percentage
- Training completion rates
- Incident response effectiveness

### Continuous Monitoring

**Real-time Monitoring:**
- Security event correlation
- Anomaly detection
- Threat hunting activities
- Vulnerability scanning

**Regular Assessments:**
- Penetration testing (quarterly)
- Security code reviews
- Architecture risk assessments
- Compliance audits

## Risk Assessment Matrix

| Threat | Likelihood | Impact | Risk Level | Mitigation Priority |
|--------|------------|--------|------------|-------------------|
| Code Injection | Medium | High | High | Critical |
| Trace Tampering | Low | High | Medium | High |
| Legal Reference Substitution | Low | High | Medium | High |
| DDoS Attack | Medium | Medium | Medium | Medium |
| Insider Threat | Low | High | Medium | High |
| Key Compromise | Low | Critical | High | Critical |

## Implementation Roadmap

### Phase 1 (Immediate - 30 days)
- Implement JWT + mTLS authentication
- Add replay protection with nonces
- Deploy KMS integration for signatures
- Enable tamper detection alerts

### Phase 2 (Short-term - 90 days)
- Implement declarative redaction policies
- Add comprehensive audit endpoints
- Deploy security monitoring and alerting
- Complete penetration testing

### Phase 3 (Medium-term - 180 days)
- Implement zero-trust network architecture
- Deploy behavioral analytics
- Complete compliance certification
- Establish incident response procedures

### Phase 4 (Long-term - 365 days)
- Achieve full compliance certification
- Implement advanced threat detection
- Complete disaster recovery testing
- Establish security operations center (SOC)

## Conclusion

The Policy as Code platform implements a comprehensive security model addressing all major threat vectors. The combination of cryptographic controls, network security, application security, and data protection measures provides defense in depth against sophisticated attacks.

Continuous monitoring, regular assessments, and incident response capabilities ensure the platform maintains its security posture as threats evolve. The implementation roadmap provides a clear path to achieving government-grade security standards.

**Security Contact:** security@policy-as-code.fi
**Last Updated:** 2024-01-15
**Next Review:** 2024-04-15
