# Governance

## Maintainer Model

This repository is maintained by the repository owner.

The maintainer is responsible for:

- reviewing pull requests;
- preserving the runtime boundary;
- deciding release cadence;
- accepting or rejecting new skills;
- keeping validation commands accurate.

## Decision Rules

Changes are accepted when they are:

- useful for portable AI engineering workflows;
- compatible with existing Codex worker setups;
- documented when they affect behavior or installation;
- validated with repository-local commands;
- free of secrets and local runtime state.

## Release Policy

Until tagged releases exist, `main` is the only supported line. Future releases
should include a changelog entry and validation evidence.
