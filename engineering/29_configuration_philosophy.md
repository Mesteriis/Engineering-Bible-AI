# Configuration Philosophy

Configuration is a control surface. Treat it as part of the system contract, not as a junk drawer with environment variables rattling around like cursed cutlery.

## Configuration types

| Type | Purpose | Example | Rules |
|---|---|---|---|
| Build-time config | Changes artifact construction | feature compiled in/out | Must be reproducible |
| Deploy-time config | Changes environment binding | host, port, region | Validate at startup |
| Runtime config | Changes behavior without redeploy | rate limits, rollout settings | Audit and observe changes |
| Secret | Grants access | token, private key | Never log, commit, or expose |
| Feature flag | Controls rollout or experiment | enable new flow | Must have owner and removal plan |
| User preference | Per-user behavior | locale, theme | Belongs in product data, not process env |
| Test config | Isolates validation environment | fake provider URL | Must not leak into production defaults |

## Core principles

- Configuration must be named by intent, not by implementation accident.
- Defaults must be safe.
- Required configuration must fail fast at startup.
- Secrets are not configuration documentation. They are sensitive inputs with stricter handling.
- Runtime config changes must be observable when they affect behavior.
- Feature flags must expire or become permanent product settings.
- Environment variables are process inputs, not a universal architecture.

## Naming

Configuration names should communicate:

- owner domain;
- affected behavior;
- unit of value;
- environment scope when relevant.

Good:

- `PAYMENT_CAPTURE_TIMEOUT_SECONDS`;
- `DEVICE_COMMAND_QUEUE_MAX_DEPTH`;
- `API_PUBLIC_BASE_URL`;
- `AUTH_SESSION_TTL_SECONDS`.

Suspicious:

- `TIMEOUT`;
- `FLAG2`;
- `USE_NEW`;
- `MAGIC_MODE`;
- `CONFIG_JSON`.

## Validation

Validate configuration before serving traffic.

Check:

- required values are present;
- values parse into expected types;
- numeric ranges are valid;
- paths and URLs are well-formed;
- mutually exclusive options are not both enabled;
- dependencies implied by config are available or explicitly lazy;
- production defaults are not unsafe.

Do not wait until the first customer request to discover that the service cannot parse its own personality.

## Secrets

Secrets must:

- never be committed;
- never be logged;
- never be included in exception messages;
- be injected through approved secret mechanisms;
- have rotation strategy when production-facing;
- be separated from non-secret config when tooling allows;
- be redacted in diagnostics.

A value being stored in an environment variable does not magically make it safe.

## Feature flags

Every feature flag needs:

- owner;
- purpose;
- default state;
- rollout plan;
- kill-switch behavior if relevant;
- observability;
- removal condition;
- expected removal date or decision point.

Long-lived flags become configuration or product settings. Undead flags become archaeology.

## Runtime configuration

Runtime configuration is appropriate when:

- safe behavior must change quickly;
- gradual rollout is required;
- operations need a temporary mitigation;
- values are data-like and not code-like.

Runtime configuration is not appropriate for:

- replacing clear code paths with remote spaghetti;
- bypassing review;
- hiding unfinished features;
- encoding business logic as JSON blobs.

## Documentation

Every production configuration option should document:

- name;
- type;
- default;
- allowed range or values;
- whether secret;
- owner;
- effect;
- reload behavior;
- production example when safe.

## Review checklist

Before merging a configuration change, verify:

- the config is actually needed;
- the name is clear;
- default is safe;
- validation happens early;
- secret handling is correct;
- runtime changes are observable when relevant;
- feature flags have a lifecycle;
- tests cover missing, invalid, and boundary values where practical.
