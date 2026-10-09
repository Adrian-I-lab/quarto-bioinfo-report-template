# Run the style checks and fix what they flag

Use this prompt when the checks fail, or before you hand a book to a reviewer.

## Prompt

```text
You are working in a Quarto report book built from the house template. Read AGENTS.md first.

1. Run bash scripts/check_style.sh and save its table as the "before" table.
2. For each failure, read the line it names and fix the content:
   - register: rewrite the sentence descriptively, or move it to the synthesis chapter. Add a register-ok comment with a reason only if the sentence must stay as it is, and list each one in your report.
   - absence: add the equivalence result or the detection floor to the same paragraph, or rewrite the claim.
   - prose: replace em dashes and spaced en dashes; remove filler phrases; use Australian spelling.
   - captions: add the missing caption, alt text, or full stop; rename duplicate labels.
   - synthesis: add the missing section or the missing Evidence or Why it could be wrong.
3. Never edit tools/style/ or style-checks.toml to make content pass.
4. Run bash scripts/check_style.sh again and save the "after" table.

Report both tables, each fix with its file and line, and every register-ok comment you added with its reason.
```

## Done checks

- `bash scripts/check_style.sh` exits 0.
- `git diff --stat -- tools/style style-checks.toml` prints nothing.
- Every added `register-ok` comment carries a reason, and is listed in the report.
