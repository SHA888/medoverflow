# Indonesia Jurisdiction Adapter (STR/KKI) — Design

**Status**: M2 task 2.2.2 — design + stub only, no external calls
**Scope**: `identity-verification` crate, `CredentialPort` implementation

## Purpose

Indonesian clinicians hold a **STR** (Surat Tanda Registrasi — Registration
Certificate) issued by **KKI** (Konsil Kedokteran Indonesia — Indonesian
Medical Council). A jurisdiction-specific adapter would let MedOverflow
verify Indonesian clinical licenses the same way the generic adapter
verifies ORCID / institutional email / manual review, but this task is
scoped to the *design and stub* only — see "Deferred: real verification"
below for why.

This mirrors the CLAUDE.md deferred-design note: "Advanced jurisdiction
adapters (NPI, STR) — only stubs in M2; full implementation only if pilot
shows demand."

## Why a jurisdiction adapter, not a generic-adapter extension

The generic adapter (`generic_adapter.rs`, task 2.2.1) verifies identity
via channels that are inherently jurisdiction-agnostic (ORCID is global,
institutional email is domain-based, manual review is a local decision).
STR/KKI verification is different in kind: it depends on a specific
government registry, a specific document format (STR number), and a
specific expiry/renewal cadence set by Indonesian regulation. Folding this
into the generic adapter would mean the generic adapter's `CredentialPort`
implementation starts branching on jurisdiction, which defeats the point
of per-jurisdiction adapters as separate, independently-evolving units
(see `CredentialPort` port definition in `qa-core/src/domain/ports.rs`).

## Scope mapping

An STR-verified user maps to `CredentialScope::Clinical` — the STR
certifies medical licensure, not software or research expertise. This
matches the scope semantics documented in `docs/BADGE-SEMANTICS.md`: a
Clinical-scope badge means "domain expertise relevant to
software/informatics," never "medical advice for you."

## Data shape (stub)

```rust
pub struct StrRegistration {
    /// STR number as printed on the certificate (format not yet validated —
    /// KKI's exact numbering scheme is not encoded until the real adapter
    /// integrates with the registry).
    pub str_number: String,
    /// Registered practitioner's name, for audit/manual cross-check only.
    pub practitioner_name: String,
}

pub struct IndonesiaAdapterConfig {
    /// Feature flag: whether this adapter is permitted to verify anyone.
    /// Defaults to `false`. Even when `true`, the stub makes no external
    /// calls and never issues a credential (see "Deferred" below) — the
    /// flag exists as the wiring point the real implementation will read.
    pub enabled: bool,
}
```

## Feature flag: activation, not compilation

The flag is a **runtime** config value (`IndonesiaAdapterConfig::enabled`),
not a Cargo compile-time feature. Rationale: the module always compiles
and its tests always run in CI (so the stub's shape is checked on every
build), but no deployment can accidentally start verifying Indonesian
credentials before the real KKI integration exists — the flag is the
single place that would need to flip, and until then `verify_credential`
returns `None` unconditionally, flag value notwithstanding.

## Deferred: real verification

The real adapter would need to:

1. Call the KKI STR registry (or an authorized intermediary) to confirm a
   `str_number` is currently valid and matches the claimed practitioner.
2. Handle STR renewal cadence (Indonesian STR certificates have a defined
   validity period; expiry must feed the same typestate lifecycle used by
   `VerifiedCredential` in `lib.rs`).
3. Decide a registration/lookup flow for users to submit their STR number
   (this repo has no ingestion path for that yet).

None of this is implemented. There is **no network client, no HTTP
dependency, and no registry lookup** in this stub — `verify_credential`
is a pure function that returns `None`. This is intentional: task 2.2.2's
DoD is "design document and stub implementation... no external calls
yet." Full implementation is explicitly deferred until pilot demand
justifies the integration work (per CLAUDE.md's deferred-designs list).

## Test coverage

The stub's tests assert the two properties that matter before the real
integration lands:

- `enabled: false` (the default) never verifies anyone.
- `enabled: true` still never verifies anyone (no verification logic
  exists yet) — this pins down that flipping the flag today is a no-op,
  not an accidental activation of unfinished logic.
