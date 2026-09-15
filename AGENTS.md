# Agent guidelines

## Testing

When updating tests for new spaCy or model versions:

1. **Do not encode regressions.** Do not add or change expected values so that tests pass by asserting on worse or incorrect model behavior. If a new model output is linguistically wrong (e.g. wrong referent, wrong morphology, or a parse error), do not adopt that output as the new expected value and exclude models that still behave correctly. Prefer keeping the correct expectation and either fixing the model/pipeline or documenting the regression; use alternative expected values only when multiple outputs are linguistically valid (e.g. parse variation), not when one is a clear regression.

3. **Fix the cause, don’t disable the test.** If a model returns the wrong value, investigate and fix the root cause (e.g. language rules, training data, or pipeline behavior) so the model passes the correct expectation. Do not add or keep exclusions solely to make the test pass; use exclusions only as a temporary measure while a fix is in progress, or when the failure is outside our control (e.g. upstream spaCy model bug with no workaround).