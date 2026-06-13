//! Body value object: non-empty, parsed question/answer text.
//!
//! The Body type makes empty and whitespace-only payloads unrepresentable.
//! The parser enforces this invariant at construction time, not at usage time.

use std::fmt;

/// A non-empty string payload for questions or answers.
///
/// Parse-Don't-Validate: illegal states (empty, whitespace-only) are rejected
/// at construction, making it impossible to construct an invalid Body at the type level.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub struct Body(String);

/// Error when parsing a Body.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum BodyError {
    /// Input string is empty.
    Empty,
    /// Input string contains only whitespace.
    WhitespaceOnly,
}

impl fmt::Display for BodyError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Empty => write!(f, "body cannot be empty"),
            Self::WhitespaceOnly => write!(f, "body cannot be whitespace-only"),
        }
    }
}

impl std::error::Error for BodyError {}

impl Body {
    /// Parse a string into a Body, rejecting empty or whitespace-only input.
    ///
    /// # Errors
    ///
    /// Returns `Err(BodyError::Empty)` if input is empty.
    /// Returns `Err(BodyError::WhitespaceOnly)` if input contains only whitespace.
    pub fn new(s: impl Into<String>) -> Result<Self, BodyError> {
        let inner = s.into();

        if inner.is_empty() {
            return Err(BodyError::Empty);
        }

        if inner.trim().is_empty() {
            return Err(BodyError::WhitespaceOnly);
        }

        Ok(Body(inner))
    }

    /// Access the inner string.
    pub fn as_str(&self) -> &str {
        &self.0
    }

    /// Convert into the inner string.
    pub fn into_inner(self) -> String {
        self.0
    }
}

impl fmt::Display for Body {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl AsRef<str> for Body {
    fn as_ref(&self) -> &str {
        self.as_str()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_fails() {
        assert_eq!(Body::new("").unwrap_err(), BodyError::Empty);
    }

    #[test]
    fn whitespace_fails() {
        assert_eq!(Body::new("   ").unwrap_err(), BodyError::WhitespaceOnly);
        assert_eq!(Body::new("\n").unwrap_err(), BodyError::WhitespaceOnly);
        assert_eq!(Body::new("\t").unwrap_err(), BodyError::WhitespaceOnly);
    }

    #[test]
    fn valid_succeeds() {
        let body = Body::new("Hello").expect("valid");
        assert_eq!(body.as_str(), "Hello");
    }

    #[test]
    fn preserves_leading_trailing_space() {
        let body = Body::new("  spaced  ").expect("valid");
        assert_eq!(body.as_str(), "  spaced  ");
    }

    #[test]
    fn into_inner() {
        let body = Body::new("test").expect("valid");
        assert_eq!(body.into_inner(), "test");
    }

    #[test]
    fn as_ref_str() {
        let body = Body::new("test").expect("valid");
        let s: &str = body.as_ref();
        assert_eq!(s, "test");
    }
}
