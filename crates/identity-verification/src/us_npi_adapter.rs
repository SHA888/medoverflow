//! US jurisdiction adapter (NPI) — design stub, no external calls.
//!
//! See `docs/JURISDICTION-ADAPTER-US-NPI.md` for the full design rationale.
//!
//! This adapter's shape exists so the NPPES NPI registry integration has a
//! place to land, but the integration itself is deferred (task 2.2.3 scope:
//! design + stub only). It is a [`StubJurisdictionAdapter`] parameterized
//! over [`NpiRegistration`] — the shared stub behavior (always returns
//! `None`, runtime-flagged activation) lives in that module; this one owns
//! only the US-specific registration record.

use crate::stub_jurisdiction_adapter::{StubAdapterConfig, StubJurisdictionAdapter};

/// A US NPI (National Provider Identifier) registration record.
///
/// Carries the fields a future NPPES registry lookup would need to
/// confirm. Not yet consumed by any verification logic — `UsNpiAdapter`
/// has no registry to check this against.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NpiRegistration {
    /// The 10-digit NPI number as issued by NPPES. Not validated against
    /// the Luhn check-digit — format validation is deferred to the real
    /// adapter.
    pub npi_number: String,
    /// Registered provider's name, for audit/manual cross-check only.
    pub provider_name: String,
}

/// Configuration for the US jurisdiction adapter (NPI).
pub type UsNpiAdapterConfig = StubAdapterConfig;

/// US jurisdiction adapter (NPI) — stub implementation.
///
/// Implements `CredentialPort` so it can be wired into qa-core once the
/// real NPPES registry integration lands, but currently never issues a
/// credential regardless of configuration or registered NPI data. See
/// `stub_jurisdiction_adapter` for the shared behavior and its tests.
pub type UsNpiAdapter = StubJurisdictionAdapter<NpiRegistration>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn npi_registration_carries_expected_fields() {
        let reg = NpiRegistration {
            npi_number: "1234567893".to_string(),
            provider_name: "Dr. Test".to_string(),
        };
        assert_eq!(reg.npi_number, "1234567893");
        assert_eq!(reg.provider_name, "Dr. Test");
    }
}
