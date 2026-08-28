---
name: sync-print-platform-postman
description: Sync the Print Platform Postman collection (My PHNX workspace) with API changes in the DistributionPrintPlatformApi repo - new/changed endpoints, new/changed filters, and internal bug/perf fixes to existing endpoints. Use after adding an endpoint or filter, after fixing a bug or performance issue in an existing endpoint's handler/query/repository, or when the user asks to update/sync its Postman collection.
---

# Sync DistributionPrintPlatformApi's Postman collection with API changes

Keeps the **Print Platform** Postman collection (in *My PHNX workspace*) in sync with changes in
the `distributionprintplatformapi` repo that matter to a caller or a maintainer - new/changed
endpoints, new/changed filters, and internal fixes (bugs, performance) to existing endpoints - so
the developer doesn't have to hand-edit Postman every time they ship an API change.

Read `references/conventions.md` before building any request - it has the exact target
collection/workspace ids, the repo's endpoint/filter conventions, and the OpenAPI spec caveats
(inconsistent query-key casing, `deprecated` params, `x-in_development`, v1/v2 duplication).

## Workflow

### 1. Detect what changed

Run, from the repo root:

```
git diff main...HEAD -- 'DistributionPrintPlatformApi/src/App/DistributionPrintPlatformApi/Features/**/*.cs' \
                          '.openapi/DistributionPrintPlatformApi.json' \
                          'DistributionPrintPlatformApi/src/DatabaseMigrations/**/*.sql'
git diff -- <same paths>   # also catch uncommitted work
```

(This only matches the main App project's `Features/` tree, not `DistributionPrintPlatformApi.UnitTests` -
test-only diffs never need a Postman sync.)

Classify each hunk into one of three buckets:
- **New/changed endpoint** - a new `[Http*]`+`[Route(...)]` action, or a changed route/params/body on an existing one.
- **New filter/sort field** - a new `[Filterable]`/`[Sortable]`/`[Aggregatable]` property on a response DTO plus a new `.AddField(...)` in the paired `FilterProfile`.
- **Behavior-only fix** - anything else that changes runtime behavior of an *existing* endpoint
  without changing its request/response contract: a query/command handler, repository (`Data/`),
  validator, domain logic, or a migration script (e.g. a bug fix, a performance fix like adding an
  index or fixing pagination). No new/changed route, param, body field, or filterable/sortable
  field - just different behavior behind the same contract.

If nothing under those paths changed, tell the user there's nothing to sync and stop - don't touch Postman.

### 2. Resolve the schema (contract changes) or the affected request (behavior-only fixes)

For a **new/changed endpoint** or **new filter/sort field**, find the matching operation in
`.openapi/DistributionPrintPlatformApi.json` (match on path + HTTP method - watch for v1/v2
duplicates). Pull: exact query/path param names (casing matters, varies per endpoint), the
request body schema (`components/schemas/...`) and any example. If the spec hasn't been updated
for a change you found in the C# code, say so explicitly and offer to build the request from the
controller/DTOs instead of guessing at the spec.

For a new filter field, no new operation exists - you're only updating the example `filter`/`sort`
values on the existing list request.

For a **behavior-only fix**, there's no schema to resolve - identify which existing Postman
request the changed file backs (e.g. `Features/PrintJobs/V1/GetAll/GetPrintJobsV1Query.cs` ->
the "Get Print Jobs" request, via the folder mapping in `references/conventions.md`). If a shared
file (a common repository, a base validator) makes the mapping ambiguous across multiple
requests, ask the user which endpoint(s) it affects rather than guessing.

### 3. Fetch the live collection

```
python3 ~/.claude/skills/sync-print-platform-postman/scripts/postman.py get --out /tmp/postman_collection_current.json
```

This never prints the API key. If it errors with "POSTMAN_API_KEY is not set", tell the user to
check `~/.zshenv` (not `~/.zshrc`) and open a new terminal/session.

### 4. Build the change as a local diff

Load the fetched JSON, and per `references/conventions.md`:
- New endpoint -> build a Postman request item (URL, method, params, body) and insert it into the
  correct feature folder (create the folder if the feature has none).
- New/changed filter field on an *existing* list endpoint -> do NOT touch the request's params
  array at all, not even the disabled `filter`/`sort` example values - leave those exactly as they
  are. Document the field instead, in the request's `description` (step 5): name, type, a
  concrete example filter string, and a filter-builder deep link with that example embedded in the
  `?filter=` param (see "Filter-builder deep links" in `references/conventions.md`).
- Behavior-only fix on an existing endpoint -> do NOT touch the request's params/body/URL at all -
  the contract didn't change. Only add a traceability note to its `description` (step 5)
  describing the fix.

Write the mutated collection to a new local file (e.g. `/tmp/postman_collection_updated.json`).
Do not touch requests/folders/variables outside the scope of the detected change.

### 5. Add a Jira ticket note

For each new/changed request or folder, or each request affected by a behavior-only fix, set its
Postman `description` field per the format in `references/conventions.md` ("Jira ticket
traceability"): the ticket key + real summary (look it up via
`mcp__plugin_atlassian_atlassian__getJiraIssue`, don't guess), what changed, and a concrete
example demonstrating it - a filter string/request body snippet for contract changes, or a short
before/after behavior description for a fix (e.g. "paginating past a page boundary with tied
`createdAt` timestamps no longer duplicates rows"). Append rather than overwrite if a description
already exists. Do not create per-ticket folders.

This is also the *only* place a filter/sort field change shows up - the field's name, type, an
example filter string, and a filter-builder deep link with that example embedded in the `?filter=`
param (`https://janith-pcty.github.io/filter-expression-builder/?filter=<url-encoded example>`)
live in this description text, never in the request's params array.

### 6. Show the diff and get approval

Summarize in plain language: which folder, which request (new or edited), method + path, and a
short body/param summary. This is a remote-modifying action (org policy) - always get explicit
user approval before the next step, even though running this skill already signals intent to
change something.

### 7. Apply

On approval:

```
python3 ~/.claude/skills/sync-print-platform-postman/scripts/postman.py put --file /tmp/postman_collection_updated.json
```

Then re-`get` and confirm the change landed and nothing else moved. Report what changed to the
user.

## Guardrails

- Never print `POSTMAN_API_KEY`, or any client secret/password found inside fetched
  collections/environments, into chat output.
- `put` replaces the whole collection - always go GET -> mutate a copy -> diff -> approve -> PUT,
  never construct a PUT body from scratch.
- If asked to point this skill at a different collection/workspace, update the defaults in
  `scripts/postman.py` (`DEFAULT_COLLECTION_UID` / `DEFAULT_WORKSPACE_ID`) and
  `references/conventions.md` together so they don't drift.
