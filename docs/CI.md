# Checks and CI

What checks a change, where, and why. Setup and commands are in [DEVELOPMENT.md](DEVELOPMENT.md);
the decisions behind this page are ADRs [0002](adr/0002-quality-gates-pre-commit-locally-megalinter-in-ci.md)
to [0006](adr/0006-actions-are-pinned-to-a-commit.md).

## Two layers

- **Locally, pre-commit:** [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) runs on the
  staged files at every commit, and on the whole repository with `make lint` and `make check`.
  Feedback comes before the push, and `make check` is the single command that says a change is
  done.
- **In CI, MegaLinter and the workflows:** MegaLinter runs the same linters, plus scanners that
  need the network or a vulnerability database; the workflows run the tests, the build, the
  bundled firmware check and a daily security scan.

Every linter MegaLinter runs on files offline is also a local hook, so a commit that passes the
hooks passes the same linters in CI.

| Tool                                   | Checks                                                                                  |  Local hook  | CI                                        |
|----------------------------------------|-----------------------------------------------------------------------------------------|:------------:|-------------------------------------------|
| pre-commit-hooks                       | whitespace, end of file, YAML, TOML, large files, merge markers, shebangs, private keys |     yes      |                                           |
| betterleaks, secretlint                | secrets in the repository                                                               |     yes      | MegaLinter                                |
| uv-lock                                | `uv.lock` matches `pyproject.toml`                                                      |     yes      | `uv sync --locked` fails                  |
| Black, isort                           | formatting, import order (Black profile, 100 columns)                                   |     yes      | MegaLinter                                |
| Ruff, Flake8, Pylint                   | lint                                                                                    |     yes      | MegaLinter                                |
| mypy, Pyright                          | types, over `src`, `tests`, `tooling` and `scripts`                                     |     yes      | MegaLinter                                |
| Bandit                                 | security issues in `src/`                                                               |     yes      | MegaLinter, `security.yaml`               |
| shellcheck, shfmt                      | shell scripts: correctness and formatting                                               |     yes      | MegaLinter                                |
| actionlint                             | workflow syntax and expressions                                                         |     yes      | MegaLinter                                |
| zizmor                                 | security of the workflows and `dependabot.yaml`                                         |     yes      | MegaLinter                                |
| markdownlint, markdown-table-formatter | Markdown style and table layout                                                         |     yes      | MegaLinter                                |
| yamllint, prettier, jsonlint           | YAML and JSON syntax and formatting                                                     |     yes      | MegaLinter                                |
| cspell                                 | spelling (project words in `.cspell.json`)                                              |     yes      | MegaLinter                                |
| jscpd                                  | copied code                                                                             |     yes      | MegaLinter                                |
| no-em-dash                             | the em dash character, banned by the coding standards                                   |     yes      |                                           |
| `tooling/sync_agents.py --check`       | agent pointers in sync with `.agents/`                                                  |     yes      |                                           |
| `tooling/check_docs.py`                | relative links in Markdown, ADR numbering and index                                     |     yes      |                                           |
| `tooling/check_commit_msg.py`          | no tool attribution in the commit message                                               |  commit-msg  |                                           |
| pytest                                 | unit tests with the 100% coverage gate                                                  | `make check` | `tests.yaml`                              |
| `uv build`                             | the sdist and wheel build                                                               | `make build` | `tests.yaml`                              |
| `make firmware`                        | the bundled firmware matches a fresh Linux build                                        |              | `firmware.yaml`                           |
| Trivy, Grype, OSV-Scanner, checkov     | vulnerable dependencies, misconfigured workflows                                        |              | MegaLinter; Trivy also in `security.yaml` |
| trufflehog                             | verified secrets                                                                        |              | MegaLinter                                |
| lychee, v8r                            | broken links, files that do not match their JSON schema                                 |              | MegaLinter                                |

Integration tests need a board on `LIVEDUINO_PORT` and run on no hosted runner; see
[DEVELOPMENT.md](DEVELOPMENT.md).

## Every linter blocks

Every active linter fails the build on a finding, formatters included: MegaLinter treats formatter
findings as warnings by default, and [`.mega-linter.yml`](../.mega-linter.yml) turns that off
(`FORMATTERS_DISABLE_ERRORS: false`). A linter that does not fit this repository is disabled there,
with the reason, never left running without blocking: a finding that never fails the build is never
fixed. Each setting in that file has a comment.

## Same settings, and mostly the same versions

**Settings.** When a repository has no config file by the name a linter looks for, MegaLinter uses
its own default (a `.pylintrc`, a `.ruff.toml` with line length 88...), so the same linter would
report different things locally and in CI. To avoid it, `.mega-linter.yml` points the Python
linters at `pyproject.toml`, and the other linters' settings live in the repository:
`.flake8`, `.cspell.json`, `.markdownlint.json`, `.yamllint.yml`, `.secretlintrc.json`,
`.jscpd.json` and `lychee.toml`. Both sides read the same files.

**Versions.**

- The **Python linters** are ordinary development dependencies: unpinned in `pyproject.toml`,
  locked in `uv.lock`, updated by Dependabot. They can differ from the versions in the MegaLinter
  image, and while they do, a Python linter can disagree between the hooks and CI.
- The **other hooks** must name a version anyway, so they name the image's: in
  `additional_dependencies` for the Node.js and Go packages, as `rev` for betterleaks, actionlint,
  shellcheck and zizmor. pre-commit installs the Node.js and Go runtimes they need.

**Bumping MegaLinter**, usually a Dependabot pull request: read the versions in the new image's
Dockerfile (`flavors/python/Dockerfile` in the MegaLinter repository, at the new commit), update
the non-Python hooks in `.pre-commit-config.yaml` to match, run `make check`, fix what the new
versions report, and push it all in the same pull request. Nothing checks this automatically.

## What a pull request checks

A pull request checks what it changes; a push to `main` checks everything.

- **MegaLinter** lints only the files that differ from `main` (`git diff origin/main...`). The
  checkout fetches the whole history, which that diff needs.
- **Exception:** a pull request that changes a linter's settings (`.mega-linter.yml`,
  `.pre-commit-config.yaml`, `pyproject.toml` or any of the config files above, or
  `code-quality.yaml`) lints everything. Otherwise a stricter rule would be checked against the
  config file alone, pass, and then fail on `main`.
- **Scanners always see everything.** Trivy, Grype, OSV-Scanner, Syft, betterleaks, secretlint,
  trufflehog, checkov and jscpd scan the whole repository by design.
- **Tests** run in full whenever they run, because a change in one module can break another.
  Pull requests that touch none of `src/`, `tests/`, `scripts/`, `pyproject.toml`, `uv.lock`,
  `.python-version`, `README.md`, `LICENSE` or `tests.yaml` skip them; `main` always runs them.
  A first job, `changes`, makes that call, so the check reports as skipped instead of pending.
- **Firmware** runs only when boards, the bundled firmware or its build script change.
- **Locally**, the hooks check the staged files, but mypy, Pyright, Pylint and Bandit check the
  whole project whenever a Python file changes.

The cost: a pull request can pass and `main` fail, on a check that spans files or on a file the
pull request did not touch; the fix goes in the next pull request.

## Workflows

| Workflow            | Runs on                                                              | Jobs                                                                                                              |
|---------------------|----------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| `tests.yaml`        | push to `main`; PRs that touch the code, tests, scripts or packaging | unit tests with the 100% coverage gate, then `uv build`                                                           |
| `code-quality.yaml` | push and PR to `main`                                                | MegaLinter (Python flavor): the changed files on PRs, everything on `main` and on PRs that change linter settings |
| `security.yaml`     | push and PR to `main`, daily                                         | Trivy (results in the Security tab, except from PRs) and Bandit (report in the job summary); neither blocks       |
| `firmware.yaml`     | push and PR to `main` that touch boards or firmware; manual          | `verify`: the bundle matches a fresh build; `regenerate` (manual): rebuild on Linux and open a PR                 |
| `publish.yaml`      | a published GitHub release; manual                                   | render the PyPI README, build, publish to PyPI with trusted publishing                                            |
| `todo.yaml`         | push to `main`                                                       | turns `TODO` and `FIXME` comments in code into issues                                                             |

Every workflow starts with no permissions (`permissions: {}`), and each job asks for what it
needs. `make actions ls` lists them and `make actions workflow-<name>` triggers one.

## Actions are pinned to a commit

Every `uses:` names a commit SHA, with the version in a comment:

```yaml
uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
```

A tag such as `v7.0.1` is a label its owner, or anyone with the owner's credentials, can move to
other code; a major tag such as `v7` moves on purpose with every release. Either way, the workflow
would run new code with no change in this repository. A SHA is the hash of the code itself and
cannot point anywhere else. It matters most in `publish.yaml`, which can upload to PyPI.

- zizmor enforces the pins, as a local hook and in MegaLinter.
- Dependabot updates the actions monthly, for releases at least 14 days old, moving the SHA and
  the comment together.
- A tool an action downloads is pinned too when the action allows it: `security.yaml` sets the
  Trivy binary's version.
- Checkouts drop their credentials (`persist-credentials: false`), and the publish job restores
  no cache.
- Still open: the MegaLinter action pulls its Docker image by tag (`TODO.md`).
