//! Indonesia jurisdiction adapter (STR/KKI) — design stub, no external calls.
//!
//! See `docs/JURISDICTION-ADAPTER-INDONESIA.md` for the full design rationale.
//!
//! This adapter's shape exists so the KKI STR registry integration has a place
//! to land, but the integration itself is deferred (task 2.2.2 scope: design +
//! stub only). `verify_credential` is a pure function that always returns
//! `None` — there is no network client and no registry lookup here yet.
//!
//! Activation is gated by [`IndonesiaAdapterConfig::enabled`], a runtime flag
//! rather than a Cargo feature: the module always compiles and its tests
//! always run in CI, but no deployment can start verifying Indonesian
//! credentials before the real KKI integration exists to back the flag.

use qa_core::domain::credential::AuthoritySnapshot;
use qa_core::domain::id::UserId;
use qa_core::domain::ports::CredentialPort;

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
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct IndonesiaAdapterConfig {
    /// Feature flag controlling activation. Defaults to `false`. Even when
    /// `true`, `verify_credential` still returns `None` unconditionally —
    /// this flag is the wiring point the real KKI integration will read,
    /// not a switch on any verification logic that exists today.
    pub enabled: bool,
}

/// Indonesia jurisdiction adapter (STR/KKI) — stub implementation.
///
/// Implements `CredentialPort` so it can be wired into qa-core once the
/// real KKI registry integration lands, but currently never issues a
/// credential regardless of configuration or registered STR data.
#[derive(Clone, Debug, Default)]
pub struct IndonesiaAdapter {
    config: IndonesiaAdapterConfig,
}

impl IndonesiaAdapter {
    /// Create a new Indonesia adapter with the given configuration.
    pub fn new(config: IndonesiaAdapterConfig) -> Self {
        IndonesiaAdapter { config }
    }

    /// Whether this adapter is enabled by feature flag.
    ///
    /// Exposed for tests and diagnostics; does not affect verification
    /// outcome today since no verification logic exists yet.
    pub fn is_enabled(&self) -> bool {
        self.config.enabled
    }
}

impl CredentialPort for IndonesiaAdapter {
    /// Always returns `None`.
    ///
    /// No STR/KKI registry integration exists yet (see module docs and
    /// `docs/JURISDICTION-ADAPTER-INDONESIA.md`). This makes no external
    /// calls, regardless of `self.config.enabled`.
    fn verify_credential(&self, _user_id: UserId) -> Option<AuthoritySnapshot> {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn disabled_adapter_never_verifies() {
        let adapter = IndonesiaAdapter::new(IndonesiaAdapterConfig { enabled: false });
        assert!(!adapter.is_enabled());
        assert_eq!(adapter.verify_credential(UserId::new(1)), None);
    }

    #[test]
    fn enabled_adapter_still_never_verifies() {
        // Pins down that flipping the flag today is a no-op, not an
        // accidental activation of unfinished verification logic.
        let adapter = IndonesiaAdapter::new(IndonesiaAdapterConfig { enabled: true });
        assert!(adapter.is_enabled());
        assert_eq!(adapter.verify_credential(UserId::new(1)), None);
    }

    #[test]
    fn default_config_is_disabled() {
        let config = IndonesiaAdapterConfig::default();
        assert!(!config.enabled);
    }

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
