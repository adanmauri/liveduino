---
name: write-issue
description: Create or update a GitHub issue for liveduino (adanmauri/liveduino) with a clear report and hardware/environment context ($ARGUMENTS optional title, context, or issue number/URL).
---

# Write GitHub Issue

Create a GitHub issue in **adanmauri/liveduino** (PyPI package `liveduino`).
$ARGUMENTS is optional: a title hint, a bug/feature description, or an existing
issue number/URL to **update** (not create a duplicate).

## When to use

The user wants a **new GitHub issue** filed (bug, enhancement, or docs) before
or instead of coding, or wants to update an existing one.

## Steps

1. **Existing issue?** If $ARGUMENTS is `#42` or an issue URL, fetch it with
   GitHub MCP (`user-github`) or `gh issue view`, and use `gh issue edit` only
   when the user asked to update — never create a duplicate.

2. **Classify the issue** and shape the body accordingly:
   - **bug** — what happened vs. expected, minimal repro, traceback, the
     `liveduino.exceptions` type raised (if any).
   - **enhancement** — motivation, proposed API (keep Arduino/Wiring fidelity),
     alternatives.
   - **documentation** — which doc (`README.md`, `docs/ARCHITECTURE.md`,
     `firmware/*/README.md`) and what is missing or wrong.

3. **Gather environment context** for bugs that touch hardware/connection. Run
   (or ask the user to run) with the board connected:

   ```bash
   python --version
   uv run python -c "import importlib.metadata as m; print('liveduino', m.version('liveduino'))"
   uv run python -c "import serial; print('pyserial', serial.__version__)"
   uname -srm                       # host OS/arch (use 'sw_vers' on macOS)
   ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || ls /dev/tty.*   # serial ports
   ```

   Also note, when relevant:
   - **Board**: model and `id` (e.g. `arduino:uno`, `arduino:nano`).
   - **Connection**: driver (`SerialDriver` / `TcpDriver` / `BluetoothDriver`),
     port or host:port / MAC, and baud rate.
   - **Firmware**: StandardFirmata variant and version flashed on the board.

4. **Pick a title** — short, action-oriented (from $ARGUMENTS or conversation),
   e.g. `analogRead returns stale value on Nano over TCP`.

5. **Fill the [issue template](./template)** — keep the **Environment** table for
   hardware/connection bugs; drop it for docs-only or pure host-logic issues.
   Write the filled body to a scratch file that is gitignored (`issue-draft.tmp`).

6. **Create the issue**

   ```bash
   gh issue create \
     --title "<title>" \
     --body-file issue-draft.tmp \
     --label "<bug|enhancement|documentation>"
   ```

   Or GitHub MCP (`user-github`) with the same title and body. Use `--label`
   only when the label already exists in the repo.

7. **Return the issue URL** to the user.

## Rules

- Do not commit the draft (`issue-draft.tmp` is matched by `*.tmp` in `.gitignore`).
- Never paste secrets, tokens, or full device paths that reveal sensitive setup.
- Keep the report concrete and minimal; prefer a small repro snippet over logs.
- Preserve Arduino/Wiring API fidelity when proposing API changes.
