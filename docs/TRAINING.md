# Training Coreferee models (including for new spaCy versions)

You use the **same** training corpora as the existing models.

**Note on French tests (spaCy ≥ 3.7):** Expected values for French rules and smoke tests when using spaCy model version ≥ 3.7 were derived from current (3.7.0) pipeline output. Native-speaker / linguistic review is recommended to confirm they remain correct. No new data is required for spaCy 3.7/3.8; you run the training pipeline once per spaCy version with that version installed.

## 1. Where to get the training data

Use the same sources as in the [model performance table](https://github.com/richardpaulhudson/coreferee#142-model-performance) in the README:

| Language | Training corpora | Links |
|----------|------------------|--------|
| **English (en)** | ParCor + LitBank | [ParCor](https://opus.nlpl.eu/legacy/ParCor/), [LitBank](https://github.com/dbamman/litbank) |
| **German (de)** | ParCor | [ParCor](https://opus.nlpl.eu/legacy/ParCor/) |
| **French (fr)** | DEMOCRAT | [DEMOCRAT](https://www.ortolang.fr/market/corpora/democrat/v1.1) |
| **Polish (pl)** | Polish Coreference Corpus (PCC) | [PCC](http://zil.ipipan.waw.pl/PolishCoreferenceCorpus) |

- Ensure your use and redistribution of the data complies with each corpus’s licence (and the project’s MIT licence).
- The loaders in `coreferee/training/loaders.py` expect specific file names and layouts. For details, read the `load` methods of the loader classes (`ParCorLoader`, `LitBankANNLoader`, `PolishCoreferenceCorpusANNLoader`, `ConllLoader` for DEMOCRAT). ParCor expects `*_words.xml` and `*_coref_level.xml`; LitBank expects `.txt` and `.ann` pairs; etc.
- **French (DEMOCRAT):** The Ortolang DEMOCRAT zip does **not** include `democrat_metadata.csv`. You can get it from [Pantalaymon/neuralcoref-for-french](https://github.com/Pantalaymon/neuralcoref-for-french) (`democrat_metadata.csv`); `sh/download_corpora.sh` fetches it automatically when preparing the French corpus. If the file is missing, `sh/conversion_conll/main.py` builds minimal metadata from the XML directory (all documents included, default genre). Place the file at `DEMOCRAT/democrat_metadata.csv` for genre/century-aware conversion.

### French DEMOCRAT: repository landscape and metadata

- **Coreferee’s French support** was contributed by [Pantalaymon](https://github.com/Pantalaymon) (see the [release notes](https://github.com/richardpaulhudson/coreferee#version-112) in the README). The French models and rules live in this repository; training uses the DEMOCRAT corpus and the conversion in `sh/conversion_conll/main.py`.

- **[Pantalaymon/neuralcoref-for-french](https://github.com/Pantalaymon/neuralcoref-for-french)** is a *separate* project by the same author. It targets **neuralcoref** (a different coreference system), not Coreferee. The README there states that training a neuralcoref model for French was not successfully completed; it points to “my other repository” for “easily accessible coreference resolution for French,” which is the Coreferee-based French support (this repo).

- **What Coreferee uses from that ecosystem:**  
  - **`democrat_metadata.csv`** from neuralcoref-for-french is the canonical metadata (per-document genre and `siècle_composition`) used by `sh/conversion_conll/main.py` when converting DEMOCRAT XML to CONLL. We fetch this file when preparing the French corpus; see above.  
  - Coreferee does *not* use the conversion script or other code from neuralcoref-for-french; it uses its own `sh/conversion_conll/main.py`, which expects the same tab-separated metadata format (columns including `fichier`, `siècle_composition`, and the column used as genre for document IDs).

- **Validating the metadata CSV:** When you have both the DEMOCRAT XML tree and `democrat_metadata.csv`, the conversion script can check that they match. Run the conversion as usual; it will report any XML files that have no metadata row (and optionally metadata rows that have no XML). See the “Metadata validation” note in the conversion script.

## 2. Train for a given spaCy version

Training is done with the **target spaCy version** installed. The config entries whose `from_version`–`to_version` include that version will be trained (and new model directories will be created).

### Example: English models for spaCy 3.7.x and 3.8.x

1. **Prepare data**  
   Put ParCor and LitBank data in a single directory (e.g. `./training_data_en`) in the format expected by `ParCorLoader` and `LitBankANNLoader`.

2. **Environment for spaCy 3.7**  
   Create a virtualenv, install spaCy 3.7.x and the project, then **download every spaCy model** that appears in the language config (training will exit with "model … cannot be loaded" if any are missing):
   ```bash
   pip install "spacy>=3.7,<3.8"  # e.g. 3.7.5
   pip install -e .
   python -m spacy download en_core_web_sm
   python -m spacy download en_core_web_md
   python -m spacy download en_core_web_lg
   python -m spacy download en_core_web_trf
   ```
   For English 3.7 you need all four (sm, md, lg, trf); trf uses lg as vectors model.

3. **Run training** (from the **repository root**):
   ```bash
   python -m coreferee train --lang en --loader_classes ParCorLoader,LitBankANNLoader --data_dir ./training_data_en --log_dir ./train_log_en
   ```
   This trains all English config entries whose version range includes the installed spaCy version (e.g. `sm_3_7_0`, `md_3_7_0`, `lg_3_7_0`, `trf_3_7_0`). Output goes to `./models/en/` and logs to `./train_log_en/`.

4. **Repeat for spaCy 3.8**  
   In a new env with spaCy 3.8.x and the same data:
   ```bash
   pip install "spacy>=3.8,<3.9"
   pip install -e .
   # download en models again for 3.8
   python -m coreferee train --lang en --loader_classes ParCorLoader,LitBankANNLoader --data_dir ./training_data_en --log_dir ./train_log_en_38
   ```
   This trains the `*_3_8_0` entries.

5. **Check quality** (optional)  
   Using the same data and loader:
   ```bash
   python -m coreferee check --lang en --loader_classes ParCorLoader,LitBankANNLoader --data_dir ./training_data_en --log_dir ./check_log_en
   ```

6. **Install the new models**  
   From the **repository root** (so Coreferee uses the local `./models/` and does not download from GitHub):
   ```bash
   python -m coreferee install en
   ```

## 3. Other languages

Same idea, different loaders and data dirs:

- **German**: ParCor data, `--loader_classes ParCorLoader`, `--lang de`
- **French**: DEMOCRAT (CONLL-style), `--loader_classes ConllLoader`, `--lang fr`
- **Polish**: PCC, `--loader_classes PolishCoreferenceCorpusANNLoader`, `--lang pl`

Loader class names and expected directory layout are in `coreferee/training/loaders.py` and in the [README section “Adding support for a new language”](https://github.com/richardpaulhudson/coreferee#4-adding-support-for-a-new-language).

## 4. Summary

- **Data**: Same corpora as in the README table; get them from the links above and place them in a directory in the format expected by the loaders.
- **Training**: Install the desired spaCy version (e.g. 3.7.5 or 3.8.11), install Coreferee and the spaCy language models, then run `python -m coreferee train --lang <lang> --loader_classes <Loaders> --data_dir <path> --log_dir <path>` from the repo root.
- **Install**: From repo root, `python -m coreferee install <lang>` so the newly trained models in `./models/<lang>/` are installed into your environment.
