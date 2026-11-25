# Business Application UI Profile

Reviewed on 2026-10-20 for dashboards, CRM, admin, ERP and working applications.
The owner profile is `ui-business-apps`; it supplies product priorities and
routes to complete, independently updated originals. It does not reimplement
their design methods. Use [the business brief](../templates/business-ui-brief.md)
for relevant roles, objects, tasks, data and acceptance evidence.

## Reviewed Originals

| Role | Author source and latest reviewed revision | Selection |
| --- | --- | --- |
| Primary product interface design and consistent components | [Interface Design](https://github.com/Dammyjay93/interface-design), latest main June 20, `2f9be3206855bcb2d1d0af262c8bae25cba6658d` | `interface.interface-design` |
| Targeted UX, chart and implementation-stack guidance | [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/tree/56ea9cf174ed86786187daa9de0e6247cb0747e4), reviewed commit `56ea9cf174ed86786187daa9de0e6247cb0747e4` | `uipro.ui-ux-pro-max` |
| UX shaping, critique, audit, hardening and final craft | [Impeccable 4.7.0](https://github.com/pbakaus/impeccable/tree/dad8dbb3aac21ad1fa236c110315ef4abece23e8), reviewed commit `dad8dbb3aac21ad1fa236c110315ef4abece23e8` | `impeccable.impeccable`, Operate mode |

The October 20 pins follow reviewed commits, not automatic tracking updates.
See the [review and runtime limits](upstream-review-2026-10-20.md).
Interface Design's current commit is older, but its stated scope specifically
covers product interfaces. Recency and product fit are recorded separately.

Interface Design retains its self-contained original two-file leaf. UI UX Pro
Max retains all 73 files, including local data, references, Python helpers and
tests. Impeccable retains its complete leaf, including references, launchers and
four Codex agent profiles. Its Apache license and original attribution notice are retained outside
the active leaf without editing the author's files.

Choose one design lead and a support only for a distinct need. The actual brief
and existing design system determine identity, supported devices and density.
Avoid competing blanket style instructions from several authors.

## Working Interface Priorities

Preserve the actual task and product structure: relevant lists, details, edits,
filters, saved views, bulk actions and drill-down. Forms need the applicable
validation, dirty/save/error/recovery states. Permissions, navigation, keyboard
and focus behavior, readable density and supported layouts are product behavior.
KPI labels, units, time windows, freshness and charts must reflect real data;
demonstration data remains labelled. Include only states and features justified
by the product. Preserve existing visual direction when extending it.

UI UX Pro Max's generic CRM design-system row recommends a showcase/demo
pattern. That row is not an authority for CRM workspaces. Use targeted UX,
chart and stack queries and check the result's fit against the actual brief.
Its generic touch/mobile thresholds and priority labels are heuristics rather
than universal desktop requirements or accessibility certification.

| Separate task | Existing native original |
| --- | --- |
| Analytics is the primary deliverable | `build-web-data-visualization:data-visualization` |
| Frontend implementation | `build-web-apps:frontend-app-builder` |
| Table/form/menu composition | `build-web-apps:shadcn` |
| React/Next.js performance | `build-web-apps:react-best-practices` |
| Journey audit or alternative directions | `product-design:audit` / `product-design:ideate` |
| Explicit Figma or multi-screen Superdesign work | Matching native Figma / `superdesign:superdesign` provider |

Native providers retain native ownership. Their availability and connections
must be established in the current session. Names in this table do not prove
authentication or authorize customer-data export.

## Installation And Updates

Normal Bible profiles require these three originals through
`upstream_required.ui`. They are part of the 20 required originals; the complete
catalog has 247 after [discovery additions](skill-discovery-pilot.md) and the
[domain expansion](domain-skill-packs.md).
Fast remains owner-only. Select this author group directly:

```bash
be skills plan --group business-ui --json
be skills ensure --group business-ui --json
be skills route crm-workspace-design --json
be skills check --group business-ui --json
be skills update --group business-ui --dry-run --json
```

The [author lifecycle](upstream-skills.md) keeps provenance, hashes, ownership
and rollback separate from Bible package state. Exact existing providers are
reused; missing originals install without running their helpers. Source skill
roots extract only reviewed skill directories and attribution, excluding
adjacent `.claude` / `.agents` configuration and plugin hooks.

## Runtime Boundaries

UI UX Pro Max's helper examples use `CLAUDE_PLUGIN_ROOT`. Resolve the provider's
actual skill directory from `be skills route` and bind helper calls there; do not
execute an unbound placeholder or edit the author tree. The search modules use
standard-library Python with no observed network/subprocess behavior.
Persistence and overwrite flags affect project artifacts and apply only when
those writes belong to the task.

Impeccable import is dormant. Its launcher requests engine 0.1.16, downloaded on
first invocation when absent; fresh downloads verify SHA-256 sidecars. Existing
custom/cache binaries follow the author's reuse rules, so file presence alone
does not establish binary provenance. Runtime use must establish the actual
engine. Set `IMPECCABLE_NO_UPDATE_CHECK=1` for Bible-managed invocations to
disable its version ping and update-cache writes; use `be skills check/update`
for author updates. Do not run its separate updater on a Bible-managed tree.

Hooks and live mode are separate workflows. Live mode starts a localhost helper
and modifies project sources/state; importing files enables neither. If the
launcher is unavailable or refused, follow the author's documented direct
context fallback and report that context loading did not run. Nested Codex agent
files do not prove registration, model selection or execution. Interface Design's
optional Claude slash commands are outside the portable leaf; the main original
supports natural-language design and review directly.

## Evidence

Catalog and routing checks establish membership and file completeness, not
visual quality or model routing behavior. Verify real rendered screens and
affected list/form/data interactions in the product task. Repository development
uses disposable installations; the main computer profile and native host
exposure are unchanged until separately applied and verified.
