//! Indonesia jurisdiction adapter (STR/KKI) — design stub, no external calls.
//!
//! See `docs/JURISDICTION-ADAPTER-INDONESIA.md` for the full design rationale.
//!
//! This adapter's shape exists so the KKI STR registry integration has a place
//! to land, but the integration itself is deferred (task 2.2.2 scope: design +
//! stub only). It is a [`StubJurisdictionAdapter`] parameterized over
//! [`StrRegistration`] — the shared stub behavior (always returns `None`,
//! runtime-flagged activation) lives in that module; this one owns only the
//! Indonesia-specific registration record.

use crate::stub_jurisdiction_adapter::{StubAdapterConfig, StubJurisdictionAdapter};

/// An Indonesian STR (Surat Tanda Registrasi) registration record.
///
/// Carries the fields a future KKI registry lookup would need to confirm.
/// Not yet consumed by any verification logic — `IndonesiaAdapter` has no
/// registry to check this against.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct StrRegistration {
    /// STR number as printed on the certificate. Format is not validated —
    /// KKI's exact numbering scheme is not encoded until the real adapter
    /// integrates with the registry.
    pub str_number: String,
    /// Registered practitioner's name, for audit/manual cross-check only.
    pub practitioner_name: String,
}

/// Configuration for the Indonesia jurisdiction adapter.
pub type IndonesiaAdapterConfig = StubAdapterConfig;

/// Indonesia jurisdiction adapter (STR/KKI) — stub implementation.
///
/// Implements `CredentialPort` so it can be wired into qa-core once the
/// real KKI registry integration lands, but currently never issues a
/// credential regardless of configuration or registered STR data. See
/// `stub_jurisdiction_adapter` for the shared behavior and its tests.
pub type IndonesiaAdapter = StubJurisdictionAdapter<StrRegistration>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn str_registration_carries_expected_fields() {
        let reg = StrRegistration {
            str_number: "1234567890123456".to_string(),
            practitioner_name: "dr. Test".to_string(),
        };
        assert_eq!(reg.str_number, "1234567890123456");
        assert_eq!(reg.practitioner_name, "dr. Test");
    }
}
