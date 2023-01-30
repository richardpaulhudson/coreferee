import unittest
import tempfile
from os import sep, mkdir, chdir, listdir
from packaging import version
from pathlib import Path
from pytest import skip
import spacy
from spacy.cli.package import package

class CommonPackagingTest(unittest.TestCase):

    def test_model_packaging(self):
        nlp = spacy.load("en_core_web_lg")
        nlp.add_pipe("coreferee")
        if version.parse(nlp.meta["version"]) < version.parse("3.3.0"):
            skip("Old spaCy version")
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = sep.join((tmpdir, "en_core_web_lg"))
            output_dir = sep.join((tmpdir, "output"))
            nlp.to_disk(input_dir)
            mkdir(output_dir)
            package(Path(input_dir), Path(output_dir))
            versioned_model_name = listdir(output_dir)[0]
            chdir(
                sep.join(
                    (output_dir, versioned_model_name, "en_core_web_lg", versioned_model_name)
                )
            )
            nlp2 = spacy.load(".")
            doc = nlp2("I saw a dog. It wagged its tail.")
            self.assertEqual("[0: [3], [5], [7]]", str(doc._.coref_chains))
