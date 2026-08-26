---
name: revenue-path-integrity
description: Assert the terminal state of a money path, never the intermediate handshake. Use when writing or reviewing anything that takes payment, provisions an entitlement, or reports success to a customer. Trigger on "checkout", "payment", "billing", "subscription", "did it charge", "purchase flow", "upgrade flow", "is this tested", "why did nobody pay".
---

# Assert the terminal state, never the intermediate one

Every money path has a handshake in the middle and an outcome at the end. The handshake is
easy to observe, easy to mock, and proves nothing. Only the terminal state is revenue.

**Evidence:** nine live subscriptions expired unpaid across four months, every one of them
with **no payment method attached**. The suite was green throughout. Every test asserted the
intermediate step — that creation returned a client secret — and not one asserted that a
subscription ever reached a state in which money moved. The gap was not a missing test. It was
a suite full of tests aimed one step short of the answer.

## Terminal is a conjunction, never a status

A single status field is never enough. A money path is complete only when **all** of these
hold at once, and each one alone is a distinct failure mode:

| Half | Missing it looks like | What actually happens |
|---|---|---|
| status is a settled one | pending forever | expires unpaid |
| an instrument is attached | first charge succeeds | **every renewal fails** |
| the amount matches the published one | a clean receipt | charged a number on no page of the site |
| the entitlement was granted | payment succeeded | paid and still locked out |

Assert the conjunction. `status === 'active'` with no instrument attached is the failure that
looks most like success, which is why it survives longest.

## Enumerate the settled states — never negate the unsettled ones

```
settled  = an explicit allow-list  { succeeded, processing }
EVERY other value, and null, is NOT settled — including ones added next year
```
An allow-list is closed against a provider adding a new intermediate state. A deny-list is not:
the new state arrives, matches nothing, and silently reads as success. *Absence is never
entitlement.*

## The guard that falls through to the thing it guards

Shipped, in a checkout confirmation:

```ts
if (settled(status)) { await onPaid(); return; }   // correct
onError(...);                                       // correct
// -- what actually shipped had no `return`, so BOTH branches reached onPaid()
```
The guard existed, was reviewed, read correctly, and was a no-op. Unpaid attempts rendered a
success screen. **A confirmation the customer cannot distinguish from a real one is worse than
an error**, because it ends their session: they believe they have bought the thing, so they
never retry and never complain. Nothing in the logs marks it.

Every early-return branch needs the `return`, and a test that takes the *unsettled* path and
asserts the success handler was **not** called.

## Three tests, or the path is untested

1. **Terminal success** — drive the real path to settlement; assert every half of the
   conjunction, by value, not by truthiness.
2. **The exact shape of the observed failure** — build the record as it appeared in production
   (here: settled-looking status, instrument absent) and assert it does **not** score as
   revenue.
3. **The near miss** — settled status, instrument present only as an unresolved reference.
   Status alone scores this as money. It is not.

Mock the provider, never the code under test. A test that mocks the function it is checking
passes with that function deleted.

## Prices are published claims

Any amount that can be attached to a charge must be in a catalog derived from **what the
customer is shown**, not a second literal beside it. Hand-made amounts from testing outlive
the test: six were still live and chargeable here, one of them a fifth of a currency unit, one
an annual rate exceeding twelve monthly renewals. Nothing refused any of them.

Archived is enough — an amount that cannot be attached cannot charge anyone. Demand archiving,
not deletion.

## Refuses to do silently
Report a path tested when only the handshake is asserted · accept a status field as proof of
payment · negate a list of unsettled states instead of enumerating settled ones · let a failed
attempt render as a success · approve a new chargeable amount that appears on no page.

## Self-test
Delete the instrument-attached half of the assertion: the suite must go red. Restore it, then
delete the settled-status half: red again. If either deletion leaves it green, that half was
never being checked, and it is the half production failed on.
