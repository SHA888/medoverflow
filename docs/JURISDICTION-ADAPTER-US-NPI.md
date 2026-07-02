# US Jurisdiction Adapter (NPI) — Design

**Status**: M2 task 2.2.3 — design + stub only, no external calls
**Scope**: `identity-verification` crate, `CredentialPort` implementation

## Purpose

US clinicians are identified by an **NPI** (National Provider Identifier), a
10-digit number issued by CMS (Centers for Medicare & Medicaid Services)
through NPPES (National Plan and Provider Enumeration System). A
jurisdiction-specific adapter would let MedOverflow verify US clinical
licenses by NPI, the same way [[Indonesia's STR/KKI adapter]] verifies
Indonesian licenses. This task is scoped to the *design and stub* only —
see "Deferred: real verification" below for why.

This mirrors the CLAUDE.md deferred-design note: "Advanced jurisdiction
adapters (NPI, STR) — only stubs in M2; full implementation only if pilot
shows demand," and follows the same rationale and structure as
`docs/JURISDICTION-ADAPTER-INDONESIA.md` (task 2.2.2).

## Why a jurisdiction adapter, not a generic-adapter extension

Same reasoning as the Indonesia adapter: NPI verification depends on a
specific government registry (NPPES), a specific 10-digit numeric format
with a Luhn-based check-digit, and US-specific enumeration/deactivation
semantics. This is jurisdiction-shaped, not identity-channel-shaped like
ORCID/institutional-email/manual-review, so it belongs in its own adapter
rather than branching the generic adapter's `CredentialPort` implementation
on jurisdiction.

## Scope mapping

An NPI-verified user maps to `CredentialScope::Clinical` — the NPI
certifies enumeration as a US healthcare provider, not software or
research expertise. This matches `docs/BADGE-SEMANTICS.md`: a
Clinical-scope badge means "domain expertise relevant to
software/informatics," never "medical advice for you."

## Data shape (stub)

```rust
pub struct NpiRegistration {
    /// The 10-digit NPI number as issued by NPPES. Stored as `String` here
    /// (not validated against the Luhn check-digit) — format validation is
    /// deferred to the real adapter, same as `StrRegistration::str_number`
    /// in the Indonesia adapter.
    pub npi_number: String,
    /// Registered provider's name, for audit/manual cross-check only.
    pub provider_name: String,
}

pub struct UsNpiAdapterConfig {
    /// Feature flag: whether this adapter is permitted to verify anyone.
    /// Defaults to `false`. Even when `true`, the stub makes no external
    /// calls and never issues a credential (see "Deferred" below) — the
    /// flag exists as the wiring point the real implementation will read.
    pub enabled: bool,
}
```

## Feature flag: activation, not compilation

As with the Indonesia adapter, the flag is a **runtime** config value
(`UsNpiAdapterConfig::enabled`), not a Cargo compile-time feature. The
module always compiles and its tests always run in CI, but no deployment
can start verifying US NPI credentials before the real NPPES integration
exists — flipping the flag today is a no-op.

## Deferred: real verification

The real adapter would need to:

1. Call the NPPES NPI Registry public API (or an authorized data feed) to
   confirm an `npi_number` is currently enumerated and active, and matches
   the claimed provider.
2. Validate the NPI's Luhn check-digit locally before any lookup, to reject
   malformed numbers without a network round-trip.
3. Handle NPI deactivation (NPPES marks deactivated/retired providers;
   this must feed the same typestate lifecycle used by
   `VerifiedCredential` in `lib.rs`).
4. Decide a registration/lookup flow for users to submit their NPI (this
   repo has no ingestion path for that yet — same gap noted for STR in the
   Indonesia adapter).

None of this is implemented. There is **no network client, no HTTP
dependency, and no registry lookup** in this stub — `verify_credential`
is a pure function that returns `None`. Full implementation is explicitly
deferred until pilot demand justifies the integration work (per
CLAUDE.md's deferred-designs list).

## Test coverage

Same two properties as the Indonesia adapter's stub:

- `enabled: false` (the default) never verifies anyone.
- `enabled: true` still never verifies anyone (no verification logic
  exists yet) — pins down that flipping the flag today is a no-op, not an
  accidental activation of unfinished logic.
