#!/bin/bash

# This script downloads the training corpora for English, German, Polish, and French.
#
# Usage: download_corpora.sh <target dir>
set -e
if [ $# -ne 1 ]
then
  echo "Usage: download_corpora.sh <target dir>"
  exit 1
fi
DATA_DIR=$1

mkdir -p "${DATA_DIR}"

# Set up temp directory
TEMP_DIR="${DATA_DIR}/tmp"
if [ -d "${TEMP_DIR}" ]; then
  rm -rf "${TEMP_DIR}"
fi
mkdir "${TEMP_DIR}"
pushd "${TEMP_DIR}"

# Download English and German files from ParCor corpus
if ! [[ -d "${DATA_DIR}/en" ]] && [[ -d "${DATA_DIR}/de" ]]; then
  echo "Downloading ParCor corpus for English and German..."
  wget -O ParCor_v1.0.tar.gz "https://opus.nlpl.eu/legacy/download.php?f=ParCor/ParCor_v1.0.tar.gz"
  echo "Extracting ParCor corpus..."
  tar -xvzf ParCor_v1.0.tar.gz

  if ! [[ -d "${DATA_DIR}/en" ]]; then
    # Download English LitBank corpus

    echo "Downloading LitBank corpus for English"
    git clone https://github.com/dbamman/litbank
    cp litbank/coref/brat/* "${DATA_DIR}/en"

# Download Polish Coreference Corpus

git clone https://github.com/dbamman/litbank
cp litbank/coref/brat/* "${DATA_DIR}/en"

    echo "Moving English corpus into place..."
    mkdir -p "${DATA_DIR}/en"
    find "${TEMP_DIR}/ParCor" -type f | grep "English/Annotator1" | grep ".xml" | xargs -I{} mv {} "${DATA_DIR}/en"
  fi

  if ! [[ -d "${DATA_DIR}/de" ]]; then
    echo "Copying German corpus into place..."
    mkdir -p "${DATA_DIR}/de"
    find "${TEMP_DIR}/ParCor" -type f | grep "German/Annotator1" | grep ".xml" | xargs -I{} mv {} "${DATA_DIR}/de"
  fi

  echo "English and German corpus are ready."
fi

if ! [[ -d "${DATA_DIR}/pl" ]]; then
  echo "Downloading Polish corpus from zil.ipipan.waw.pl..."
  mkdir -p "${DATA_DIR}/pl"
  wget -O "PCC-1.5-BRAT.zip" "https://zil.ipipan.waw.pl/PolishCoreferenceCorpus?action=AttachFile&do=get&target=PCC-1.5-BRAT.zip"
  echo "Extracting Polish corpus..."
  unzip PCC-1.5-BRAT.zip
  echo "Moving Polish corpus into place..."
  cp PCC-1.5-BRAT/*/* "${DATA_DIR}/pl/"
  echo "Polish corpus is ready."
fi

if ! [[ -d "${DATA_DIR}/fr" ]]; then
  echo "Downloading French corpus..."
  mkdir -p "${DATA_DIR}/fr"
  echo "Extracting French corpus..."
  wget -O "DEMOCRAT.zip" "https://repository.ortolang.fr/api/content/export?&path=/democrat/5/&filename=democrat&scope=YW5vbnltb3Vz1"
  unzip "DEMOCRAT.zip"
  mv "democrat" "DEMOCRAT"
  # Ortolang zip does not include democrat_metadata.csv; fetch from neuralcoref-for-french (used by conversion for genre/century)
  if [[ ! -f "DEMOCRAT/democrat_metadata.csv" ]]; then
    echo "Fetching democrat_metadata.csv from neuralcoref-for-french..."
    wget -O "DEMOCRAT/democrat_metadata.csv" "https://github.com/Pantalaymon/neuralcoref-for-french/raw/main/democrat_metadata.csv"
  fi
  PROJECT_ROOT="$(dirname "$(dirname "$(pwd)")")"
  echo "Converting French corpus to CONLL format (this will take a while)..."
  echo "Switching to conversion_conll: ${PROJECT_ROOT}/sh/conversion_conll"
  pushd "${PROJECT_ROOT}/sh/conversion_conll"
  source .venv/bin/activate
  python "main.py" "${TEMP_DIR}"
  popd
  echo "Moving French CONLL data to ${DATA_DIR}/fr ..."
  mv "DEMOCRAT" "${DATA_DIR}/fr/"
  echo "French corpus is ready."
fi
popd
rm -Rf ${TEMP_DIR}