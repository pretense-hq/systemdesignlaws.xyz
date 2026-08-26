---
name: jira-evidence
description: Update Jira with measured evidence, resolve stale tickets, and avoid duplicates. Trigger on "update jira", "file a ticket", "close the ticket", "is there a ticket for".
---

# Measure before you write; search before you create

## Always

1. **Search first.** A 78-PR backlog usually already has the ticket. Comment on it rather than adding a duplicate. If two tickets describe the same defect, say so and let a human pick the canonical one — do not merge them yourself.
2. **Re-measure every figure.** Tickets go stale. Two of three findings on one ticket here were already resolved; saying so is more valuable than restating them.
3. **Sign the comment.** The MCP posts as the account owner, not a bot. An unsigned agent comment reads as if a person wrote it.
4. **Never transition status.** Whether acceptance criteria are met is a judgement belonging to whoever owns the ticket.

## Structure a comment as

What was re-measured, with the command or query · what is now resolved · what is still open and whether it got **worse** · suggested disposition (close / re-scope / fold into another ticket) · anything surfaced while measuring.

## Watch for a recorded decision you are about to contradict

A ticket may hold a founder decision. If your recommendation argues against one, **stop recommending it** and instead surface the consequence nobody connected. Example: "local is the perimeter permanently" resolves *verification* but not *provenance* — signing cannot follow the work local.
