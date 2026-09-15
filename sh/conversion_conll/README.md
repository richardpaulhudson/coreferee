# CONLL Conversion

## Setup

```bash
PATH="$PATH:$(pyenv root)/versions/3.12.13/bin" uv venv --python 3.12.13
. .venv/bin/activate.fish 
uv sync --active 
python -m ensurepip --upgrade
```  