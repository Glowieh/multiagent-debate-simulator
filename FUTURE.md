# Future improvements

Tracked ideas that are not urgent but worth doing when the relevant code is next touched.

## Migrate `null_resource` to `terraform_data` in `terraform/api`

**Where:** `terraform/api/lambda.tf` — `null_resource.build_api_proxy` runs `scripts/build-api-proxy.sh` before zipping Lambda packages.

**What to do:**

- Replace `null_resource` with the built-in `terraform_data` resource.
- Rename `triggers` to `triggers_replace` (same file-hash map; this is the direct equivalent of `null_resource.triggers`).
- Add a `moved` block (`from = null_resource.build_api_proxy`, `to = terraform_data.build_api_proxy`) so state migrates in place on Terraform 1.9+.
- Update `depends_on` references in the `archive_file` data sources.
- Remove the `hashicorp/null` provider from `terraform/api/versions.tf` and refresh the lock file.

**Why:**

- HashiCorp recommends `terraform_data` over `null_resource` for trigger + provisioner patterns on Terraform 1.4+; this project already requires Terraform ≥ 1.5.
- One fewer provider to download, pin, and maintain.
- Behavior stays the same: when Lambda source files change, the build script runs again before `archive_file` zips the output.

**Priority:** Low. The current setup works; this is modernization, not a bug fix.

---

## Build Lambda artifacts outside Terraform

**Where:** `terraform/api/lambda.tf` uses a `local-exec` provisioner (via `null_resource` today) to run `scripts/build-api-proxy.sh`, then `archive_file` zips `terraform/api/build/`.

**What to do:**

- Run `scripts/build-api-proxy.sh` (or a `pnpm` wrapper) as an explicit pre-apply step — locally, in CI, or in a deploy script.
- Point Terraform at pre-built zip files (or a fixed `build/` directory) using `filename` / `source_code_hash` on `aws_lambda_function`, without provisioners.
- Update README and deployment docs so the build step is documented separately from `terraform apply`.

**Why:**

- Provisioners are discouraged in Terraform: they run only at apply time, depend on tools being present on the operator's machine (`uv` or `pip`, Python 3.12), and couple infrastructure code to application build logic.
- Plans are more predictable when Terraform reads finished artifacts instead of a directory that may be stale until a provisioner runs.
- Fits common AWS Lambda workflows and makes automated API deploys easier — today only the frontend has a GitHub Actions deploy path; API Lambdas are rebuilt when someone runs `terraform apply` locally.
- Clearer separation of concerns: Terraform manages AWS resources; the build pipeline produces deployable packages.

**Priority:** Medium when API deployment is automated or the team grows. For a solo demo project, the current one-command `terraform apply` workflow is acceptable.

**Note:** The `terraform_data` migration above can be done independently. Moving the build out of Terraform would remove the need for either `null_resource` or `terraform_data` in this stack entirely.
