// This fixture proves the read-typestate guarantee for task 2.2.4's DoD
// ("typestate prevents reading expired credentials") generically, without
// needing to construct an actual Issued/Expired value (impossible from
// outside this crate anyway, since `issue` is `pub(crate)` — see
// cannot_call_issue.rs).
//
// Read accessors (scope, user_id, credential_id, expiry, is_expired,
// authority_weight) are defined only in `impl VerifiedCredential<Active>`,
// not in the generic `impl<S: CredentialState> VerifiedCredential<S>` block.
// So a function generic over `S: CredentialState` — which must compile for
// every state, including Issued and Expired, not just Active — cannot call
// `.scope()` on its `VerifiedCredential<S>` parameter. This must fail to
// compile with E0599 (no method found), because method resolution for a
// generic type parameter only considers trait bounds, not the concrete
// `Active` inherent impl.

use identity_verification::{CredentialState, VerifiedCredential};

fn try_read_scope<S: CredentialState>(cred: VerifiedCredential<S>) {
    let _ = cred.scope();
}

fn main() {}
