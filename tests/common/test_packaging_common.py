import unittest
import tempfile
from os import sep, mkdir, chdir, listdir
from packaging import version
from pathlib import Path
from pytest import skip
import spacy
from spacy.cli.package import package
from coreferee.test_utils import get_nlps

class CommonPackagingTest(unittest.TestCase):
    def setUp(self):
        nlps = get_nlps("en")
        for nlp in (nlp for nlp in nlps if nlp.meta["name"] == "core_web_lg"):
            self.lg_nlp = nlp

    def test_model_packaging(self):
        if version.parse(self.lg_nlp.meta["version"]) < version.parse("3.3.0"):
            skip("Old spaCy version")
        with tempfile.TemporaryDirectory() as tmpdir:
            model_name = "_".join(("en", self.lg_nlp.meta["name"]))
            input_dir = sep.join((tmpdir, model_name))
            output_dir = sep.join((tmpdir, "output"))
            self.lg_nlp.to_disk(input_dir)
            mkdir(output_dir)
            package(Path(input_dir), Path(output_dir))
            versioned_model_name = listdir(output_dir)[0]
            chdir(
                sep.join(
                    (output_dir, versioned_model_name, model_name, versioned_model_name)
                )
            )
            nlp2 = spacy.load(".")
            doc = nlp2("I saw a dog. It wagged its tail.")
            self.assertEqual("[0: [3], [5], [7]]", str(doc._.coref_chains))
