# Fixtures

Two manifests and a self-test. Vendor names are deliberately fictional (`vendor-large-…`,
`other-vendor-medium-…`) so the fixtures never imply a recommendation and never rot when a
real naming scheme changes.

- **`models.good.json`** — three components that can survive a model release: pinned to an
  exact artifact, each with a frozen probe set, none self-upgrading, runtime recorded (one
  explicitly `null`, which is a decision rather than an omission). Passes with and without
  `--strict`.

- **`models.bad.json`** — six components, nothing malformed. Each is the kind of declaration
  a real system ships, and each carries `_fails_because` explaining the failure in plain
  terms so the fixture's intent stays auditable:

  | id | what it demonstrates |
  |---|---|
  | `floating-alias` | the obvious one — an identifier containing `latest` |
  | `alias-drift` | the one that survives review — looks specific, still resolves to newest in its family |
  | `no-probes` | pinned with nothing to compare against when the pin finally moves |
  | `auto-upgrade` | pinned and probed, then configured to move its own pin |
  | `runtime-omitted` | model pinned, toolchain floating — half a pin |
  | `score-only` | structurally perfect; fails only under `--strict`, which is the point |

  Five violations by default, six under `--strict`.

- **`selftest.sh`** — 14 assertions: both fixtures at both strictness levels, each failure
  mode named individually, proof that a clean component is not blamed for its neighbours,
  and three fail-loud cases (missing file, empty component list, malformed JSON).

```sh
sh selftest.sh
```

An empty `components` list exits 2 rather than 0 on purpose: a manifest that pins nothing
must not be able to report success.
