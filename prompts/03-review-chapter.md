# Review a chapter

Use this prompt to review one chapter against the house style. The reviewer proposes edits. It does not rewrite.

## Prompt

```text
You are reviewing one chapter of a Quarto report book built from the house template. Read AGENTS.md and STYLE-GUIDE.md first.

Review {{chapter file}} against STYLE-GUIDE.md, section by section. Run bash scripts/check_style.sh first and include its findings.

Output one table with these columns: rule (the style guide section), line, finding, proposed fix.
Group the rows in two parts:
1. Measurement problems: a number typed instead of computed, a missing denominator, a threshold not read from _params.yml, a caption that does not match its figure, an absence claim without its detection floor.
2. Register problems: interpretation in a descriptive chapter, a missing "How to read this" note, a missing draft-question answer.

Do not edit the chapter. Propose each change, so the author decides.
End with: the check_style.sh table, and a list of the things you could not check (see "What the checks cannot catch" in AGENTS.md).
```

## Done checks

- The review is a table with rule, line, finding, and proposed fix.
- Measurement problems and register problems are listed apart.
- The chapter file is unchanged (`git diff --quiet -- {{chapter file}}` exits 0).
