---
name: strata
description:
  Plan a huge chunk of work (more than one agent session can hold) as a tree of tickets, charted one stratum at a time
  and decomposed until every remaining piece is fully defined, sized so one focused execution session can complete it.
disable-model-invocation: true
---

A loose idea has arrived, too big for one agent session, and wrapped in fog: the way from here to the **destination**
isn't visible yet. Strata is about finding that way, not charging at the destination. Where a broad sweep would chart
the whole domain at once, strata descends **one stratum at a time**: it charts the top few coarse tickets first, and
never opens a deeper layer until the user chooses to. Each stratum is small — a handful of tickets — and each ticket
either resolves a decision or **decomposes** into a handful of sharper ones. The way is clear when every remaining
ticket is **fully defined** and needs no further decomposition.

The destination varies per effort, and naming it is the first act of charting: it shapes every ticket. It might be a
spec to hand off and iterate on, a decision to lock before planning starts, or a change made in place like a
data-structure migration. The map is domain-agnostic: engineering work, course content, whatever fits the shape.

## Plan, don't do

Strata is **planning** by default: each ticket resolves a decision or decomposes a too-large one, and the map is done
when the way is clear, with nothing left to decide or slice before someone goes and does the thing. The pull to just do
the work is usually the signal you've reached the edge of the map and it's time to hand off. An effort can override this
in its **Notes**, carrying execution into the map itself, but absent that, produce decisions and decompositions, not
deliverables.

## Refer by name

Every map and ticket is an issue, so it has a **name**: its title. In everything the human reads (narration, the map's
Decisions-so-far), refer to it by that name.

## The Map

The map is a single directory in this repo's checkout, called `.pi/strata/{}` (where `{}` is replaced by a very short
description of the map confirmed by the user), the canonical artifact. Its tickets are child "issues" of the map,
realized as subdirectories. Each issue directory (including the map issue) can have additional files for storing
additional information about the issue. The canonical `spec.md` file describes the issue in more detail.

The map is an **index**, not a store. It lists the decisions made and points at the tickets that hold their detail; a
decision lives in exactly one place, its ticket, so the map never restates it, only gists it and links.

Put ticket metadata in flat `key: value` front matter in each `spec.md`. Use one plain value per line (no YAML
lists or nested values). `title` and `status` (`open` or `closed`) are required. `blocks` names sibling ticket
directories, comma-separated if there is more than one. For example:

```
---
title: Check the source format
status: open
parent: decomposed-issue
blocks: dependent-issue
labels: strata:research
assignee: null
---
```

This unclaimed research ticket is a child of `decomposed-issue` and blocks `dependent-issue`.

The tickets form a **tree**: decomposition edges (`parent`) give the tree its shape; blocking edges (`blocks`) record
that one ticket's resolution hangs on another's, within or across strata. Strata themselves are never recorded — the
passes that chart them are the strata, and the tree they leave behind is the truth.

### The map body

The whole map at low resolution, loaded once per session. Open tickets are **not** listed: they are open child issues,
found by query.

```markdown
## Destination

<what reaching the end of this map looks like: the spec, decision, or change this effort is finding its way to. One or
two lines; every session orients to it before choosing a ticket.>

## Notes

<domain; skills every session should consult; standing preferences for this effort>

## Decisions so far

<!-- the index: one line per closed ticket, enough to judge relevance, then zoom the link for detail -->

- [<closed ticket title>](link): <one-line gist of the answer>

## Not yet specified

<!-- see "Fog of war": fog with no home ticket yet; graduates as the frontier advances -->

## Out of scope

<!-- see "Out of scope": work ruled beyond the destination; closed, never graduates -->
```

### Tickets

Each ticket is a **child issue** of the map; the **name** is its identity. Its body is the question, sized to one 100K
token agent session:

```markdown
## Question

<the decision or investigation this ticket resolves>
```

Each ticket carries a `strata:<type>` label, one of `research`, `prototype`, `grilling`, `task` (see
[Ticket Types](#ticket-types)), unless it is **fully defined** (see [Fully defined](#fully-defined)).

A session **claims** a ticket by assigning it to the dev driving the map, **first**, before any work, so concurrent
sessions skip it. That assignee _is_ the claim: an open, unassigned ticket is unclaimed.

A ticket is **unblocked** when every ticket blocking it is closed. The **frontier** is the open, unblocked,
unclaimed tickets that are not marked `handover: ready`. A `parent` edge does not block by itself.

The answer isn't part of the body; it's recorded on resolution (see [Work through the map](#work-through-the-map)).
Assets created while resolving a ticket are linked from the issue, not pasted in.

### Find and report next tickets

Run `python3 <skill-dir>/scripts/frontier.py .pi/strata/<map>` from the checkout. Replace `<skill-dir>` with the
absolute path to the directory containing this skill. The script reads only ticket front matter and reports titles
and paths under **Actionable**, **Blocked** (with blocker titles), **Claimed**, and **Handoff ready**. Use its
output instead of opening ticket bodies to compute the frontier. If it errors, report the problem instead of
guessing what is actionable.

Run it when opening a map and again after persisting charting or resolution changes. Use the latest output to tell
the user what can be looked at next: name and link the actionable tickets first. Recommend one when there is a clear
reason, such as unlocking a blocked ticket. Then name blockers and distinguish claimed work from execution handoffs.
If no ticket is actionable, say why. Report the next options without opening a deeper layer automatically.

### Fully defined

A ticket is **fully defined** when its question is sharp and its answer is small enough to execute in one focused
session: for production code, estimated at no more than ~250 lines. The estimate is a calibration, not a contract — it
sets the order of magnitude, not a budget to count lines against. A ticket carrying a decision still open (a genuine
choice to make, a shape to react to, a fact to surface) is **not** fully defined no matter how few lines it might touch,
and a build-ready piece of work whose shape is settled is fully defined even though it produces code, not a decision.

A fully defined ticket carries the marker `handover: ready` — it has nothing left to decide or decompose, and is the
unit such work is handed to an execution session in. Strata resolves the tickets above it and leaves the ready ones
standing for handoff; they graduate from the frontier.

### Ticket Types

Every ticket is either **HITL** (human in the loop, worked _with_ a human who speaks for themselves) or **AFK**, driven
by the agent alone. A HITL ticket only resolves through that live exchange; the agent never stands in for the human's
side of it (a grilling agent that answers its own questions has broken this).

- **Research** (AFK): Reading documentation, third-party APIs, or local resources like knowledge bases to surface a fact
  a decision waits on. Resolved by a subagent that calls the Skill tool with "research". Use when knowledge outside the
  current working directory is required.
- **Prototype** (HITL): Raise the fidelity of the discussion by making a cheap, rough, concrete artifact to react to (an
  outline, a rough take, a stub, or UI/logic code) by calling the Skill tool with "prototype". Links the prototype as an
  asset. Use when "how should it look" or "how should it behave" is the key question.
- **Grilling** (HITL): Conversation. The default case. Always call the Skill tool twice, for "grilling" and
  "domain-modeling".
- **Task** (HITL or AFK): Manual work that must happen before a _decision_ can be made: nothing to decide, prototype, or
  research, but the discussion is blocked until it's done. Signing up for a service so its API can be judged,
  provisioning access, moving data so its shape can be seen. This is the one type that _does_ rather than decides, and
  it earns its place by unblocking a decision, not by delivering the destination. The agent drives it alone where it can
  (AFK); otherwise it hands the human a precise checklist (HITL). Resolved when the work is done; the answer records
  what was done and any resulting facts (credentials location, new URLs, row counts) later tickets depend on.

## Fog of war

The map is _deliberately_ incomplete: don't chart what you can't yet see. Beyond the live tickets lies the **fog of
war**: the dim view of decisions and investigations you can tell are coming but can't yet pin down, because they hang on
questions still open. Resolving a ticket clears the fog ahead of it, graduating whatever's now specifiable into fresh
tickets, one at a time, until the way to the destination is clear and no tickets remain.

Fog lives **where it will be consumed**: each ticket's spec.md carries its own **Not yet specified** section for the dim
questions that hang under it, and decomposing that ticket is the moment its fog resolves — each child's question
crystallized from it, the rest left waiting on the children. The map's **Not yet specified** section holds only **orphan
fog**: dim questions with no home ticket yet, typically sketched at charting time. Write as loosely or as fully as the
view allows; it doubles as a signpost for collaborators reading where the effort is headed.

**Fog or ticket?** The test is whether you can state the question precisely now, _not_ whether you can answer it now.

- **Ticket when** the question is already sharp, even if it's blocked and you can't act on it yet.
- **Not yet specified when** you can't yet phrase it that sharply. Don't pre-slice the fog into ticket-sized pieces:
  it's coarser than a ticket, and one patch may graduate into several tickets, or none, once the frontier reaches it.

**Not yet specified** excludes what's already decided (Decisions so far), what's already a live ticket, and what's out
of scope (the next section).

## Out of scope

Fog only ever gathers _toward_ the destination. The destination fixes the scope, so work beyond it is **out of scope**:
it isn't fog, and it doesn't belong in **Not yet specified**. It gets its own **Out of scope** section on the map: work
you've consciously ruled out of _this_ effort. Scope, not sharpness, lands it here.

Out-of-scope work never graduates (the frontier stops at the destination), so it returns only if the destination is
redrawn, and then as a fresh effort, not a resumption.

Ruling something out of scope is a scoping act, not a step on the route. When a ticket that already exists turns out to
sit past the destination (mis-scoped in while charting, or exposed by a resolution), **close it** (a closed ticket is
unambiguously off the frontier) and leave one line in the **Out of scope** section: the gist plus why it's out of scope,
linking the closed ticket. It stays out of **Decisions so far**, which records the route actually walked; a scope
boundary isn't a step on it.

## Invocation

Two modes. Either way, **never resolve more than one ticket per session**, with the exception of research tickets.

### Chart the map

User invokes with a loose idea.

1. **Name the destination.** Call the Skill tool twice, for "grilling" and "domain-modeling", to pin down what this map
   is finding its way to: the spec, decision, or change. The destination fixes the scope, so it's settled first.
2. **Chart the top stratum.** Grill again, this time to surface the first coarse slice of the route: the few top-level
   decisions or work areas the destination hangs on. Stay shallow — breadth over depth, never descending past questions
   that hang on resolving these first. Aim for **no more than about four tickets**; more is a smell that the slicing is
   wrong, so re-slice coarser, exceeding the cap only with a noted reason. **If this surfaces no fog** (the way to the
   destination is already clear, the whole journey small enough for one session), you don't need a map. Stop and ask the
   user how they'd like to proceed.
3. **Create the map** (label `strata:map`): Destination and Notes filled in, Decisions-so-far empty, orphan fog sketched
   into **Not yet specified**.
4. **Create the tickets you can specify now** as child issues of the map, then wire blocking edges in a **second pass**
   (issues need ids before they can reference each other). Wiring sorts them into the frontier and the blocked;
   everything you can't yet specify stays in the fog. These root tickets are rarely fully defined — they are the stratum
   that later decompositions descend from.
5. **Fire the research subagents.** For each `research` ticket you just created, spin up a subagent that calls the Skill
   tool with "research" to resolve it in parallel, capturing its findings on a throwaway `research/<name>` branch with a
   context pointer from the ticket.
6. Use the [frontier script](#find-and-report-next-tickets) to report next tickets, then stop. Charting is one
   session's work: it hand-resolves nothing and charts **one stratum only**.

### Work through the map

User invokes with a map (URL or number). A ticket is **optional**: without one, you pick the next decision, not the
user.

1. Load the **map** and run the [frontier script](#find-and-report-next-tickets), not every ticket body.
2. Choose the ticket. If no ticket was named, take the first under **Actionable**. If there is none, report the
   state and stop. For a named ticket, check its state before proceeding: don't bypass blockers or another session's
   claim, and only take an explicit handoff into execution if the map's Notes allow execution. **Claim** the ticket
   by assigning it to yourself before working its body.
3. **Size it before resolving.** If the ticket is fully defined (sharp, ~one focused execution session, see
   [Fully defined](#fully-defined)), resolve it: the question is answered, or — when the map's Notes carry execution —
   executed as one unit of handoff. Otherwise the resolution **is the decomposition**: split it into about four sharper
   children, each linked with `parent` to this ticket, wired with blocking edges among themselves where they depend on
   each other, and consume this ticket's **Not yet specified** fog into the children it can now phrase. Then **close the
   decomposed ticket** and record the decomposition in Decisions-so-far with a context pointer; its children replace it
   on the frontier.
4. Record the resolution: post the answer as a **resolution comment**, **close** the issue, and **append a context
   pointer** to the map's Decisions-so-far.
5. Graduate fog the answer has made specifiable, wherever that fog lives; add newly-surfaced tickets (create-then-wire).
   If the answer reveals that a ticket (this one or another) sits beyond the destination, **rule it out of scope**
   rather than resolving it on the route. If the decision invalidates other parts of the map, update or delete those
   tickets.

A decomposed ticket is **done when its children are**: nothing of it remains open once it is closed on decomposition —
the children carry its content forward, and resolving them is recorded on them, not resurrected on the parent.

Descent is **never automatic**: charting and each decomposition open exactly one stratum, then stop and persist. The
user picks which ticket to work or decompose next. The map is done when every open ticket is fully defined and marked
`handover: ready` — at that point the tree is the work breakdown, and what remains is handoff, not wayfinding.

The user may run unblocked tickets in parallel, so expect other sessions to be editing the tracker concurrently.
