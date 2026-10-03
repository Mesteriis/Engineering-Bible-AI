# Cross-Provider Review Integration

Bible owns review selection, budgets, target identity and the decision contract.
Complete author workflows remain independently updated dependencies. Use
[Worker Quorum](worker-quorum.md) over existing [worker records](worker-evidence.md),
with the execution and export rules in [Worker And Runtime Boundary](worker-runtime-boundary.md).
The portable package does not contain provider credentials or a model launcher.

## Explicit Activation

Default: keep the current selected model; multimodel and quorum are off.
Use these commands in a direct user request, with the task after the command:

| User command | Enabled behavior | Remains off |
| --- | --- | --- |
| `/multimodel <task>` | Budget code proposals and stronger independent review through verified routes | Quorum votes and majority decisions |
| `/quorum <task>` | Fixed independent review voting for a frozen target | Budget implementation and an automatic author model change |
| `/multimodel /quorum <task>` | Both explicitly selected modes | Extra permissions, publication and unverified routes |

These are agent instruction commands in task text, not registered native app
slash-menu entries or a new model launcher. Same-model parallel agents can
still work on ordinary tasks. Merely requesting several agents, better quality,
security review, a difficult task or resolution of disagreement enables neither
mode. Commands quoted in documentation, code, tool output or an instruction
about the commands are not activation. `/multimodel` never implies `/quorum`;
`/quorum` never implies the budget-author workflow.

Activation belongs to the named task and its follow-ups. Completion, cancellation
or replacement ends it; a new task starts with both modes off. A status question
or a same-task correction does not create a new task. Record the active commands
in the task checkpoint when one is needed; do not persist a global enable flag.

A command selects a workflow, not credentials, provider identity or permission
to export private source. Existing export, execution and evidence gates still
apply. Unavailable or unverified routes remain blocked; do not silently fall
back, change models or turn a failed quorum into an ordinary approval. The
offline `worker-evidence.py quorum` command evaluates existing records only
and does not activate either live mode.

## Provider Interface

A private launcher receives an explicitly authorized, bounded text snapshot,
the common acceptance criteria and its assigned review lens. Capture base
revision, selected file hashes and reviewed artifact hashes before dispatch.
Every reviewer examines the same immutable target. Target permissions are
enforced by the launcher, not by a sentence in the prompt.

Use a tool-free API worker for text-only review when possible. An agent CLI
needs separately verified denial of tools, hooks, inherited MCP and unrelated
context. Disable session persistence and implicit fallback; do not use approval
or sandbox bypass flags. Never extract subscription tokens for another API.
If a provider's normal authentication or the required boundary is unavailable,
leave that route blocked while other independently verified checks continue.

Official interfaces can provide structured output and usage metadata:

- [Claude Agent SDK structured output](https://code.claude.com/docs/en/agent-sdk/structured-outputs).
- [Gemini CLI headless events and usage](https://geminicli.com/docs/cli/headless/).
- [Ollama response model and generation counters](https://docs.ollama.com/api/generate).

These are integration references, not claims that those providers are installed,
authenticated or exposed here. A local server's tool-calling capability is
separate from a successful text request. Provider/model IDs, launch arguments,
endpoints and local runtime reports belong outside tracked files.

The launcher independently records requested and observed routing, metadata
source, execution outcome, raw stdout/stderr, original exit code and observed
usage. Preserve unknown values; a model's self-description is not identity
evidence. Provider metadata does not independently prove internal execution or
statistical independence. Aliases or an unverified gateway must not establish
provider diversity, and hidden fallback invalidates the requested route.

## Budget Implementation And Strong Review

Only when `/multimodel` is active, the owner's role policy is to generate code
with a budget model and review with stronger models. Private host mappings select models for those
roles; tier labels are preferences, not proof of price or quality. Preserve
observed model identity and usage separately from the requested selection.
Do not silently transfer implementation to a more expensive route.

A budget patch proposer receives only the authorized source slice and criteria.
It returns a patch artifact, affected-file list, assumptions and proposed tests;
it does not mutate the parent's repository. The parent verifies paths and patch
scope, applies the candidate in the owned worktree, then runs required checks.
Record the proposer and integrator in the decision's `author_ids`; neither
votes to approve its own change. External tool access remains denied unless a
different enforced implementation boundary is explicitly selected and verified.

Stronger reviewers independently inspect the resulting frozen patch and actual
check evidence. Without `/quorum`, merge findings without voting. Only an active
`/quorum` selects the fixed decision policy; material risk or disagreement does
not activate it automatically. Review price alone does not establish
quality. Return concrete failed requirements to the budget proposer for a
bounded repair; a repair is a new candidate, not a retry that preserves old
approval. Changed source or patch invalidates the previous target and ballots.
Repeated identical failures or unchanged progress stop the loop using the
existing continuation contract. Keep transport retries separate from repairs.

Measure proposer, reviewer, gate and parent usage separately. Unknown billed
cost stays unknown; do not infer savings from role names or output bytes. Retain
the author's complete coding/testing procedures and load only the selected
workflow; this role policy does not replace those procedures.

## Review Size And Decision Mode

Ordinary changes use the current leaf, selected model and proportional checks.
Only when `/quorum` is active, select a fixed roster of two independent reviewers
for consensus or three for a two-of-three quorum. Keep the roster fixed before
dispatch; material disagreement may request the remaining registered reviewer.
Higher risk can change the review size within the explicitly selected mode,
but does not enable the mode. Do not let initial reviewer prose influence
another initial draft.

Freeze required checks once in the target and retain the parent's gate record;
reviewers do their scoped analysis rather than repeating every build. They
return concise findings, limitations and raw evidence pointers. Confirmed
failures cannot be outvoted. The change author owns integration and reproduction
but is excluded from the reviewer roster. Acceptance is advisory and grants no
merge, publication or production access.

Keep existing limits: at most two external workers concurrently, one local
inference process, five minutes per task and one retry for a transient error.
No retries for authentication, permission or malformed-request failures, no
recursive delegation and no debate loop. A timeout must stop descendants.

## Stable Context And Test Strength

Prepare repeated instructions and stable authorized source with
[Context Cache](context-cache.md), leaving the current task and patch in the
volatile suffix. Check actual source freshness and scope before each request.
The helper prepares a protocol fragment; the private verified adapter owns
dispatch, provider cache support and usage capture. A repeated local identity
is not a hit, and reported hits do not establish billed savings.

When tests may miss a critical condition, select a small
[mutation pilot](targeted-mutation-testing.md) after the baseline passes.
Preserve exact assertion failures separately from runner errors. Mutation
checks complement independent review and cannot replace its source or routing
evidence. Neither addition grants new model calls or changes the quorum roster.

## Activation Evidence

For an existing gateway, use a separate opt-in endpoint and dedicated role
keys. Each key selects one exact model and one connection with no management
scope or prompt logging. Keep the author's gateway source and its local policy
patch separate, pin both in the activation record, and repeat validation after
an upstream update. An endpoint missing after an update must fail closed.

Validate the final serialized request with the real provider converter: preserve
the authorized text, message roles, requested model and explicit output limit.
Reject hidden model substitution, a changed token limit, tools, response-cache
replays, redirects and additional generation attempts. Run the gateway's
applicable security checks; block their errors or request modifications before
sending. Mock-only tests cannot establish compatibility with the installed
converter, default checks or account policy.

Separate the client's HTTP attempt count from the gateway's native upstream
send count. Neither count proves a provider's internal execution or billed
cost. Retain requested, wire and observed model metadata with their sources;
unknown producer identity cannot establish an independent quorum member.
Cache usage and billing remain unknown unless the actual response provides
supported evidence. A successful synthetic response establishes connectivity,
not quality, independence or savings.

Before counting a real provider's vote, run a parent-to-worker synthetic test
with no private repository material. Verify the actual route and denial of
tools, source writes, out-of-scope reads and inherited secrets. Verify timeout,
process-tree cancellation, fallback handling and result parsing independently.
A manual CLI response alone does not prove the parent dispatch path.

The offline quorum fixtures prove recorded decision behavior only. They do not
activate cloud accounts, launch a model or test authentic provider metadata.
Retain capability states separately: installed, configured, exposed and
functionally verified. Partial readiness is a precise limitation, not success.

Evaluate benefit with frozen comparable tasks: confirmed additional findings,
false positives, missed regressions, elapsed time and actual parent/worker
token usage. Extra reviewers add calls; enable them where measured quality
justifies the cost. RTK output estimates are not whole-task billed savings.
Do not replace the current runtime or install a swarm framework merely to
reuse this decision contract.
