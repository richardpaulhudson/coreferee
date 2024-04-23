# Copyright 2021 msg systems ag

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from coreferee.test_utils import get_nlps


class RussianSmokeTest(unittest.TestCase):

    def setUp(self):

        self.nlps = get_nlps('ru')

    def all_nlps(self, func):
        for nlp in self.nlps:
            func(nlp)

    def compare_annotations(self, doc_text, expected_coref_chains, *, excluded_nlps=[],
                            alternative_expected_coref_chains=None):

        def func(nlp):

            if nlp.meta['name'] in excluded_nlps:
                return

            doc = nlp(doc_text)
            chains_representation = str(doc._.coref_chains)
            if alternative_expected_coref_chains is None:
                self.assertEqual(expected_coref_chains,
                                 chains_representation, nlp.meta['name'])
            else:
                self.assertTrue(expected_coref_chains == chains_representation or
                                alternative_expected_coref_chains == chains_representation)

        self.all_nlps(func)

    def test_simple(self):
        self.compare_annotations('Я увидел собаку, она преследовала кошку.', '[0: [2], [4]]')

    def test_simple_plural(self):
        self.compare_annotations('Я увидел собак, они преследовали кошку.', '[0: [2], [4]]')

    def test_simple_conjunction_same_word(self):
        self.compare_annotations(
            'Я увидел собаку и собаку, они преследовали кошку.', '[0: [2, 4], [6]]',
        excluded_nlps=['core_news_sm'])

    def test_simple_conjunction_different_words(self):
        self.compare_annotations(
            'Я увидел коня и собаку, они преследовали кошку.', '[0: [2, 4], [6]]',
            excluded_nlps=['core_news_md', 'core_news_sm'])

    def test_simple_nmod_conjuntion_same_words(self):
        self.compare_annotations(
            'Я увидел коня c конем, они преследовали кошку.', '[0: [2, 4], [6]]')

    def test_simple_nmod_conjuntion_different_words(self):
        self.compare_annotations(
            'Я увидел коня c собакой, они преследовали кошку.', '[0: [2, 4], [6]]')

    def test_conjunction_different_pronouns(self):
        self.compare_annotations(
            'Я увидел Петра и Анну, она и он преследовали кошку.', '[0: [2], [8], 1: [4], [6]]',
            excluded_nlps=['core_news_md'])

    def test_conjunction_involving_pronoun(self):
        self.compare_annotations(
            'Я увидел Сергея и Анну. Она преследовала кошку.', '[0: [4], [6]]',
            excluded_nlps=['core_news_lg', 'core_news_md'])

    def test_conjunction_involving_pronoun_2(self):
        self.compare_annotations(
            'Я увидел Сергея и Анну. Он преследовал кошку.', '[0: [2], [6]]')

    def test_different_sentence(self):
        self.compare_annotations(
            'Я видел Петра. Он преследовал кошку.', '[0: [2], [4]]')

    def test_proper_noun_coreference(self):
        self.compare_annotations(
            'Я видел Петра. Петр преследовал кошку.', '[0: [2], [4]]')

    def test_proper_noun_coreference_multiword(self):
        self.compare_annotations(
            'Я видел Петра Иванова. Петр Иванов преследовал кошку.', '[0: [2], [5], 1: [3], [6]]')

    def test_proper_noun_coreference_multiword_only_second_repeated(self):
        self.compare_annotations(
            'Я видел Петра Иванова. Иванов преследовал кошку.', '[0: [3], [5]]')

    def test_proper_noun_coreference_multiword_only_first_repeated(self):
        self.compare_annotations(
            'Я видел Петра. Иванов преследовал кошку .', '[]')

    def test_common_noun_coreference(self):
        self.compare_annotations(
            'Я видел собаку. Она преследовала кошку, которая виляла своим хвостом',
            '[0: [2], [4], 1: [6], [8], [10]]')

    def test_conjunction_same_words_with_which(self):
        self.compare_annotations('Я увидел собаку c собакой, которые преследовали кошку.',
                                 '[0: [2, 4], [6]]')

    def test_conjunction_different_words_with_which(self):
        self.compare_annotations('Я увидел коня c собакой, которые преследовали кошку.',
                                 '[0: [2, 4], [6]]')

    def test_which_with_multiple_antecedents(self):
        self.compare_annotations(
            'Я видел кошку и кота, которые виляли своими хвостами',
            '[0: [2, 4], [6], [8]]', excluded_nlps=['core_news_sm'])

    def test_two_objects_same_gender_with_which(self):
        self.compare_annotations(
            'Я видел женщину с книгой. Она сидела',
            '[0: [2], [6]]')

    def test_reflexive_simple(self):
        self.compare_annotations(
            'Кошка увидела себя',
            '[0: [0], [2]]')

    def test_reflexive_excluded_mix_of_coordination_and_single_member_1(self):
        self.compare_annotations(
            'Пришли Петр и Анна. Они увидели его.',
            '[0: [1, 3], [5]]')

    def test_reflexive_excluded_mix_of_coordination_and_single_member_2(self):
        self.compare_annotations(
            'Пришли Петр c Анной. Они увидели его.',
            '[0: [1, 3], [5]]', excluded_nlps=['core_news_md', 'core_news_sm'])

    def test_reflexive_anaphor_precedes_referent(self):
        self.compare_annotations(
            'Мы обсуждали его, когда Петр пришел.',
            '[]')

    def test_cataphora_simple(self):
        self.compare_annotations(
            'Хотя он устал, Петр пошел в парк.',
            '[0: [1], [4]]')

    def test_first_and_second_person_conjunction_control(self):
        self.compare_annotations(
            'Я и ты в парке. Они гуляли',
            '[]', excluded_nlps=['core_news_md', 'core_news_sm'])

    def test_cataphora_with_coordination(self):
        self.compare_annotations(
            'Хотя они добрались до их дома, мужчина и женщина грустили',
            '[0: [1], [4], [7, 9]]', excluded_nlps=['core_news_sm'])

    def test_documentation_example_1(self):
        self.compare_annotations(
            'Женщина встала и увидела Петра. Она поздоровалась с ним',
            '[0: [0], [6], 1: [4], [9]]'
        )

    def test_documentation_example_2(self):
        self.compare_annotations(
            'Я видел мужчину, чья собака гуляла. Она виляла своим хвостом',
            '[0: [2], [4], 1: [5], [8], [10]]'
        )

    def test_documentation_example_3(self):
        self.compare_annotations(
            'Хотя они добрались до их дома, Петр и Анна грустили. Он ушел спать. Она взяла свою любимую книгу, которую купила давно.',
            '[0: [1], [4], [7, 9], 1: [7], [12], 2: [9], [16], [18], 3: [20], [22]]')


if __name__ == '__main__':
    unittest.main()
