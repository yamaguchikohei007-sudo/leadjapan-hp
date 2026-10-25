# Lead Japan HP — agent instructions

## Project context

- `README.md` describes the intended architecture and publishing workflow. Read the relevant sections before judging a change; treat PR descriptions as claims to verify against the code.
- `build.py` and `sitegen/` generate the public static site using the Python standard library. Django dependencies belong to the separate local CMS in `cms/` and `requirements-admin.txt`.
- `functions/` contains Cloudflare Pages Functions. `bonus/` contains the reader-bonus source and download logic. Server-side JavaScript is intentional here.
- The CMS is intended to run on loopback only. Check changes to that boundary; do not assume it is an internet-hosted Django deployment.

## Code Review Rules

### Evidence and scope

- Review the PR's actual base/head diff. Trace changed behavior through callers, URL configuration, templates, export/build steps and relevant tests; unchanged surrounding code may explain a defect introduced by the diff.
- Report actionable defects introduced by the PR, with the triggering condition, observable impact, and a precise changed-file location. Cite the supporting code or test result. Do not invent vulnerabilities or present checklist items as confirmed findings.
- Separate defects introduced by this PR from failures already present on the base branch. If a test fails, compare the relevant base behavior when feasible; otherwise say attribution is unverified. Never recommend deleting a security assertion merely to make CI pass.
- Prioritize broken behavior, authorization bypass, data exposure and data loss. Avoid style preferences, speculative hardening requests and repeating the same root cause across comments.
- Write findings in concise Japanese. Use severity proportional to the demonstrated impact and state any assumptions. If no actionable issue is found, do not manufacture findings or describe the result as proof of security.

### CMS authorization and private content

- For changes in `cms/`, follow the complete URL-to-view/admin-action path. Check anonymous users, non-staff users, staff without article permissions, viewers, and publishing users as applicable.
- Preview and private-media access require staff status plus article-view permission. Publishing requires article-change permission. A hidden button does not replace server-side checks.
- Check effective routes and their ordering, including aliases. Tests must exercise routes that actually resolve to the protected view: a 404 alone does not prove authorization. If an old route is intentionally removed, verify the active route remains protected and test removal separately.
- Changes to publishing must preserve CSRF validation and prevent state changes through GET. Private previews/media must not leak through shared caching or public build/export output.
- Check Markdown/HTML handling and URL validation across CMS input, JSON export and public rendering. Look for untrusted HTML or dangerous URL schemes reaching a browser without the intended sanitization.
- Check image export for unintended disclosure of original/private files, metadata, or paths outside the intended directories. Verify that draft articles and their images do not become public merely because a build runs.

### Public functions and build output

- For reader-bonus changes, trace form submission through the Pages Function and `bonus/download.js`. Verify that invalid input/passwords cannot return the protected payload and that no public static path bypasses the check.
- Reader passwords, tokens and private keys must not enter public assets, logs or review comments. Distinguish real secrets from hashes and documented local-development defaults; assess the actual exposure path.
- Check cache isolation on personalized responses and protected downloads. `noindex` and an obscure URL are not access controls.
- Inspect changes to `build.py`, generated `_routes.json`, redirects and copied assets together. Verify that private content stays outside public output and that intended public routes still work.

### Publishing and regression checks

- For CMS publishing changes, verify that only published content and intended image paths are committed, failed tests stop publishing, concurrent updates are not silently overwritten, and the user's checkout is preserved. Publication must remain a reviewed PR workflow rather than an automatic merge/deploy.
- For site changes, check the source-to-generated-output path, escaping, links and page metadata when affected. For bonus-tool source changes, check that the generated module stays consistent with its source.
- Inspect relevant CI results for the reviewed commit. Run targeted tests when the review environment supports them; never claim a test or browser check ran if it did not. Missing dependencies or inaccessible production settings are verification limits, not proof of a defect.
- Available test entry points (use those relevant to the diff):
  - Static site: `python3 -m unittest discover -s tests -v`
  - CMS, with `requirements-admin.txt` installed: `python3 cms/manage.py test press -v 2`
  - Visitor pin: `node --test tests/js/visitor_pin.test.mjs`
- For changes to dependencies or externally defined security behavior, check current official advisories/documentation when available. Do not rely on an unverified IOC/CVE list or infer deployed MFA, audit logging or cloud permissions from repository code alone.

## Review boundaries

Review is read-only unless the user separately authorizes changes. Do not run real CMS publishing, push branches, post external reports, merge, deploy, rotate credentials or probe a live service as part of a review without authorization. Use synthetic fixtures and redact sensitive evidence.
