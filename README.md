# arc-prize-2026-tools

Open-source utilities I built while competing in the **[ARC Prize 2026 — ARC-AGI-2](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2)** Kaggle competition (abstract visual reasoning).

These are general-purpose engineering tools — not a solution writeup. They're the kind of plumbing you end up needing when working with Kaggle's API and building ARC program-synthesis experiments.

## Contents

### `kaggle_bearer.py` — Kaggle API client for the new `KGAT_` tokens
Kaggle's newer API tokens are `KGAT_`-prefixed and authenticate via an
`Authorization: Bearer <token>` header — **not** the legacy Basic auth that
`kaggle.json` + the official `kaggle` CLI use. The result: the CLI silently
returns `401` on a valid new-style token, which is confusing to debug.

This is a tiny dependency-free client (stdlib only) that speaks Bearer auth, so you
can check auth and download datasets / competition data with a `KGAT_` token:

```bash
python3 kaggle_bearer.py whoami
python3 kaggle_bearer.py comp-files <competition-slug>
python3 kaggle_bearer.py dataset <owner>/<dataset-slug> ./out
python3 kaggle_bearer.py comp-download <competition-slug> ./comp_data
```

It reads the token from `~/.kaggle/kaggle.json` (the `"key"` field) — **no secrets are stored in this repo.**

### `_poll_kernel.py` — Kaggle notebook (kernel) run-status poller
Polls a Kaggle kernel's run status until it reaches a terminal state
(`complete` / `error` / `cancelled`), printing transitions. Handy for waiting on
a long commit/run from a script instead of refreshing the web UI.

```bash
python3 _poll_kernel.py <user_name> <kernel_slug>
```

### `arc_dsl.py` — a small ARC Domain-Specific Language
A library of ~35 pure grid primitives (perception, color, geometry, object ops)
for building program-synthesis solvers over [ARC](https://arcprize.org/) grids.
Grids are `list[list[int]]` (values 0–9); every function returns a new grid and
never mutates in place.

## License
[MIT](LICENSE)
