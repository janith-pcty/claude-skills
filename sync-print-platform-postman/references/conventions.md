# Conventions for syncing DistributionPrintPlatformApi -> Postman

## Targets

- Repo: `distributionprintplatformapi` (ASP.NET Core 8, vertical slice).
- Postman collection: **Print Platform** in workspace **My PHNX workspace**.
  - Collection uid: `40050308-e1f5d5cf-3cd0-4503-a01d-1aa10284db29`
  - Workspace id: `48b6d1c0-fe04-4a95-b13d-b745ff2cf18b`
  - These are the defaults baked into `scripts/postman.py`; override with `--uid`/`--workspace` if the target ever changes.
- The original team collection **Print Job** (in the *Tax - Validation & Discovery* team workspace) has the full historical set of requests and is a good reference for naming/structure, but is **not** the sync target - the API key used here does not have write access to that team workspace.

## Where things live in the repo

- Controllers: `DistributionPrintPlatformApi/src/App/DistributionPrintPlatformApi/Features/**/*Controller.cs`
  - Attribute-routed: `[HttpGet]`/`[HttpPost]`/`[HttpPatch]`/`[HttpDelete]` + `[Route("distribution/v{n}/...")]`.
  - Params via `[FromBody]` (request body type), `[FromQuery]` (query envelope type), `[FromRoute]` (path segment).
- Filterable/sortable fields: on the response DTO via `[Filterable]`/`[Sortable]`/`[Aggregatable]`/`[AggregateGroup]` attributes (namespace `Paylocity.Apis.Server.Filtering.Attributes`), paired with an `ISqlFilterConfigurationProfile` that maps each field with `.AddField(x => x.Prop, "sql_column", ...)`. Example pair:
  - `Features/PrintJobs/V1/GetAll/Models/PrintJobDto.cs` <-> `Features/PrintJobs/V1/GetAll/FilterProfile/PrintJobsFilterProfile.cs`
  - A new filter = a new `[Filterable]`/`[Sortable]` property + a matching `AddField(...)` line. It is **not** a new query parameter - the field becomes usable inside the existing `Filter`/`Sort` string envelope.
- OpenAPI spec (authoritative schema source): `.openapi/DistributionPrintPlatformApi.json` (OpenAPI 3.0.1). Committed to the repo, kept in sync by both a TeamCity automated job ("Automated PR: Syncing OAS Data") and manual developer edits under Jira tickets. Treat it as current as of the latest commit touching it.

### Spec caveats to handle

- **Query-key casing is inconsistent across endpoints.** e.g. `printJobs` uses `Filter`/`Sort`/`Limit`/`NextCursor`/`IncludeTotalCount` (PascalCase); `printCenters` uses `filter`/`includeTotalCount` (camelCase) alongside PascalCase `NextCursor`/`Limit`/`Sort`. Always read the exact key casing from the spec for the specific operation - don't assume one convention.
- **`deprecated: true` params** (e.g. `DistributionCenterName`, `PrinterType` on printCenters) - skip these when building new examples; don't propose new requests that rely on them.
- **`x-in_development` extension** - marks endpoints only available in Sandbox-Dev/Tin environments (not Bronze/DrProd/Cobalt). Flag this to the user when proposing a request for such an endpoint so they pick the right Postman environment.
- **v1 vs v2** - `POST /distribution/v1/printJobs` (`CreatePrintJobRequestV1`) and `POST /distribution/v2/printJobs` (`CreatePrintJobRequestV2`) both exist. Match on the exact path + version, never assume "the" create-print-job endpoint.
- The automated OAS-sync commits can churn formatting/ordering without semantic changes - when diffing the spec file across commits, compare parsed JSON structure (paths/operations/schemas), not raw text lines.

## Postman request conventions (match these when building new requests)

Derived from existing requests in the `Print Job` / `Print Platform` collections:

- Base URL: `https://{{rootUri}}/...` (a Postman variable, resolved per-environment).
- Path parameters become Postman variables: `{{jobId}}`, `{{shipment_id}}`, `{{fileId}}`, etc. - lowerCamel or snake_case matching whatever the existing sibling requests use for that resource.
- Auth: omit an explicit `auth` block on new requests so they **inherit** the collection-level bearer auth (`{{accessToken}}`), unless the endpoint genuinely needs different credentials.
- List/filterable endpoints (GET with `Filter`/`Sort`/etc.): include the full query-param envelope for that operation as **disabled** example entries, e.g.:
  ```json
  {"key": "filter", "value": "status eq 'Queued'", "disabled": true},
  {"key": "limit", "value": "10"},
  {"key": "sort", "value": "updatedAt:desc", "disabled": true},
  {"key": "nextCursor", "value": "<uuid>", "disabled": true},
  {"key": "includeTotalCount", "value": "true"}
  ```
  Key casing must match the spec for that specific operation (see caveat above). This full-envelope
  build only happens **once**, when the request is first created for a brand-new endpoint - it does
  not apply to filter/sort fields added later to an already-existing request (see below).
- **Any request that has a `filter` query param must link the filter builder at the very top of its description**, above the Jira ticket notes:
  ```
  Building a combined filter? Use the [Filter Expression Builder](https://janith-pcty.github.io/filter-expression-builder/) to compose AND/OR filter strings, then paste the result into the `filter` param below.

  ---

  <rest of description / Jira notes follow>
  ```
  Only add this to requests with an actual `filter` param - not to PATCH/POST requests that don't use the filter DSL.
- **Filter-builder deep links: embed the example filter in the URL.** The builder accepts a
  `?filter=<expression>` query param and parses it back into editable conditions on load (see
  [[filter-builder-url-param]]). Whenever you document a concrete filter example - the generic
  link above is fine bare, but **any example filter string you write for a specific field must be
  accompanied by a deep link with that string embedded** so the reader can open the builder
  pre-populated instead of retyping it. Build the link as
  `https://janith-pcty.github.io/filter-expression-builder/?filter=<URL-encoded expression>`:
  - URL-encode the expression (spaces -> `%20`, `'` may stay literal). The builder decodes both
    `%20` and `+` for spaces, so either works.
  - Example: `taxCode eq '123'` -> `https://janith-pcty.github.io/filter-expression-builder/?filter=taxCode%20eq%20'123'`
  - For a multi-condition example, embed the whole combined string, e.g.
    `status eq 'Queued' AND retries gt 3` ->
    `.../?filter=status%20eq%20'Queued'%20AND%20retries%20gt%203`
- **New or changed filter field on an existing list endpoint** -> do not create a new request, and
  do not touch the params array at all - not even the disabled `filter`/`sort` example values.
  Leave those exactly as they were. Document the field purely in the request's `description`
  instead (see "Jira ticket traceability" below): name, type, a concrete example filter string
  (e.g. `taxCode eq '123'`), **and a filter-builder deep link with that example embedded in the
  `?filter=` param** (see "Filter-builder deep links" above) so the field's example is one click
  away from an editable builder. The API only ever exposes one generic `Filter`/`Sort` string param
  (per-field query params were tried and explicitly reverted - see [[filter-consolidation]]), so
  the params list for a list endpoint should stay fixed once built; only the docs grow.
- Request bodies: `mode: raw`, `options.raw.language: json`, pretty-printed JSON built from the spec's example/schema for that request type.
- **Every request needs an explicit `X-Pcty-Api-Key: {{printjob_api_key}}` header**, in addition to the inherited collection bearer auth. This is a gateway-level key separate from the OAuth token - every real request in the source `Print Job` collection carries it, and omitting it produces a 403 even with a valid `{{accessToken}}` (confirmed the hard way: the first `Get Print Jobs` request built for this collection was missing it and 403'd until this header was added). Never build a new request without it.
- Feature -> existing folder name mapping (top-level items in the collection):

  | Feature area | Postman folder |
  |---|---|
  | Print Jobs (create/get/update/aggregations) | `Print Job` |
  | Shipments | `Shipment` |
  | Print Centers | `Print Centers` |
  | Files | `FileAccess` |
  | Outbox | `Outbox` |
  | Address | `AddressApi` |
  | Health checks | `Health` |

  If a genuinely new feature area appears with no matching folder, create a new top-level folder named after the feature (title case) rather than forcing it into an existing one.

## Jira ticket traceability

Every request/folder that's added or changed because of a specific ticket should get a short note
in its Postman **description** field (not a new folder-per-ticket - that's the clutter pattern
seen in the old `Print Job` collection, e.g. stray `TDV-1325`/`TDV-1627` folders, and it's exactly
what this convention exists to avoid).

- Derive the ticket key from the branch name (e.g. `fix/tui-1107-...` / `feat/tui-1107-...` ->
  `TUI-1107`) or ask the user if it's ambiguous.
- Look up the ticket via `mcp__plugin_atlassian_atlassian__getJiraIssue` (cloudId
  `paylocity.atlassian.net`) to get its real summary - don't guess at the title.
- Format (Markdown, goes in the request/folder's `description` field):
  ```
  **<TICKET-KEY>** - <one-line summary from Jira>

  <what changed on this request/endpoint, one line>

  Example:
  <a concrete filter string, or request body snippet, demonstrating the change>

  https://paylocity.atlassian.net/browse/<TICKET-KEY>
  ```
  When the change is a **new/changed filter field**, the "Example:" line must be a concrete filter
  string *plus* a filter-builder deep link with that string embedded, e.g.:
  ```
  Example: `taxCode eq '123'` - [open in builder](https://janith-pcty.github.io/filter-expression-builder/?filter=taxCode%20eq%20'123')
  ```
  When the change is a **behavior-only fix** (bug fix, perf fix - no contract change), the
  "Example:" line is a one-line before/after description of the behavior, not a filter string or
  body snippet, e.g.:
  ```
  **TUI-1124** - Fix cursor pagination duplicate rows

  Fixed keyset pagination on this endpoint to use a strict, uniquely-tiebroken cursor comparison.

  Example: paginating past a page boundary where multiple rows share the same `createdAt` timestamp
  no longer returns those tied rows twice (or skips them) on the next page.

  https://paylocity.atlassian.net/browse/TUI-1124
  ```
  Don't add a filter-builder link for a behavior-only fix unless the fix specifically changed
  filter/sort evaluation.
- Only touch the `description` field - never let this bleed into renaming requests/folders or
  restructuring the collection.
- If a request already has a description from a prior ticket, append a new dated entry rather
  than overwriting the existing note, so the request accumulates a small changelog over time.

## Workflow safety rules

1. Never print `POSTMAN_API_KEY` or any raw secret value (client secrets, passwords) pulled from environments/collections into chat output. Use the `whoami` subcommand to sanity check auth instead of dumping headers.
2. The Postman `PUT /collections/{uid}` endpoint replaces the **entire** collection body. Always: `get` the current collection -> mutate a local copy -> show the user a summary diff -> get explicit approval -> `put`. Never construct a PUT body from scratch.
3. Treat this as a remote-modifying action requiring the user's explicit approval before every `put` call (org policy), even though invoking the skill itself is implicit intent to change something - the specific request/folder being added still needs a look before it goes live, since a bad build could clobber teammates' saved examples.
4. If `.openapi/DistributionPrintPlatformApi.json` hasn't been updated yet for a code change you detected, say so and offer to build the Postman request from the C# controller/DTOs directly instead - don't silently guess at the spec.
