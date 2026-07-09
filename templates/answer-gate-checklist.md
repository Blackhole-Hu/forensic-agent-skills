# Answer Gate Checklist

Pre-submission validation. Every answer must pass all five checks before submission.

**Investigation**: <case name or ID>
**Date**: <YYYY-MM-DD>

---

## Check 1: Question Semantics

- [ ] I understand what the question is asking
- [ ] My answer directly addresses the question (not a related but different question)
- [ ] I have not assumed information not present in the question or evidence
- [ ] Answer format matches what was requested (IP, domain, timestamp, flag, etc.)

**Notes**: <any ambiguity in the question>

---

## Check 2: Answer Format

- [ ] Answer matches the expected format (IPv4, email, ISO timestamp, flag{...}, etc.)
- [ ] No extra whitespace, newlines, or formatting artifacts
- [ ] Case sensitivity is correct (flags, passwords, hashes)
- [ ] Numeric values are in the correct unit/range

**Notes**: <format observations>

---

## Check 3: Evidence Binding

- [ ] Every component of my answer is backed by at least one evidence entry
- [ ] Evidence entries reference actual artifacts (not hallucinated paths)
- [ ] I can point to the specific command output or file content that supports each answer component
- [ ] Hash values match where I claimed integrity

**Evidence references**:
| Answer Component | Evidence Entry | Artifact |
|-----------------|---------------|----------|
| | | |

---

## Check 4: Cross-Validation

- [ ] I have not contradicted any other finding in this investigation
- [ ] Timeline events are consistent (no future events referenced as past)
- [ ] Multiple evidence sources agree where they overlap
- [ ] Negative findings don't contradict positive findings

**Cross-validation notes**: <any inconsistencies found and resolved>

---

## Check 5: Final Evidence Re-read

- [ ] I have re-read the original artifact(s) that support my answer
- [ ] The evidence still says what I think it says (no misreading)
- [ ] I have not cherry-picked evidence that supports my answer while ignoring contradicting evidence
- [ ] Confidence level is justified: <high/medium/low>

**Final verification**: <re-read confirmation>

---

## Result

- [ ] **PASS** — All five checks passed, ready for submission
- [ ] **NEEDS FIX** — One or more checks failed, see notes above
- [ ] **NOT REPRODUCED** — Cannot verify locally, needs manual review

**Decision**: <pass / needs_fix / not_locally_reproduced>
**Signed**: <agent or human>
