# EXECUTE mode — design

**Date:** 2026-08-16
**Status:** approved, not yet built
**Scope:** InDesign only

Apply audit findings as real edits to an InDesign document, on a copy, and prove nothing regressed.

---

## 1. Goal

Today the Artworking tool audits and marks up. It cannot fix anything. Most of what it finds is mechanical — 122 soft hyphens, 13 double spaces, 22 hairline strokes — and correcting those by hand is an afternoon of tedium with its own error rate.

EXECUTE mode does the tedious 70% and proves it did no harm, so attention goes to the 30% that needs a person.

**Success:** point it at an InDesign file, get back a corrected copy, a change log where every edit traces to a numbered finding, and evidence that nothing else moved. The original is byte-identical afterwards, and that is asserted, not assumed.

---

## 2. Non-negotiable: the original is never opened

The weak version of "work on a copy" is to open the original and `saveACopy()`. That still opens the original, and InDesign writes to files on open — link updates, version migration, lock files.

**InDesign never sees the original.**

```
1.  sha256 the original; record size and mtime
2.  REFUSE if the original is open in InDesign      (match app.documents by fullName)
3.  REFUSE if an .idlk lock file sits beside it
4.  chmod the original read-only for the duration
5.  shutil.copy2 -> <stem>_ARTWORKED_<YYYYMMDD-HHMMSS>.indd, SAME FOLDER
6.  InDesign opens ONLY the copy
7.  apply rules; save the copy; close
8.  restore original permissions
9.  re-hash the original — ANY difference aborts the run as a tool bug
```

Step 5 copies into the **same directory** deliberately: relative links and a sibling `Document Fonts` folder keep resolving. A copy in a temp directory arrives with every link broken.

Step 9 is the point of the whole section. The guarantee is an assertion that fails the run, not a policy anyone has to trust.

Read-only in step 4 means even a bug in the ExtendScript cannot write to the original.

---

## 3. Architecture: one registry, not two systems

A fixer driven by a hand-authored findings file is a one-off script. To work on any document it must find the faults itself — and a rule that knows how to *find* double spaces already knows how to *fix* them. Splitting the system into an auditor and a separate fixer duplicates that knowledge, and the two copies drift.

So: **one rule per fault type, carrying its own detection, fix and verification.**

```python
class Rule:
    id       = "typo.double-space"     # stable, namespaced
    severity = "CRAFT"                 # BLOCK | RISK | CRAFT | NOTE
    domain   = "Typography"            # maps to artworking-functions.md
    short    = "double space"          # printed on the mark
    tier     = AMBER                   # GREEN | AMBER | RED

    def detect(self, doc) -> list[Finding]:
        """Findings with page, rects and evidence. Required."""

    def fix(self, doc, finding) -> list[Change]:
        """Apply. Return None for propose-only rules."""

    def verify(self, before, after) -> Result:
        """Rule-specific invariant. Runs on top of the global gates."""
```

Adding a rule once covers every job from then on. Nothing is document-specific.

### Tiers

| Tier | Meaning | Behaviour |
|---|---|---|
| **GREEN** | Cannot recompose text | Applied by default |
| **AMBER** | Correct in isolation, but recomposes the story | **Off by default in v1.** Opt in per run. |
| **RED** | Needs judgement or a client decision | Detect and report only. Never applied. |

Tier is declared on the rule, so the distinction is enforced in code rather than by convention.

Every rule is individually switchable. The whole `colour.*` namespace can be left off until it has earned trust — swatch edits are the highest-risk category and only about six clicks by hand.

---

## 4. Verification

Three gates, all run against the copy. Any hard failure rolls back.

### 4.1 Rule invariant

Specific to the rule, and sharper than a generic check. Stripping soft hyphens must reduce character count by exactly the number removed, with no other text difference. A generic "did anything break" test cannot make that assertion.

### 4.2 Global structural

Snapshot before, compare after. **Hard fail:**

- Overset appears where there was none
- Page count changes
- Any frame moves — no GREEN or AMBER fix should shift geometry by a point
- Group tree differs — nesting, membership or bounds
- Font list or link list changes
- A text difference the tool cannot account for. Every differing character must map to an approved finding.

**Report, do not fail:**

- Story line counts changed. Inevitable when stripping 122 soft hyphens, and exactly why it is surfaced rather than waved through. New widows and orphans live here.

### 4.3 Colour

Snapshot every page item's **resolved** fill and stroke — actual CMYK values, not swatch names. **No object may resolve to a different colour.**

Swatches may be renamed, merged or deleted; objects may not change appearance. This holds regardless of how the fix logic was written, which is why it is the right invariant.

Known swatch failure modes it defends against:

- `swatch.remove()` without `replacingWith` silently substitutes a colour into whatever used it
- Deleting while iterating shifts collection indices
- Gradients and tints reference base swatches and break when the base is deleted
- `[None]`, `[Paper]`, `[Black]`, `[Registration]` are reserved and are never touched

Group rules, for the same reason:

- **Never ungroup.** `allPageItems` reaches inside groups for read and write, so there is no reason to.
- **Never set a property on a Group** where a child is meant. Assigning `strokeWeight` to a group applies it to every member, so one hairline fix could thicken a dozen unrelated objects.

### 4.4 Rollback policy

Ambiguous in the first draft, so stated explicitly.

**Every run is a dry run first.** Apply the full rule set to the copy, run all three gates, and report the predicted diff. Nothing is committed until the whole set verifies clean.

On a hard failure:

1. **Roll back the offending rule** and re-run the gates
2. If the remainder now passes, commit it and report the rule that was dropped and why
3. If rules interacted and the remainder still fails, **roll back the whole run** and report

The copy is disposable, so a failed run costs nothing but time. Whole-run rollback is simply deleting the copy — never an in-place undo, which is where scripted repair usually goes wrong.

---

## 5. Differential audit

The audit engine is its own verification harness.

```
original ──(filesystem copy, never opened)──► copy
                                               │
                          detect ──► findings_before
                                               │
                             fix ──► detect ──► findings_after

findings may only go DOWN.  Any new finding is a regression.
```

**Both detection passes run on the copy**, not the original — section 2 forbids opening the original at all. The baseline is taken from the copy before any fix is applied, which is equivalent because the copy is byte-identical at that moment and the hash proves it.

Plus a **page-by-page visual PDF diff**: export before and after, compare, and report which pages changed and what moved. The structural gates prove integrity; the visual diff is what actually lets a designer sign it off. The export is nearly free once the file is already open.

---

## 6. Outputs

| Artefact | Contents |
|---|---|
| `<stem>_ARTWORKED_<ts>.indd` | The corrected copy |
| `changes.json` | Every edit, keyed to its finding id, with before and after values |
| `findings_before.json` / `findings_after.json` | The differential audit |
| `<stem>_DIFF.pdf` | Visual page-by-page before/after |
| `<stem>_MARKED.pdf` | Markup of what remains, via the existing `mark.py` |
| Console gate | PASS / FAIL, with the reason on failure |

---

## 7. v1 rule set

Scoped to what the first live job actually produced: 12 rules covering 38 of 41 findings.

**GREEN** — `print.stroke-below-minimum` · `colour.registration-in-artwork` · `colour.unused-swatch` · `colour.duplicate-swatch` · `colour.rgb-swatch-in-cmyk` · `doc.bleed-not-set`

**AMBER** — `typo.soft-hyphen` · `typo.double-space` · `typo.straight-quote` · `typo.hyphen-for-range` · `typo.spaced-hyphen-compound`

**RED** — factual contradictions · date/day mismatch · arithmetic · missing or substituted fonts · low-resolution images · overset text · hidden special-finish layer · QR destination mismatch

RED is the largest group and always will be. The expensive findings are judgement calls; that split is the feature.

---

## 8. Out of scope for v1

- **Illustrator and Photoshop.** The rule interface stays open; the ExtendScript underneath differs enough to roughly double the work per rule.
- **Editing PDFs.** Corrections belong at source. Unchanged from existing project rules.
- **Ambient tidying.** Nothing is cleaned up unless it appeared as a finding first. No helpful-on-the-way-past edits.
- **Anything RED.** The tool proposes; a person decides.

---

## 9. Known risks

**AMBER may not be worth it.** Every text fix recomposes, so on a 22pp document most pages shift slightly. The gates catch real breakage, but the diff will carry a lot of "this moved 0.4mm" noise. Mitigation: AMBER defaults off; enable after seeing how noisy real diffs are.

**Detection is the larger half.** The fixer is small. Findings today are hand-authored after a careful read; a dynamic fixer needs a dynamic auditor, and that is most of the build. This spec depends on Phases 1–4 of `PLAN.md` existing.

**Fixes interact.** Rolling back "just the offending rule" is not always cleanly separable. Mitigation: dry-run the full set and show the predicted diff before committing; per-rule rollback is the backstop, whole-run rollback the fallback.

**ExtendScript is ES3 and fails quietly.** No `JSON`, no modern syntax, and errors inside loops are easy to swallow. Mitigation: every rule wrapped in try/catch that records rather than skips, and `userInteractionLevel = NEVER_INTERACT` so a modal dialog cannot hang a run.

---

## 10. Definition of done

- Point it at an InDesign file with no other arguments and get a corrected copy plus a change log
- Original verified byte-identical by hash after every run
- Every edit traces to a numbered finding
- All three verification gates implemented, with rollback on hard failure
- Differential audit shows findings only decreasing
- Visual diff produced
- Each rule independently testable against a fixture document with that fault seeded
- GREEN rule set passes on a fixture and on a live 22pp brochure
