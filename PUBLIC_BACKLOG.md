# 📋 Public Backlog — Policy-as-Code (Open Source)

## Status Legend
- ✅ = done
- 🧩 = in progress
- 🚧 = planned
- ⚠️ = requires discussion

---

## P0 — Immediate (OSS readiness, CI hygiene)

### 1. Default-deny and package hygiene (OPA) — 🚧
- Add explicit default deny = true in every entrypoint.
- Normalize package naming (org.system.policy.v1).
- Require metadata block in all Rego files (owner, version, description).
- CI must fail on missing metadata or undefined results.

### 2. Schema validation in CI — 🚧
- Validate every YAML policy against policy_schema.yaml.
- Ensure registry → Rego entrypoint mapping exists.
- Add a policy-validate job in CI with JSONPath error output.

### 3. Rego test coverage gate — 🚧
- Add opa test --coverage step; enforce ≥80%.
- Generate coverage summary in CI artifacts.

### 4. GitHub Actions hardening — 🚧
- Pin all actions to commit SHAs.
- Add actions-lint workflow to enforce pinned usage.

### 5. Structured logging + error taxonomy — 🚧
- Replace ad-hoc print with structured JSON logs.
- Add exceptions: ConfigurationError, PolicyLoadError, EvaluationError.
- Map exit codes 1/2/3 to those errors for CLI.

### 6. OPA client resilience — 🚧
- Add per-request timeout and total budget.
- Retry with jitter on transient errors.
- Integration test forces simulated 5xx / EOF.

### 7. Pre-commit hook enforcement — 🚧
- CI must run pre-commit run --all-files.
- Keep hook versions identical across .pre-commit-config.yaml and CI.

### 8. License & compliance audit — 🚧
- Verify all dependencies are OSI-approved.
- Add REUSE compliance badge and SPDX headers.
- Publish LICENSE for Rego and Python separately if needed.

### 9. Security scans — 🚧
- Add trivy for container scan and gitleaks for secret detection.
- Add tfsec for Terraform.
- Fail build on high severity findings.

### 10. Reproducible OPA bundle build — 🚧
- CI builds policy-bundle.tar.gz, computes SHA256 digest, generates SBOM (SPDX).
- Publish artifacts on each tagged release.
- Sign bundle with GitHub Actions OIDC (cosign).

---

## P1 — Short term (2–3 weeks)

### 11. Trusted bundle enforcement — 🧩
- Engine accepts --bundle-digest.
- Rejects unsigned or mismatched digest.
- Add trust_store.json for approved digests.

### 12. Policy drift guard — 🚧
- Generate Rego stubs and tests automatically from registry YAML.
- CI job ensures no orphaned entrypoints.

### 13. Decision event schema & immutable audit trail — 🚧
- JSON schema with fields: policy_id, bundle_digest, input_hash, decision, timestamp.
- Validate before writing to trace store.

### 14. Replay verification CLI — 🚧
- Command: policy-as-code replay <event-file> --bundle <bundle>
- Returns diff if non-deterministic.

### 15. Deep tests & counterexamples — 🚧
- For each policy: one positive, one negative, one boundary.
- Coverage ≥90%.

### 16. Typed configuration — 🚧
- Replace YAML parsing with Pydantic models.
- CI fails on unknown config fields.

### 17. CLI strict mode — 🚧
- --dry-run and --strict flags.
- Reject unknown keys.
- Document with real output examples.

### 18. Terraform hardening — 🚧
- Add required_providers, lock file, and backend config.
- Enforce tags and encryption via tfvalidate.

### 19. Community guidelines — 🚧
- Add CODE_OF_CONDUCT.md, SECURITY.md, and CONTRIBUTING.md updates.
- Include contact for vulnerability reporting (security@).

### 20. Documentation cleanup — 🚧
- Trim README.md to quickstart + example.
- Move roadmap and whitepapers to /docs/strategic.
- Add "How to write a policy" and "How to release a bundle" guides with copy-paste commands.

---

## P2 — Medium (4–6 weeks)

### 21. Build provenance and SBOM publication — 🚧
- Generate SLSA provenance with commit SHA, inputs, runner metadata.
- Attach .intoto.jsonl to releases.

### 22. Performance benchmarks — 🚧
- Benchmark OPA eval latency under load.
- Add benchmark/ folder and CI performance job (non-blocking).

### 23. Multi-environment promotion gates — 🚧
- Require signed bundle and passing replay tests for promotion.
- Approval step with digest pin in GitHub Environments.

### 24. Policy style guide & linter — 🚧
- Add docs/policy-style.md.
- Build custom opa lint plugin to enforce naming and metadata.

### 25. Public dashboard & alerts — 🚧
- Publish CI metrics (coverage, build status, scan results) to GitHub Pages or Shields.
- Add JSON feed for policy bundle digests.

---

## Meta / Governance

### 26. Versioning policy — 🚧
- Define how policy versions (v1.0, v1.1) map to semantic bundle tags.

### 27. Backward compatibility tests — 🚧
- Replay random subset of old trace logs against new bundles; report drift %.

### 28. Transparency reporting — 🚧
- Automate weekly summary of bundle digests, passing tests, and compliance stats.

---

## Done Definition (Public OSS)
- All GitHub Actions pinned and reproducible
- LICENSE + SPDX headers present
- CI passes with ≥80% Rego + code coverage
- All policies validated against schema
- Default-deny enforced globally
- Bundle artifacts signed and attached to GitHub release
- No critical security or license violations
