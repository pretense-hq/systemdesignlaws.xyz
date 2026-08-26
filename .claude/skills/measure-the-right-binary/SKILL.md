---
name: measure-the-right-binary
description: Confirm the command you measured with is the command that actually runs. Use before trusting any shell-based gate, grep result, exit code, or "all green" report. Trigger on "the gate says green", "works in my shell but not in CI", "grep returns nothing", "exit code differs", "shim", "alias", "which grep", "why does the script disagree with me".
---

# `grep` may not be grep

An entire round of gate testing reported **all 8 seeds GREEN**. Every one was an artifact of the
wrong binary. `command grep` immediately turned **7 of 8 RED**.

## What happened

In the interactive shell, `grep` was a **shell function** wrapping **ugrep 7.8.4**. The gate used
`grep -q -v` to assert absence. The two engines disagree on exactly that combination:

| Invocation | real GNU/BSD grep | ugrep 7.8.4 |
|---|---|---|
| `grep -q -v PATTERN file` (pattern present on every line) | rc **0** | rc **1** |

The gate read `rc != 0` as "clean". So the seeded P0 violations — which were present, and which
the test suite caught — reported green through the gate. The bug was not in the patterns, the
seeds, the document, or the logic. It was in **which program ran**.

## Diagnose in three commands, before trusting any measurement

```bash
type -a grep        # function? alias? builtin? which files?
command -v grep     # the resolved external binary, ignoring functions/aliases
grep --version | head -1   # and: command grep --version | head -1  -- compare them
```
`type -a` is the one that matters. `which` misses shell functions entirely on some shells, which
is precisely how this survived.

```
$ type -a grep
grep is a function
grep is /opt/homebrew/bin/grep
$ command grep --version | head -1
grep (BSD grep, GNU compatible) 2.6.0-FreeBSD
```
Two different programs, and the function wins in your shell.

## Always measure through `command`

```bash
command grep -qE "$pat" "$f"       # bypasses functions and aliases
\grep -qE "$pat" "$f"              # backslash also bypasses aliases (not functions)
env -i PATH=/usr/bin:/bin grep ... # nuclear: clean environment
```
In a script, set it once and use the variable everywhere:

```bash
GREP="$(command -v grep)"
"$GREP" -qE "$pat" "$f"
```
## The asymmetry that makes this invisible

**A script run via `#!/usr/bin/env bash` does NOT inherit interactive shell functions.**

That is the second half of the trap, and it cuts the opposite way:

| | your interactive test | the gate script |
|---|---|---|
| `grep` resolves to | the **function** → ugrep | the **binary** → GNU grep |

So the tool under test and your test of it can use **different binaries**, and the two will
disagree exactly when it matters. Reproducing a gate failure by hand can fail to reproduce, and
"it works when I run it" is then evidence of nothing.

Non-interactive shells skip `~/.bashrc`/`~/.zshrc` unless `BASH_ENV`/`ZDOTDIR` says otherwise —
so also check those before concluding a script is clean.

## Generalise: this applies to any measured command

Before trusting **any** measurement, check for a shim:

| Command | Common shim | Consequence of missing it |
|---|---|---|
| `grep` | ugrep, ripgrep alias | exit-code inversion, as above |
| `npm` | `tools/npm/npm-aws` wrapper (this repo) | auth against the wrong token |
| `python` | pyenv/asdf shim | different interpreter than CI |
| `node` | nvm shim, `.nvmrc` mismatch | different runtime than production |
| `sed` `date` `readlink` | GNU coreutils via `g`-prefix or PATH | silently different flag semantics |
| `git` | wrapper injecting config | different `core.bare`, different index |

## Rule

**A green produced by an unverified binary is not a measurement.** Add the binary identity to the
gate's own output, so the next reader can see it without re-deriving it:

```bash
echo "gate using: $(command -v grep) $(command grep --version | head -1)"
```
This costs one line and would have saved the entire round of testing above. It also composes with
[[false-green-hunt]] arm 2: when you delete the feature and the check stays green, **suspect the
binary before the logic**.

Related: [[shared-pattern-source]] — the same gate was ALSO carrying a divergent copy of the
pattern list, so it had two independent reasons to be wrong at once. Fixing one would have left a
green that still proved nothing.

## Self-test
Seed the exact defect this skill describes into a fixture, confirm the check reports it,
then remove the check and confirm the fixture now passes. A check never seen to fail is
not evidence.
