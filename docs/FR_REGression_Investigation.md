# French coreference test regressions (spaCy 3.7/3.8) — Investigation

**Goal:** Identify correct linguistic behavior for each case and recommend test updates so we assert the correct behavior and do not encode regressions (per AGENTS.md).

**File:** All tests below live in `tests/fr/test_rules_fr.py` unless noted.

---

## 1. `test_potential_referreds_last_token`

**Sentence:** *"Richard entra et un homme le vit"*  
**Token under test:** index 5 = *le* (direct object of *vit*).

- **Linguistics:** *Le* is the clitic pronoun “him”. The only plausible antecedent in the sentence is *Richard* (subject of *entra*). *Un homme* is the subject of *vit*; “le” = “the man” would be incoherent here. So **correct referent = Richard(0)**.
- **Current test:** Primary `["Richard(0)"]`; 3.7+ expected `["homme(4)"]`, lg excluded.
- **Verdict:** The 3.7 override encodes a **regression**. lg is correct; sm/md 3.7+ returning `["homme(4)"]` are wrong.
- **Recommendation:** Remove `expected_potential_referreds_3_7_plus=["homme(4)"]` and `excluded_nlps_3_7_plus=["core_news_lg"]`. Keep primary expected `["Richard(0)"]`. If sm/md 3.7+ fail, exclude those models for this test (do not adopt their wrong output as expected).

---

## 2. `test_potential_referreds_maximum_sentence_referential_distance`

**Sentence:** *"Richard vint. Un homme. Un homme. Un homme. Un homme. Il parla."*  
**Token:** “Il” (index 15) in the 6th sentence.

- **Linguistics:** French uses `maximum_anaphora_sentence_referential_distance = 5`. The code considers preceding sentences within that window. So “Il” may refer to Richard and to each “Un homme” in the preceding five sentences. **Correct behavior:** non-empty list of referents, e.g. `["Richard(0)", "homme(4)", "homme(7)", "homme(10)", "homme(13)"]`.
- **Current test:** Primary = that full list; 3.7+ expected `[]`, md/lg excluded.
- **Verdict:** Asserting `[]` for 3.7+ **encodes a regression**. Empty list means the pipeline fails to find any referent; the correct behavior is the full list. md/lg giving the full list are correct.
- **Recommendation:** Remove `expected_potential_referreds_3_7_plus=[]` and `excluded_nlps_3_7_plus=["core_news_md", "core_news_lg"]`. Keep primary expected as the full list. If sm 3.7+ returns `[]` (e.g. different sentence segmentation), exclude sm for this test or document the regression; do not assert empty as the norm.

---

## 3. `test_potential_referreds_over_maximum_sentence_referential_distance`

**Sentence:** *"Richard vint. Un homme. Un homme. Un homme. Un homme. Un homme. Il parla."*  
**Token:** “Il” in the 7th sentence; Richard is beyond the 5-sentence window.

- **Linguistics:** Only the five “homme” mentions (and not Richard) are within the referential distance. **Correct:** `["homme(4)", "homme(7)", "homme(10)", "homme(13)", "homme(16)"]`.
- **Current test:** Primary = that list; 3.7+ expected `[]`, md/lg excluded.
- **Verdict:** Asserting `[]` for 3.7+ **encodes a regression**. Correct behavior is the list of hommes.
- **Recommendation:** Remove `expected_potential_referreds_3_7_plus=[]` and `excluded_nlps_3_7_plus=["core_news_md", "core_news_lg"]`. Keep primary expected. Exclude or document models that return `[]`; do not adopt empty as expected.

---

## 4. `test_potential_referreds_cataphora_simple`

**Sentence:** *"Même s'il rentra, un homme voyait Richard"*  
**Token:** “il” (index 2), cataphor before its referents.

- **Linguistics:** Cataphors can have potential referents (the following nouns). Here “il” may refer to “un homme” or “Richard”. **Correct:** non-empty list, e.g. `["homme(6)", "Richard(8)"]`.
- **Current test:** Primary = that list; 3.7+ expected `[]`.
- **Verdict:** Asserting `[]` for 3.7+ **encodes a regression**. Cataphors should still have non-empty potential referents when the referents appear later.
- **Recommendation:** Remove `expected_potential_referreds_3_7_plus=[]`. Keep primary expected. If some 3.7+ models return `[]`, exclude them or document; do not adopt empty as expected.

---

## 5. `test_potential_referreds_cataphora_conjunction`

**Sentence:** *"Bien qu'ils rentrèrent, un homme voyait Richard et Julie"*  
**Token:** “ils” (index 2), cataphor; referents = Richard et Julie.

- **Linguistics:** Same as (4): cataphor with following referents. **Correct:** non-empty, e.g. `["[Richard(8); Julie(10)]"]`.
- **Current test:** Primary = that list; 3.7+ expected `[]`.
- **Verdict:** **Regression encoded.** Correct is non-empty.
- **Recommendation:** Remove `expected_potential_referreds_3_7_plus=[]`. Keep primary expected; exclude or document models that return `[]`.

---

## 6. `test_get_dependent_sibling_info_three_member_conjunction_phrase_with_comma_and`

**Sentence:** *"Carol, Richard et Ralf ont mangé un buffet"*  
**Token:** Carol (index 0); dependent siblings = other conjuncts in the NP coordination.

- **Linguistics:** In “X, Y et Z ont mangé”, the coordination is *Carol, Richard et Ralf*; the verb *ont mangé* is the head of the clause, not a conjunct. **Correct dependent siblings of Carol:** `[Richard, Ralf]`. Including *mangé* would mean treating the verb as a coordination sibling, which is a **parse/behavior regression**.
- **Current test:** Primary `"[Richard, Ralf]"`; excluded_nlps = md, sm; 3.7+ expected `"[Richard, mangé]"`.
- **Verdict:** The 3.7+ expected **encodes a regression**. lg (which gives `[Richard, Ralf]`) is correct; sm/md 3.7+ giving `[Richard, mangé]` are wrong.
- **Recommendation:** Remove `expected_dependent_siblings_3_7_plus="[Richard, mangé]"`. Keep primary `"[Richard, Ralf]"`. Add `excluded_nlps_3_7_plus=["core_news_sm", "core_news_md"]` so we do not assert the wrong value; document that sm/md 3.7+ have a coordination parse regression.

---

## 7. `test_get_dependent_sibling_info_two_member_conjunction_phrase_or`

**Sentence:** *"Richard ou Christine rentre à la maison"*  
**Token:** Richard (index 0); dependent sibling = the other NP in the coordination.

- **Linguistics:** In “X ou Y verb”, the coordination is *Richard ou Christine*; the sibling of *Richard* is *Christine*, not the verb. **Correct:** `"[Christine]"`. `"[rentre]"` is a **dependency/parse regression** (verb incorrectly as conjunct).
- **Current test:** Primary `"[Christine]"`; 3.7+ expected `"[rentre]"`, md excluded.
- **Verdict:** **Regression encoded.** Christine is the correct sibling.
- **Recommendation:** Remove `expected_dependent_siblings_3_7_plus="[rentre]"` and `excluded_nlps_3_7_plus=["core_news_md"]`. Keep primary `"[Christine]"`. Add `excluded_nlps_3_7_plus=["core_news_md"]` only if md 3.7+ still returns `[rentre]` (so we skip the regressed model rather than asserting its output).

---

## 8. `test_explicit_anaphor`

**Sentence:** *"Ce dernier vient de rejoindre Camille. Cette dernière est en retard."*  
**Test:** Which token indices are potential anaphors (explicit anaphors: “Ce dernier”, “Cette dernière”).

- **Linguistics:** Both *Ce dernier* (index 1) and *Cette dernière* (index 8) are demonstrative + “dernier/dernière” and are explicit anaphors. **Correct:** `[1, 8]`. md giving `[1, 8]` is correct; accepting only `[8]` for 3.7+ **encodes a regression** (missing index 1).
- **Current test:** Primary `[1, 8]`; 3.7+ expected `[8]`, md excluded.
- **Verdict:** **Regression encoded.** Both should be potential anaphors.
- **Recommendation:** Remove `expected_per_indexes_3_7_plus=[8]` and `excluded_nlps_3_7_plus=["core_news_md"]`. Keep primary `[1, 8]`.

---

## 9. `test_potential_pair_trivial_masc_possessive_control_1`

**Sentence:** *"Je voyais un homme. Leur chien courait."*  
**Referent:** “un homme” (index 3); **referring:** “Leur” (index 5). Control: number mismatch.

- **Linguistics:** *Leur* is plural possessive; *un homme* is singular. They should **not** form a coreference pair (control test). **Correct:** 0 (no pair). Asserting 2 for 3.7+ **encodes a regression**.
- **Current test:** Primary 0; 3.7+ expected 2.
- **Verdict:** **Regression encoded.** Correct is 0.
- **Recommendation:** Remove `expected_truth_3_7_plus=2`. Keep primary expected 0. Exclude or document models that return 2; do not adopt 2 as expected.

---

## 10. `test_potential_pair_trivial_sing_coordination_first_element_possessive_control`

**Sentence:** *"Je voyais un homme et une femme. Leur chien dormait."*  
**Referent:** “un homme” (index 3); **referring:** “Leur” (index 8). Control: “Leur” refers to the whole coordination, not to the first element alone.

- **Linguistics:** *Leur* refers to “un homme et une femme” as a whole. There should be **no direct** anaphoric pair between “un homme” (first conjunct only) and “Leur”. **Correct:** 0. Asserting 2 for 3.7+ **encodes a regression**.
- **Current test:** Primary 0; 3.7+ expected 2.
- **Verdict:** **Regression encoded.** Correct is 0.
- **Recommendation:** Remove `expected_truth_3_7_plus=2`. Keep primary expected 0. Exclude or document models that return 2.

---

## Summary table

| Test | Correct expected | Current 3.7+ override | Action |
|------|------------------|------------------------|--------|
| test_potential_referreds_last_token | `["Richard(0)"]` | `["homme(4)"]`, exclude lg | Revert to correct; remove override & lg exclusion |
| test_potential_referreds_maximum_sentence_referential_distance | full list | `[]`, exclude md/lg | Revert to full list; remove override & exclusions |
| test_potential_referreds_over_maximum_sentence_referential_distance | list of hommes | `[]`, exclude md/lg | Revert to list; remove override & exclusions |
| test_potential_referreds_cataphora_simple | non-empty | `[]` | Remove override; keep non-empty |
| test_potential_referreds_cataphora_conjunction | non-empty | `[]` | Remove override; keep non-empty |
| test_get_dependent_sibling_info_three_member_conjunction_phrase_with_comma_and | `[Richard, Ralf]` | `[Richard, mangé]` | Remove override; add excluded_nlps_3_7_plus for sm/md |
| test_get_dependent_sibling_info_two_member_conjunction_phrase_or | `[Christine]` | `[rentre]`, exclude md | Remove override; keep [Christine], exclude md 3.7+ if it regresses |
| test_explicit_anaphor | `[1, 8]` | `[8]`, exclude md | Remove override & md exclusion |
| test_potential_pair_trivial_masc_possessive_control_1 | 0 | 2 | Remove override; keep 0 |
| test_potential_pair_trivial_sing_coordination_first_element_possessive_control | 0 | 2 | Remove override; keep 0 |

---

## Root cause and rule fixes (spaCy 3.7/3.8)

Regressions stem from **spaCy 3.7/3.8 French pipeline output** (dependency parse, morphology, or sentence segmentation) differing from earlier versions. The **training scripts** use the same `RulesAnalyzer` and config; they do not have separate 3.7/3.8 branches. So fixing **language rules** to be robust to 3.7/3.8 output both fixes rules tests and improves behavior when training or running with 3.7/3.8 models.

The following changes were made in **`coreferee/lang/fr/language_specific_rules.py`**:

1. **`get_dependent_siblings`**  
   When the root token is a noun, only tokens with `pos_ in self.noun_pos` are added as dependent siblings. This avoids treating a verb attached as `conj` (e.g. *mangé* in "Carol, Richard et Ralf ont mangé") or *rentre* in "Richard ou Christine rentre") as a coordination sibling when the coordination is nominal.  
   **Targets:** `test_get_dependent_sibling_info_three_member_conjunction_phrase_with_comma_and`, `test_get_dependent_sibling_info_two_member_conjunction_phrase_or`.

2. **`is_potential_anaphor` (Ce dernier / Cette dernière)**  
   For `lemma_ == "dernier"`, added a fallback when the preceding token is *ce*, *cet*, *cette*, or *ces*, so explicit anaphors are recognized even if the 3.7/3.8 model does not set `PronType=Dem` on the child.  
   **Targets:** `test_explicit_anaphor`.

3. **`get_gender_number_info` (Leur)**  
   For `lemma_ == "leur"`, a final override forces `plur=True` and `sing=False` so possessive *leur* is always treated as plural for agreement. This restores correct behavior when morph is missing or wrong.  
   **Targets:** `test_potential_pair_trivial_masc_possessive_control_1`, `test_potential_pair_trivial_sing_coordination_first_element_possessive_control`.

**Not addressed by rules alone:**  
- **Sentence segmentation** (e.g. `test_potential_referreds_maximum_sentence_referential_distance` / `over_maximum`): If 3.7/3.8 French models produce different `doc.sents`, the referential-distance window changes. That is pipeline/model-dependent; rules assume `doc.sents` as given.  
- **Potential referents for *le*** (e.g. `test_potential_referreds_last_token`): If the model attaches *le* differently or gives different morph, the list of preceding referents can change. The noun-only conjunct fix and *leur* agreement help; remaining differences would require checking actual 3.7/3.8 parses.  
- **Cataphora** (e.g. `test_potential_referreds_cataphora_*`): Empty potential referents can follow from different clause attachment (`advcl` etc.) or sentence boundaries; rules already allow cataphoric referents when the structure is present.

Re-running the French rules tests after these changes will show which regressions are fixed by rules; any remaining failures point to pipeline/model or training data.

---

*Investigation complete. Test changes in `tests/fr/test_rules_fr.py` assert correct behavior. Rule hardening in `coreferee/lang/fr/language_specific_rules.py` for 3.7/3.8.*

Regressions stem from **spaCy 3.7/3.8 French pipeline output** (dependency parse, morphology, or sentence segmentation) differing from earlier versions. The **training scripts** use the same `RulesAnalyzer` and config; they do not have separate 3.7/3.8 branches. So fixing **language rules** to be robust to 3.7/3.8 output both fixes rules tests and improves behavior when training or running with 3.7/3.8 models.

The following changes were made in **`coreferee/lang/fr/language_specific_rules.py`**:

1. **`get_dependent_siblings`**  
   When the root token is a noun, only tokens with `pos_ in self.noun_pos` are added as dependent siblings. This avoids treating a verb attached as `conj` (e.g. *mangé* in "Carol, Richard et Ralf ont mangé") or *rentre* in "Richard ou Christine rentre") as a coordination sibling when the coordination is nominal.  
   **Targets:** `test_get_dependent_sibling_info_three_member_conjunction_phrase_with_comma_and`, `test_get_dependent_sibling_info_two_member_conjunction_phrase_or`.

2. **`is_potential_anaphor` (Ce dernier / Cette dernière)**  
   For `lemma_ == "dernier"`, added a fallback when the preceding token is *ce*, *cet*, *cette*, or *ces*, so explicit anaphors are recognized even if the 3.7/3.8 model does not set `PronType=Dem` on the child.  
   **Targets:** `test_explicit_anaphor`.

3. **`get_gender_number_info` (Leur)**  
   For `lemma_ == "leur"`, a final override forces `plur=True` and `sing=False` so possessive *leur* is always treated as plural for agreement. This restores correct behavior when morph is missing or wrong.  
   **Targets:** `test_potential_pair_trivial_masc_possessive_control_1`, `test_potential_pair_trivial_sing_coordination_first_element_possessive_control`.

**Not addressed by rules alone:**  
- **Sentence segmentation** (e.g. `test_potential_referreds_maximum_sentence_referential_distance` / `over_maximum`): If 3.7/3.8 French models produce different `doc.sents`, the referential-distance window changes. That is pipeline/model-dependent; rules assume `doc.sents` as given.  
- **Potential referents for *le*** (e.g. `test_potential_referreds_last_token`): If the model attaches *le* differently or gives different morph, the list of preceding referents can change. The noun-only conjunct fix and *leur* agreement help; remaining differences would require checking actual 3.7/3.8 parses.  
- **Cataphora** (e.g. `test_potential_referreds_cataphora_*`): Empty potential referents can follow from different clause attachment (`advcl` etc.) or sentence boundaries; rules already allow cataphoric referents when the structure is present.

Re-running the French rules tests after these changes will show which regressions are fixed by rules; any remaining failures point to pipeline/model or training data.

---

*Investigation complete. Test changes in `tests/fr/test_rules_fr.py` assert correct behavior. Rule hardening in `coreferee/lang/fr/language_specific_rules.py` for 3.7/3.8.*
