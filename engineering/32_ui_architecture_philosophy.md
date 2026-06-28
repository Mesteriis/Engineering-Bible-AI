# UI Architecture Philosophy

UI is not decoration. UI is distributed state, user intent, network failure, accessibility, latency, and product semantics arranged into rectangles. Naturally, people call this "frontend" and move on.

## Core principles

- Separate domain state, server state, local interaction state, and presentation state.
- Components should have clear responsibility and stable inputs.
- Side effects should be explicit and testable.
- Loading, empty, error, partial, optimistic, and permission states are part of the design.
- Accessibility is behavior, not a late CSS apology.
- UI contracts with backend APIs must be explicit.
- Design system usage should reduce variation, not create a shrine to tokens.

## State categories

| State type | Meaning | Owner | Examples |
|---|---|---|---|
| Domain state | Product facts and rules | Backend/domain layer | order status, device enabled |
| Server state | Remote data cached in UI | data fetching layer | fetched profile, list page |
| Local interaction state | Temporary user interaction | component or feature | open menu, input draft |
| Presentation state | Visual representation | component/design system | selected tab, density |
| Navigation state | Where the user is | router | route params, query filters |
| Permission state | What user may do | authz contract | can edit, can approve |

Do not mix these casually. A modal boolean should not become the source of truth for a domain workflow, no matter how persuasive the sprint demo was.

## Component responsibilities

A component should usually do one of:

- layout composition;
- data loading boundary;
- form interaction;
- domain action surface;
- reusable visual primitive;
- feature-specific view;
- error/loading/empty boundary.

Smell: one component loads data, transforms domain rules, owns form state, renders layout, handles permissions, formats dates, calls analytics, opens modals, and performs mutations. That component is not smart. It is unsupervised.

## Data fetching

Data fetching should define:

- query key or cache identity;
- loading behavior;
- error behavior;
- stale data behavior;
- refetch triggers;
- permission failure behavior;
- pagination and filtering contract;
- optimistic update strategy when used.

Do not let every component invent remote state management from scratch. Humans already invented enough tiny tragedies.

## Forms

A form should define:

- initial value source;
- validation boundary;
- dirty state;
- submit behavior;
- disabled state;
- server error mapping;
- success behavior;
- unsaved changes handling when relevant.

Validation may exist both client-side and server-side, but server-side validation owns truth.

## Permissions

UI permission checks improve experience. They do not replace backend authorization.

A UI permission contract should define:

- visible but disabled actions;
- hidden actions;
- backend rejection behavior;
- stale permission behavior;
- audit or explanation text where needed.

## Error states

Every meaningful UI operation should define:

- loading state;
- empty state;
- validation error;
- permission error;
- network/server error;
- partial success when relevant;
- retry path when safe;
- support/debug identifier when available.

A spinner with no timeout is just a tiny monument to denial.

## Accessibility

Accessibility architecture includes:

- semantic HTML or equivalent roles;
- keyboard navigation;
- focus management;
- labels and descriptions;
- color contrast;
- reduced motion where relevant;
- screen reader behavior;
- error announcement;
- hit targets and responsive layout.

Do not treat accessibility as a plugin that forgives architectural negligence.

## Design systems

Use design systems to:

- standardize primitives;
- reduce visual drift;
- encode accessibility defaults;
- clarify interaction patterns;
- speed implementation.

Do not use them to hide poor state ownership or force every feature into a generic component that understands nothing.

## Review checklist

Before merging UI architecture changes, verify:

- state ownership is clear;
- server state and local state are separated;
- side effects are explicit;
- loading, empty, error, permission, and partial states are covered;
- API contract assumptions are documented;
- accessibility behavior is considered;
- component boundaries follow responsibility, not arbitrary file size;
- tests or visual QA cover important states.
