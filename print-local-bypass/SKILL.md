---
name: print-local-bypass
description: Restore local dev-only working-tree changes in the distributionprintplatformapi repo that stub out the Address API and point launchSettings.json at QA. Use when the user runs /print-local-bypass or asks to bring back their local address-stub/dev setup after a fresh clone, stash, or checkout.
---

# Restore local Address API bypass for dev

Repopulates three uncommitted, dev-only files in `distributionprintplatformapi` that let the
API run locally without hitting the real Address API:

1. `DistributionPrintPlatformApi/src/App/DistributionPrintPlatformApi/Infrastructure/AddressApi/AddressDependencyResolution.cs`
   - modified: registers `StubAddressHttpClient` when `address_api_use_stub` config is true
2. `DistributionPrintPlatformApi/src/App/DistributionPrintPlatformApi/Infrastructure/AddressApi/StubAddressHttpClient.cs`
   - new file: stub `IAddressHttpClient` returning a fixed Schaumburg, IL address
3. `DistributionPrintPlatformApi/src/App/DistributionPrintPlatformApi/Properties/launchSettings.json`
   - modified: points `idp_authority_url`/`security_resource_api_url`/`address_api_base_url` at
     the `tin*.qa.paylocity.com` environment, sets `address_api_use_stub: true` for Kestrel, and
     carries local secret values (`idp_client_secret`, `gateway_api_key`) for that QA environment

These are never meant to be committed — do not `git add` or commit them as part of this skill.

## What NOT to touch

Ignore any other uncommitted changes in the repo (e.g. SQL migration scripts under
`DatabaseMigrations/**/Scripts/`, or a stray `.sln` file). Only touch the three files above.

## Workflow

1. Find the repo root: `git -C <cwd> rev-parse --show-toplevel` (must be the
   `distributionprintplatformapi` repo — if not, tell the user this skill only applies there).
2. Copy the reference files from this skill's `files/` directory over the corresponding repo
   paths, overwriting whatever is currently there:
   - `files/AddressDependencyResolution.cs` -> `DistributionPrintPlatformApi/src/App/DistributionPrintPlatformApi/Infrastructure/AddressApi/AddressDependencyResolution.cs`
   - `files/StubAddressHttpClient.cs` -> `DistributionPrintPlatformApi/src/App/DistributionPrintPlatformApi/Infrastructure/AddressApi/StubAddressHttpClient.cs`
   - `files/launchSettings.json` -> `DistributionPrintPlatformApi/src/App/DistributionPrintPlatformApi/Properties/launchSettings.json`
3. Run `git status` (and optionally `git diff` on the two modified files) in the repo to confirm
   only those three files changed, then report to the user which files were written/created.

No approval is needed to overwrite these three files — restoring them is the whole point of the
skill. Do not stage or commit them.
