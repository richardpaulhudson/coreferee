# Adding support for a new spaCy version (Coreferee)

**When to use:** Adding or validating support for a new spaCy minor version: new config entries, retraining Coreferee models, and updating tests. Use this skill when editing configs, training, or tests for a new spaCy/model version.

---

## 1. SpaCy library vs model version

- **spaCy library version** = the `spacy` package version (e.g. 3.7.5, 3.8.11).
- **spaCy model version** = `nlp.meta["version"]` for a loaded pipeline (e.g. 3.7.1, 3.8.0). It can differ by language and pipeline (e.g. English 3.7.1/3.7.3, other languages 3.7.0; 3.8.x often 3.8.0 for all).

In `config.cfg`, **`from_version`, `to_version`, and `train_version` always refer to the spaCy model (pipeline) version**, not the library. When editing config or explaining failures, use the correct one.

---

## 2. Model configuration

- Add one config block **per pipeline** (sm, md, lg, trf if applicable) per language.
- **`train_version`**: exact model version the Coreferee model was trained with (must match the pipeline you train with).
- **`from_version` / `to_version`**: range of model versions this Coreferee model supports. Set so that every supported pipeline version in that minor line is included (e.g. 3.8.0–3.8.0 for 3.8).
- Confirm latest model versions from the pipeline's meta or [spaCy models](https://github.com/explosion/spacy-models/releases); do not use library versions (e.g. 3.7.5, 3.8.11) as `train_version` unless the pipeline meta actually reports that.

---

## 3. Data and training

- **Same corpora** as the README model performance table; no new sources. Use existing tooling (e.g. `sh/download_corpora.sh`, `sh/conversion_conll/` for French) as described in [docs/TRAINING.md](docs/TRAINING.md).
- Train with the **target spaCy version** installed and **all** pipelines for that language downloaded. Run from the **repository root**. Repeat for each language and each minor version in a clean environment.
- After training, install from repo root: `python -m coreferee install <lang>`.

---

## 4. Updating tests — rules and constraints

- **Loading:** Ensure `from_version` / `to_version` include the new model versions so `get_nlps()` loads the new pipelines. Otherwise tendencies tests may skip (e.g. when no model matches `train_version`).
- **Prefer conditional assertions over exclusions.** Use version-gated or model-specific expected values (e.g. `expected_*_3_7_plus`, `alternative_expected_*`) so that every supported model is still asserted for that scenario where feasible. Do not add or keep `excluded_nlps` / `excluded_nlps_3_7_plus` when the same case can be covered by a conditional or alternative expected value.
- **Do not encode regressions.** Do not add or change expected values so that tests pass by asserting on incorrect model behaviour. If the new output is linguistically wrong (wrong referent, wrong morphology, parse error), do not adopt it as the new expected value and exclude models that still behave correctly. Keep the correct expectation; fix the model/pipeline or document the regression. Use alternative expected values only when **multiple outputs are linguistically valid** (e.g. parse variation), not when one is a clear regression.
- **Tendencies tests** (`tests/common/test_tendencies_common.py`): Snapshot tests per **model version**. For each new model version, add a branch. Obtain expected values by **running the same code path** as the test (same doc, mention, token) and recording the result. Do not set expected values to "whatever makes the test pass" if that would assert incorrect output.
- **Interpreting failures:** When a test fails for a new version, determine whether the **correct** behaviour is the existing expected value or the new output. If the new output is wrong, treat it as a regression: assert the correct value; fix rules or training (and retrain if needed); do not adopt the wrong output as primary expected.

---

## 5. Regressions: rules vs models

- Failures can come from: (a) **language rules** not handling new parse/morph output, (b) the **Coreferee Thinc model** (weights), or (c) the **spaCy pipeline** (parse/morph).
- When the wrong behaviour is determined by rule logic (e.g. dependent siblings, agreement), fix **language rules** first; then retrain so the neural model is trained on the corrected rule output. Do not assume "retrain only" or "exclude model" without checking rules and pipeline behaviour.
- See [docs/FR_REGression_Investigation.md](docs/FR_REGression_Investigation.md) for a worked example and [AGENTS.md](AGENTS.md) for testing rules.
