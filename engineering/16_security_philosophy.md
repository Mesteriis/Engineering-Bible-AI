# Security Philosophy

Security is an engineering property, not a final checklist.

## Principles

- Treat untrusted input as hostile.
- Never hardcode, log, expose, or commit secrets.
- Validate at trust boundaries.
- Authorize actions, not just users.
- Prefer deny-by-default behavior.
- Avoid dynamic evaluation, unsafe deserialization, and shell interpolation.
- Constrain file paths, URLs, redirects, and external resources.
- Use parameterized database access.
- Preserve auditability for sensitive actions where the project supports it.
- Verify security-sensitive behavior against current code and official documentation.

## Sensitive areas

Use security workflow for:

- authentication;
- authorization;
- secrets;
- cryptography;
- injection;
- SSRF;
- deserialization;
- parsers;
- file uploads;
- path traversal;
- dependency/supply-chain changes;
- permission models;
- hardware/physical safety controls.

## Rule

Do not implement security-sensitive behavior from memory when documentation or existing project patterns are required.
