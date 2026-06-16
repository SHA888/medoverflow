//! Port definitions: interfaces to external systems.
//!
//! Ports are the boundaries of the qa-core hexagon. They define what services
//! qa-core needs from external systems (identity-verification, search, persistence)
//! without depending directly on those systems. Adapters implement these ports.
//!
//! This enforces the architectural rule: only ports point outward; the domain logic
//! itself has zero outward dependencies.

use crate::domain::id::{AnswerId, ContentId, QuestionId, UserId};
use crate::domain::license::License;

/// Representation of a content change for indexing.
///
/// This enum allows the search system to distinguish between questions and answers
/// when receiving change notifications. The search index tracks both types separately
/// to support type-specific queries and ranking.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IndexableContent {
    /// A question has been created, modified, or deleted.
    Question(QuestionId),
    /// An answer has been created, modified, or deleted.
    Answer(AnswerId),
}

/// Port for credential verification.
///
/// This port defines how qa-core requests verification of user credentials.
/// The identity-verification crate implements this port, returning opaque
/// VerifiedCredential tokens that qa-core cannot forge.
///
/// Implementations must:
/// - Return `Some(credential)` if the user has been verified
/// - Return `None` if the user is not verified or does not exist
/// - Never return an invalid or expired credential (type system enforces this)
pub trait CredentialPort {
    /// Verify a user by ID, returning an opaque credential token if verified.
    ///
    /// # Arguments
    /// - `user_id`: The user to verify
    ///
    /// # Returns
    /// - `Some(credential)`: User is verified and active
    /// - `None`: User is not verified, does not exist, or is inactive
    ///
    /// # Implementation notes
    /// Implementers (identity-verification crate) are responsible for:
    /// - Checking user identity against external authority systems
    /// - Managing credential expiry and lifecycle
    /// - Issuing unforgeable tokens that qa-core cannot construct
    fn verify_credential(&self, user_id: UserId) -> Option<()>;
    // TODO: When identity-verification is available in M2, replace Option<()>
    // with Option<VerifiedCredential<Active>>. Keeping as () for now to avoid
    // circular dependencies during M1 (library-only phase).
}

/// Port for content source licensing.
///
/// This port defines how qa-core queries the license of content from external sources.
/// The ingestion crate implements this port, tracking which license applies to each
/// piece of content based on its origin (Stack Exchange, Biostars, native, etc).
///
/// This is essential for:
/// - Ensuring all content respects its original license
/// - Attribution rendering (must know the license to render correct attribution)
/// - Legal compliance (must verify content can be used before including it)
///
/// Implementations must:
/// - Return the correct License for each content ID
/// - Never return an unknown or invalid license (exhaustive enum enforces this)
/// - Be consistent: same content ID always returns same license
pub trait ContentSourcePort {
    /// Query the license of a piece of content by ID.
    ///
    /// # Arguments
    /// - `content_id`: The content to query (question, answer, or imported item)
    ///
    /// # Returns
    /// - The License that applies to this content (exhaustive enum, no unknowns)
    ///
    /// # Implementation notes
    /// Implementers (ingestion crate) are responsible for:
    /// - Tracking per-source license rules (SE=CC BY-SA, Biostars=CC BY, etc)
    /// - Assigning licenses to mirrored content based on source
    /// - Assigning licenses to native content based on platform policy
    /// - Never returning an unknown license (compile-fail test enforces this)
    fn source_license(&self, content_id: ContentId) -> License;
}

/// Port for search index updates.
///
/// This port defines how qa-core notifies the search system when questions or answers
/// are created, modified, or deleted. The search crate implements this port as a
/// read-side projection that stays synchronized with the qa-core write side.
///
/// This separation enables:
/// - Independent scaling of search indexing from the core domain logic
/// - Different storage backends for the search index (Elasticsearch, SQLite FTS, etc)
/// - Eventual consistency: the search index can lag behind the core domain
/// - Decoupled failure domains: if search indexing fails, it doesn't crash the domain
///
/// Implementations must:
/// - Accept notifications for questions and answers (exhaustive enum enforces this)
/// - Update the search index to reflect the new state
/// - Be idempotent: receiving the same notification twice must be safe
/// - Handle both creation and modification (the port does not distinguish; indexers can decide)
pub trait SearchIndexPort {
    /// Notify the search index that content has changed.
    ///
    /// # Arguments
    /// - `content`: The question or answer that changed (created, modified, or deleted)
    ///
    /// # Implementation notes
    /// Implementers (search crate) are responsible for:
    /// - Updating full-text indexes
    /// - Updating tag facets
    /// - Updating jurisdiction and date facets
    /// - Handling deletions (may store deletion markers instead of removing entirely)
    /// - Being idempotent: if the same content notification arrives twice, the result must be the same
    fn notify_content_changed(&self, content: IndexableContent);
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    /// Mock credential port for testing qa-core logic.
    struct MockCredentialPort {
        verified_users: std::collections::HashSet<u64>,
    }

    impl MockCredentialPort {
        fn new(verified_users: Vec<u64>) -> Self {
            MockCredentialPort {
                verified_users: verified_users.into_iter().collect(),
            }
        }
    }

    impl CredentialPort for MockCredentialPort {
        fn verify_credential(&self, user_id: UserId) -> Option<()> {
            if self.verified_users.contains(&user_id.inner()) {
                Some(())
            } else {
                None
            }
        }
    }

    #[test]
    fn mock_port_returns_none_for_unverified() {
        let port = MockCredentialPort::new(vec![1, 2, 3]);
        assert_eq!(port.verify_credential(UserId::new(1)), Some(()));
        assert_eq!(port.verify_credential(UserId::new(999)), None);
    }

    #[test]
    fn mock_port_verifies_users() {
        let port = MockCredentialPort::new(vec![42, 100]);
        assert_eq!(port.verify_credential(UserId::new(42)), Some(()));
        assert_eq!(port.verify_credential(UserId::new(100)), Some(()));
        assert_eq!(port.verify_credential(UserId::new(50)), None);
    }

    /// Mock content source port for testing qa-core logic.
    struct MockContentSourcePort {
        licenses: HashMap<u64, License>,
    }

    impl MockContentSourcePort {
        fn new(licenses: HashMap<u64, License>) -> Self {
            MockContentSourcePort { licenses }
        }
    }

    impl ContentSourcePort for MockContentSourcePort {
        fn source_license(&self, content_id: ContentId) -> License {
            self.licenses
                .get(&content_id.inner())
                .copied()
                .expect("content must have a license")
        }
    }

    #[test]
    fn mock_content_port_returns_correct_licenses() {
        let mut licenses = HashMap::new();
        licenses.insert(1, License::CcBySa4);
        licenses.insert(2, License::CcBy4);
        licenses.insert(3, License::LinkOnly);

        let port = MockContentSourcePort::new(licenses);

        assert_eq!(port.source_license(ContentId::new(1)), License::CcBySa4);
        assert_eq!(port.source_license(ContentId::new(2)), License::CcBy4);
        assert_eq!(port.source_license(ContentId::new(3)), License::LinkOnly);
    }

    #[test]
    #[should_panic]
    fn mock_content_port_panics_for_unlicensed_content() {
        let port = MockContentSourcePort::new(HashMap::new());
        let _ = port.source_license(ContentId::new(999));
    }

    /// Mock search index port for testing qa-core logic.
    #[derive(Clone)]
    struct MockSearchIndexPort {
        indexed_content: std::sync::Arc<std::sync::Mutex<Vec<IndexableContent>>>,
    }

    impl MockSearchIndexPort {
        fn new() -> Self {
            MockSearchIndexPort {
                indexed_content: std::sync::Arc::new(std::sync::Mutex::new(Vec::new())),
            }
        }

        fn get_indexed_content(&self) -> Vec<IndexableContent> {
            self.indexed_content.lock().unwrap().clone()
        }
    }

    impl SearchIndexPort for MockSearchIndexPort {
        fn notify_content_changed(&self, content: IndexableContent) {
            self.indexed_content.lock().unwrap().push(content);
        }
    }

    #[test]
    fn mock_search_port_records_question_changes() {
        let port = MockSearchIndexPort::new();
        let q1 = IndexableContent::Question(QuestionId::new(1));
        let q2 = IndexableContent::Question(QuestionId::new(2));

        port.notify_content_changed(q1);
        port.notify_content_changed(q2);

        let indexed = port.get_indexed_content();
        assert_eq!(indexed.len(), 2);
        assert_eq!(indexed[0], q1);
        assert_eq!(indexed[1], q2);
    }

    #[test]
    fn mock_search_port_records_answer_changes() {
        let port = MockSearchIndexPort::new();
        let a1 = IndexableContent::Answer(AnswerId::new(1));
        let a2 = IndexableContent::Answer(AnswerId::new(3));

        port.notify_content_changed(a1);
        port.notify_content_changed(a2);

        let indexed = port.get_indexed_content();
        assert_eq!(indexed.len(), 2);
        assert_eq!(indexed[0], a1);
        assert_eq!(indexed[1], a2);
    }

    #[test]
    fn mock_search_port_distinguishes_questions_and_answers() {
        let port = MockSearchIndexPort::new();
        let q = IndexableContent::Question(QuestionId::new(1));
        let a = IndexableContent::Answer(AnswerId::new(1));

        port.notify_content_changed(q);
        port.notify_content_changed(a);

        let indexed = port.get_indexed_content();
        assert_eq!(indexed.len(), 2);
        assert_eq!(indexed[0], q);
        assert_eq!(indexed[1], a);
        assert_ne!(indexed[0], indexed[1]);
    }
}
