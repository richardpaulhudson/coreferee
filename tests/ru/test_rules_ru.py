# test = RussianRulesTest
# test.setUp(test)


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
import spacy
import coreferee
from coreferee.rules import RulesAnalyzerFactory
from coreferee.test_utils import get_nlps
from coreferee.data_model import Mention


class RussianRulesTest(unittest.TestCase):

    def setUp(self):

        self.nlps = get_nlps('ru', add_coreferee=False)
        self.rules_analyzers = [RulesAnalyzerFactory.get_rules_analyzer(nlp) for
                                nlp in self.nlps]

    def all_nlps(self, func):
        for nlp in self.nlps:
            func(nlp)

    def compare_get_dependent_sibling_info(self, doc_text, index, expected_dependent_siblings,
                                           expected_governing_sibling,
                                           expected_has_or_coordination=None,
                                           *, excluded_nlps=[]):

        def func(nlp):

            if nlp.meta['name'] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            self.assertEqual(expected_dependent_siblings, str(
                doc[index]._.coref_chains.temp_dependent_siblings), nlp.meta['name'])
            for sibling in (sibling for sibling in
                            doc[index]._.coref_chains.temp_dependent_siblings if
                            sibling.i != index):
                self.assertEqual(doc[index], sibling._.coref_chains.temp_governing_sibling,
                                 nlp.meta['name'])
            if expected_governing_sibling is None:
                self.assertEqual(None, doc[index]._.coref_chains.temp_governing_sibling,
                                 nlp.meta['name'])
            else:
                self.assertEqual(doc[expected_governing_sibling],
                                 doc[index]._.coref_chains.temp_governing_sibling, nlp.meta['name'])
            self.assertEqual(expected_has_or_coordination,
                             doc[index]._.coref_chains.temp_has_or_coordination, nlp.meta['name'])

        self.all_nlps(func)

    def test_get_dependent_sibling_info_no_conjunction(self):
        self.compare_get_dependent_sibling_info('Дима пришел домой', 0, '[]', None, False)

    def test_get_dependent_sibling_info_two_member_conjunction_phrase_and(self):
        self.compare_get_dependent_sibling_info('Дмитрий и Кристина пришли домой', 0,
                                                '[Кристина]', None, False)

    def test_get_dependent_sibling_info_two_member_conjunction_phrase_with(self):
        self.compare_get_dependent_sibling_info('Дмитрий с Кристиной пришли домой', 0,
                                                '[Кристиной]', None, False)

    def test_get_dependent_sibling_info_two_member_conjunction_phrase_verb_anaphor_with(self):
        self.compare_get_dependent_sibling_info('Артем приехал. Он уехал с Анной', 3,
                                                '[]', None, False)

    def test_get_dependent_sibling_info_two_member_conjunction_phrase_verb_anaphor_with_and(self):
        self.compare_get_dependent_sibling_info('Артем приехал. Он уехал с Кристиной и Анной', 3,
                                                '[]', None, False)

    def test_get_governing_sibling_info_two_member_conjunction_phrase_and(self):
        self.compare_get_dependent_sibling_info('Дмитрий или Кристина приехали домой', 2,
                                                '[]', 0, False)

    def test_get_dependent_sibling_info_two_member_conjunction_phrase_or(self):
        self.compare_get_dependent_sibling_info('Дмитрий или Кристина приехали домой', 0,
                                                '[Кристина]', None, True)

    def test_get_dependent_sibling_info_two_member_nmod_conjunction(self):
        self.compare_get_dependent_sibling_info('Дмитрий c Кристиной приехали домой', 0,
                                                '[Кристиной]', None, False)

    def test_get_governing_sibling_info_two_member_conjunction_phrase_or_control(self):
        self.compare_get_dependent_sibling_info('Дмитрий или Кристина приехали домой', 2,
                                                '[]', 0, False)

    def test_get_dependent_sibling_info_three_member_conjunction_phrase_with_comma_and(self):
        self.compare_get_dependent_sibling_info('Василий, Петр и Сергей провели совещание', 0,
                                                '[Петр, Сергей]', None, False)

    def test_get_dependent_sibling_info_three_member_conjunction_phrase_with_comma_or(self):
        self.compare_get_dependent_sibling_info('Василий, Петр или Сергей провели совещание', 0,
                                                '[Петр, Сергей]', None, True)

    def test_get_dependent_sibling_info_conjunction_itself(self):
        self.compare_get_dependent_sibling_info(
            'Встреча с Василием, Петром и Сергеем состоялась вчера.', 3,
            '[]', None, False)

    def test_get_dependent_sibling_other_instrumental(self):
        self.compare_get_dependent_sibling_info(
            'Они обсудили эту книгу.', 3,
            '[]', None, False)

    def compare_independent_noun(self, doc_text, expected_per_indexes, *,
                                 excluded_nlps=[]):

        def func(nlp):
            if nlp.meta['name'] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            per_indexes = [token.i for token in doc if
                           rules_analyzer.is_independent_noun(token)]
            self.assertEqual(expected_per_indexes, per_indexes, nlp.meta['name'])

        self.all_nlps(func)

    def test_independent_noun_simple(self):
        self.compare_independent_noun('Они смотрели на львов', [3])

    def test_independent_noun_conjunction(self):
        self.compare_independent_noun('Они смотрели на львов и слонов', [3, 5])

    def test_substituting_indefinite_pronoun(self):
        self.compare_independent_noun('Один из мальчиков подошел к парку', [2, 5])

    def test_punctuation(self):
        self.compare_independent_noun(
            '[Enter]',
            [1])

    def compare_potentially_indefinite(self, doc_text, index, expected_truth, *,
                                       excluded_nlps=[]):

        def func(nlp):
            if nlp.meta['name'] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            self.assertEqual(expected_truth,
                             rules_analyzer.is_potentially_indefinite(doc[index]),
                             nlp.meta['name'])

        self.all_nlps(func)

    def test_potentially_indefinite_proper_noun(self):
        self.compare_potentially_indefinite('Я поговорил с Петром', 3, False)

    def test_potentially_indefinite_common_noun_with_reflexive_pronoun(self):
        self.compare_potentially_indefinite('Я поговорил со своим братом', 4, False,
                                            excluded_nlps=['core_news_md', 'core_news_lg'])

    def test_potentially_indefinite_common_noun_jakis(self):
        self.compare_potentially_indefinite('Я поговорил с братом', 3, True)

    def test_potentially_indefinite_definite_common_noun(self):
        self.compare_potentially_indefinite('Я говорил с этим братом', 4, False)

    def test_potentially_indefinite_with_indefinite_determinant(self):
        self.compare_potentially_indefinite('Я говорил с каким-то братом', 6, True,
                                            excluded_nlps=[])

    def test_potentially_indefinite_common_noun_with_possessive_pronoun(self):
        self.compare_potentially_indefinite('Я говорил с твоим братом', 4, False)

    def test_potentially_definite_common_noun_with_indefinitive_pronoun(self):
        self.compare_potentially_indefinite('Тот брат', 1, False)

    def compare_potentially_definite(self, doc_text, index, expected_truth, *,
                                     excluded_nlps=[]):

        def func(nlp):
            if nlp.meta['name'] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            self.assertEqual(expected_truth,
                             rules_analyzer.is_potentially_definite(doc[index]),
                             nlp.meta['name'])

        self.all_nlps(func)

    def test_potentially_definite_proper_noun(self):
        self.compare_potentially_definite('Я поговорил с Петром', 3, True)

    def test_potentially_definite_common_noun_with_reflexive_pronoun(self):
        self.compare_potentially_definite('Я поговорил со своим братом', 4, True)

    def test_potentially_definite_definite_common_noun(self):
        self.compare_potentially_definite('Я говорил с этим братом', 4, True)

    def test_potentially_definite_common_noun_with_possessive_pronoun(self):
        self.compare_potentially_definite('Я говорил с твоим братом', 4, True)

    def test_potentially_definite_with_indefinite_determinant(self):
        self.compare_potentially_definite('Я говорил с каким-то братом', 6, False,
                                          excluded_nlps=['core_news_sm'])

    def test_potentially_definite_common_noun(self):
        self.compare_potentially_definite('Я поговорил с братом', 3, False)

    def test_potentially_definite_common_noun_with_definitive_pronoun(self):
        self.compare_potentially_definite('Тот брат', 1, True)

    def compare_potential_anaphor(self, doc_text, expected_per_indexes, *,
                                  excluded_nlps=[]):
        def func(nlp):
            if nlp.meta['name'] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            per_indexes = [token.i for token in doc if
                           rules_analyzer.is_potential_anaphor(token)]
            self.assertEqual(expected_per_indexes, per_indexes, nlp.meta['name'])

        self.all_nlps(func)

    def test_first_person_pronouns(self):
        self.compare_potential_anaphor('Я вышел посмотреть на нас', [0, 4])

    def test_second_person_pronouns(self):
        self.compare_potential_anaphor('Вы вышли посмотреть на вас', [0, 4])

    def test_third_person_pronouns(self):
        self.compare_potential_anaphor('Она вышла посмотреть на нее.', [0, 4])

    def test_reflexive(self):
        self.compare_potential_anaphor('Она вышла посмотреть на свою машину.', [0, 4])

    def test_first_and_second_person_pronouns(self):
        self.compare_potential_anaphor('Я знаю, что ты его знаешь', [0, 4, 5])

    def test_reflexive_pronoun(self):
        self.compare_potential_anaphor('Он посмотрел на себя в зеркале', [0, 3])

    def test_it(self):
        self.compare_potential_anaphor('Я видел чудо. Это было незабываемо', [0, 4])

    def testit_with_conjunction(self):
        self.compare_potential_anaphor('Я видел звезду. Это и ночь было незабываемо', [0, 4])

    def test_pleonastic_pronoun(self):
        self.compare_potential_anaphor('Он сказал мне о том, что его приняли работу', [0, 2, 4, 7])

    def compare_potential_pair(self, doc_text, referred_index, include_dependent_siblings,
                               referring_index, expected_truth, *, excluded_nlps=[], directly=True):

        def func(nlp):
            if nlp.meta['name'] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            assert rules_analyzer.is_independent_noun(doc[referred_index]) or \
                   rules_analyzer.is_potential_anaphor(doc[referred_index])
            assert rules_analyzer.is_potential_anaphor(doc[referring_index])
            referred_mention = Mention(doc[referred_index], include_dependent_siblings)
            self.assertEqual(expected_truth, rules_analyzer.is_potential_anaphoric_pair(
                referred_mention, doc[referring_index], directly), nlp.meta['name'])

        self.all_nlps(func)

    def test_potential_pair_trivial_singular(self):
        self.compare_potential_pair('Я увидел мужчину. Он гулял', 2, False, 4, 2)

    def test_potential_pair_trivial_plural_conjuntion_and(self):
        self.compare_potential_pair('Я увидел мужчину и женщину. Они гуляли', 2, True, 6, 2)

    def test_potential_pair_trivial_plural_conjuntion_and_control(self):
        self.compare_potential_pair('Я увидел мужчину и женщину. Они гуляли', 4, True, 6, 2)

    def test_potential_pair_trivial_plural_conjuntion_and_with_names(self):
        self.compare_potential_pair('Я увидел Петра и Анну. Они гуляли', 2, True, 6, 2)

    def test_potential_pair_trivial_plural_conjuntion_and_with_names_control(self):
        self.compare_potential_pair('Я увидел Петра и Анну. Они гуляли', 4, True, 6, 2)

    def test_potential_pair_trivial_plural_conjuntion_and_with_names_as_subjects(self):
        self.compare_potential_pair('Петр и Анна были в парке. Они гуляли', 0, True, 7, 2)

    def test_potential_pair_trivial_plural_conjuntion_and_with_names_as_subjects_control(self):
        self.compare_potential_pair('Петр и Анна были в парке. Они гуляли', 2, True, 7, 2)

    def test_potential_pair_trivial_plural_nmod_conjuction(self):
        self.compare_potential_pair('Я увидел мужчину с женщиной. Они гуляли', 2, True, 6, 2)

    def test_potential_pair_plurals_with_coordination_first_conjuntion_and(self):
        self.compare_potential_pair('Я увидел мужчин и женщин. Они гуляли', 2, True, 6, 2)

    def test_potential_pair_plurals_with_coordination_second_conjuntion_and(self):
        self.compare_potential_pair('Я увидел мужчин и женщин. Они гуляли', 4, True, 6, 2)

    def test_potential_pair_plurals_with_coordination_first_conjuntion_with(self):
        self.compare_potential_pair('Я увидел мужчин c женщинами. Они гуляли', 2, True, 6, 2)

    def test_potential_pair_plurals_with_coordination_second_conjuntion_with(self):
        self.compare_potential_pair('Я увидел мужчин c женщинами. Они гуляли', 4, True, 6, 2)

    def test_two_singular_objects_same_gender_with_plural_referring_pronoun_2(self):
        self.compare_potential_pair('Я увидел девочку и женщину, они гуляли', 4, False, 6, 2)

    def test_two_singular_objects_same_gender_inanimate_with_plural_referring_pronoun_2(self):
        self.compare_potential_pair('Я увидел кисть и краску, они лежали', 4, False, 6, 2)

    def test_potential_pair_different_pronouns_1(self):
        self.compare_potential_pair('Я увидел его и ее друга', 2, False, 4, 0)

    def test_potential_pair_different_pronouns_2(self):
        self.compare_potential_pair('Я увидел его и их друга', 2, False, 4, 0)

    def test_potential_pair_different_pronouns_control(self):
        self.compare_potential_pair('Я увидел его и его друга', 2, False, 4, 2)

    def test_potential_pair_plural_referred_singular_referring(self):
        self.compare_potential_pair('Я увидел мужчин. Он был там', 2, False, 4, 0)

    def test_potential_pair_noun_and_first_person_pronoun(self):
        self.compare_potential_pair('Я увидел мужчину. Я был там', 2, False, 4, 0)

    def test_potential_pair_noun_and_second_person_pronoun(self):
        self.compare_potential_pair('Я увидел мужчину. Ты был там', 2, False, 4, 0)

    def test_potential_pair_and_conjunction_and_referred_singular_referring(self):
        self.compare_potential_pair('Я увидел мужчину и женщину. Он был там', 2, True, 6, 2)

    def test_potential_pair_and_conjunction_and_referred_singular_referring_control(self):
        self.compare_potential_pair('Я увидел мужчину и женщину. Он был там', 4, False, 6, 0)

    def test_potential_pair_and_conjunction_with_referred_singular_referring(self):
        self.compare_potential_pair('Я увидел мужчину с женщиной. Он был там', 2, True, 6, 2)

    def test_potential_pair_and_conjunction_with_referred_singular_referring_control(self):
        self.compare_potential_pair('Я увидел мужчину с женщиной. Он был там', 4, False, 6, 0)

    def test_potential_pair_and_conjunction_and_referred_singular_referring_control_2(self):
        self.compare_potential_pair('Я увидел мужчину и женщину. Она была там', 4, False, 6, 2)

    def test_potential_pair_and_conjunction_with_referred_singular_referring_control_3(self):
        self.compare_potential_pair('Я увидел мужчину с женщиной. Она была там', 4, False, 6, 2)

    def test_potential_pair_and_conjunction_with_names_and_referred_singular_referring(self):
        self.compare_potential_pair('Я увидел Петра и Анну. Он был там', 2, True, 6, 2)

    def test_potential_pair_and_conjunction_with_names_and_referred_singular_referring_control(
            self):
        self.compare_potential_pair('Я увидел Петра и Анну. Он был там', 4, False, 6, 0,
                                    excluded_nlps=['core_news_md', 'core_news_sm'])

    def test_potential_pair_and_conjunction_with_names_with_referred_singular_referring(self):
        self.compare_potential_pair('Я увидел Петра с Анной. Он был там', 2, True, 6, 2)

    def test_potential_pair_and_conjunction_with_names_with_referred_singular_referring_control(
            self):
        self.compare_potential_pair('Я увидел Петра с Анной. Он был там', 4, False, 6, 0)

    def test_potential_pair_and_conjunction_with_names_and_referred_singular_referring_control_2(
            self):
        self.compare_potential_pair('Я увидел Петра и Анну. Она была там', 4, False, 6, 2,
                                    excluded_nlps=['core_news_sm'])

    def test_potential_pair_and_conjunction_with_names_with_referred_singular_referring_control_2(
            self):
        self.compare_potential_pair('Я увидел Петра с Анной. Она была там', 4, False, 6, 2)

    def test_potental_pair_two_antecedent_pronouns_with_plural_referring(self):
        self.compare_potential_pair('Я увидел его и ее. Они гуляли', 4, False, 6, 2)

    def test_potental_pair_two_antecedent_pronouns_with_plural_referring_2(self):
        self.compare_potential_pair('Я увидел его с ней. Они гуляли', 4, False, 6, 2)

    def test_potental_pair_two_antecedent_names_subjects_with_plural_referring(self):
        self.compare_potential_pair('Пришли Петр и Анна. Они увидели его', 3, False, 5, 2)

    def test_potental_pair_two_antecedent_names_subjects_single_pronom_after_plural_one(self):
        self.compare_potential_pair('Пришли Петр и Анна. Они увидели его', 1, False, 7, 0)

    def test_potential_pair_they_singular_antecedent(self):
        self.compare_potential_pair('Я увидел дом. Они были там', 2, False, 4, 0)

    def test_potential_pair_they_singular_antecedent_person(self):
        self.compare_potential_pair('Я увидел врача. Они были там', 2, False, 4, 0)

    def test_potential_pair_they_singular_antecedent_proper_name_person(self):
        self.compare_potential_pair('Я видел Петра. Они были там', 2, False, 4, 0)

    def test_potential_pair_it_singular_antecedent_singular_proper_name_person(self):
        self.compare_potential_pair('Я говорил с Петром. Оно было там', 3, False, 5, 0)

    def test_potential_pair_it_singular_antecedent_plural_proper_name_person(self):
        self.compare_potential_pair('Я говорил с Петрами. Оно было там', 3, False, 5, 0)

    def test_potential_pair_it_singular_antecedent_proper_name_non_person(self):
        self.compare_potential_pair('Я работал в компании Петра. Оно было там', 3, False, 6, 0)

    def test_potential_pair_he_she_antecedent_non_person_noun(self):
        self.compare_potential_pair('Я видел дом. Она была там', 2, False, 4, 0)

    def test_potential_pair_he_she_antecedent_person_noun(self):
        self.compare_potential_pair('Я говорил с Петром. Он был там', 3, False, 5, 2)

    def test_potential_pair_he_she_antecedent_non_person_proper_noun(self):
        self.compare_potential_pair('Я работал в компании Петра. Она была там', 3, False, 6, 2)

    def test_potential_pair_he_she_antecedent_non_person_proper_noun_control(self):
        self.compare_potential_pair('Я работал в компании Петра. Она была там', 4, False, 6, 0)

    def test_potential_pair_he_exclusively_female_antecedent(self):
        self.compare_potential_pair('Я видел женщину. Он был там', 2, False, 4, 0)

    def test_potential_pair_he_exclusively_female_name_antecedent(self):
        self.compare_potential_pair('Я видел Анну. Он был там', 2, False, 4, 0)

    def test_potential_pair_he_exclusively_male_name_compound_antecedent(self):
        self.compare_potential_pair('Я видел Иванова Петра. Он был там', 3, True, 5, 2)

    def test_potential_pair_she_exclusively_male_name_compound_antecedent(self):
        self.compare_potential_pair('Я видел Иванова Петра. Она была там', 3, False, 5, 0)

    def test_potential_pair_she_exclusively_female_name_compound_antecedent(self):
        self.compare_potential_pair('Я видел Иванову Анна. Она была там', 3, False, 5, 2)

    def test_potential_pair_he_exclusively_female_name_compound_antecedent(self):
        self.compare_potential_pair('Я видел Иванову Анну. Он был там', 3, True, 5, 0)

    def test_potential_pair_possessive_in_genitive_phrase(self):
        self.compare_potential_pair('Мужчина и его коллега', 0, False, 2, 2)

    def test_potential_pair_possessive_in_genitive_phrase_control(self):
        self.compare_potential_pair('Мужчина и ее коллега', 0, False, 2, 0)

    def test_potential_pair_with_definite_adjective(self):
        self.compare_potential_pair('Мужчина и тот коллега', 0, False, 2, 0)

    def test_potential_pair_with_substantive_definite_adjective(self):
        self.compare_potential_pair('Я видел его. Тот был там', 2, False, 4, 2)

    def test_definite_pronoun_with_complex_substantive_construction(self):
        self.compare_potential_pair('Анна — подруга мужа, с которой тот был близок', 3, False, 7, 0)

    def test_potential_pair_with_indefinite_adjective_related_to_other_noun(self):
        self.compare_potential_pair('Он говорил о каком-то мужчине', 0, False, 3, 0)

    def test_potential_pair_with_possesive_pronoun_with_noun(self):
        self.compare_potential_pair('Этот путь не совпадает с нашим путем', 1, False, 5, 0)

    def test_potential_pair_with_possesive_pronoun_without_noun(self):
        self.compare_potential_pair('Этот путь не совпадает с нашим', 1, False, 5, 0)

    def test_potential_pair_with_possesive_pronoun_without_noun_2(self):
        self.compare_potential_pair('Этот путь не совпадает с вашим', 1, False, 5, 0)

    def test_potential_pair_noun_and_pronoun_first_person(self):
        self.compare_potential_pair('Я посетил много стран. Мы облетели весь мир', 3, False, 5, 0)

    def test_potential_pair_noun_and_pronoun_second_person(self):
        self.compare_potential_pair('Вы посетили много стран. Вы облетели весь мир', 3, False, 5, 0)

    def test_potential_pair_two_pronouns_same_person(self):
        self.compare_potential_pair('Мы посетили много стран. Мы облетели весь мир', 0, False, 5, 2)

    def test_potential_pair_two_pronouns_same_person_2(self):
        self.compare_potential_pair('Вы посетили много стран. Вы облетели весь мир', 0, False, 5, 2)

    def test_potential_pair_two_pronouns_same_person_3(self):
        self.compare_potential_pair('Мы облетели всю страну. Нас удивила ее красота', 0, False, 5,
                                    2)

    def test_potential_pair_acronym(self):
        self.compare_potential_pair('В здании КГБ его приняли на работу', 2, False, 3, 0)

    def test_potential_pair_with_thats_all_construction(self):
        self.compare_potential_pair('Минусы есть, и все', 0, False, 4, 0)

    def test_potential_pair_with_plays_role_construction(self):
        self.compare_potential_pair('Работа играет важную роль. Она приносит доход', 3, False, 5, 0)

    def test_potential_pair_with_plays_role_construction_2(self):
        self.compare_potential_pair('Работа играет важную роль. Она приносит доход', 0, False, 5, 2)

    def test_potential_pair_with_name_acronym(self):
        self.compare_potential_pair('Я видел П. Петрова. Он был там', 2, False, 5, 0)

    def test_potential_pair_part_of_complex_substantive_construction_with_same_gender(self):
        self.compare_potential_pair('Часть речи, которая упоминается', 1, False, 3, 0)

    def test_potential_pair_part_of_complex_substantive_construction_with_same_gender_2(self):
        self.compare_potential_pair('Часть речи, которая упоминается', 0, False, 3, 2)

    def test_potential_pair_object_same_gender_as_subject_and_which(self):
        self.compare_potential_pair('Мужчина с портфелем, который все видели', 2, False, 4, 2)

    def test_potential_pair_object_same_gender_as_subject_and_which_2(self):
        self.compare_potential_pair('Мужчина с портфелем, который все видели', 0, False, 4, 0)

    def test_potential_pair_subject_in_instrumental_case_one_referring_pronoun_same_gender(self):
        self.compare_potential_pair('Мужчина с портфелем, из которого была видна книга', 2, False,
                                    5, 2)

    def test_potential_pair_subject_in_instrumental_case_one_referring_pronoun_same_gender_2(self):
        self.compare_potential_pair('Мужчина с портфелем, из которого была видна книга', 0, False,
                                    5, 0, excluded_nlps=['core_news_md'])

    def test_potential_pair_pronouns_different_person(self):
        self.compare_potential_pair('Мы шли. Они бежали', 0, False, 3, 0)

    def test_potential_pair_pronouns_different_person_2(self):
        self.compare_potential_pair('Вы шли. Они бежали', 0, False, 3, 0)

    def test_potential_pair_first_person_pronoun_with_noun(self):
        self.compare_potential_pair('Мужчины шли. Мы гуляли.', 0, False, 3, 0)

    def test_potential_pair_second_person_pronoun_with_noun(self):
        self.compare_potential_pair('Мужчины шли. Вы гуляли.', 0, False, 3, 0)

    def test_potential_pair_reflexive_pronoun_as_adjective(self):
        self.compare_potential_pair('Я вижу своего друга. Он гуляет.', 2, False, 5, 0)

    def test_potential_pair_reflexive_pronoun_as_adjective_2(self):
        self.compare_potential_pair('Я вижу своего друга. Он гуляет.', 3, False, 5, 2)

    def test_potential_pair_sentence_with_subject_after_object(self):
        self.compare_potential_pair('Она читала книгу, которая вышла в прошлом году', 0, False, 4,
                                    0)

    def test_potential_pair_sentence_with_subject_after_object_2(self):
        self.compare_potential_pair('Она читала книгу, которая вышла в прошлом году', 2, False, 4,
                                    2)

    def test_potential_pair_sentence_with_subject_after_object_3(self):
        self.compare_potential_pair('Люди пишут о книгах, которые прочли в прошлом году', 0, False,
                                    5, 0)

    def test_potential_pair_sentence_with_subject_after_object_4(self):
        self.compare_potential_pair('Люди пишут о книгах, которые прочли в прошлом году', 3, False,
                                    5, 2)

    def test_potential_pair_noun_with_possesive_pronoun_related_to_other_object(self):
        self.compare_potential_pair('Рассказ был написан моим другом', 0, False, 3, 0)

    def test_potential_pair_two_subject_one_referring_pronoun_same_gender(self):
        self.compare_potential_pair('Друг написал картину и книгу, которую потом опубликовали', 2,
                                    False, 6, 0)

    def test_potential_pair_two_subject_one_referring_pronoun_same_gender_2(self):
        self.compare_potential_pair('Друг написал картину и книгу, которую потом опубликовали', 4,
                                    False, 6, 2)

    def test_potential_pair_which_with_object_in_plural_form(self):
        self.compare_potential_pair('Вам помогут разобраться люди, которые живут работой', 3, False,
                                    5, 2)

    def test_potential_pair_which_with_object_in_plural_form_2(self):
        self.compare_potential_pair('Вам помогут разобраться люди, которые живут книгами', 3, False,
                                    5, 2)

    def test_potential_pair_which_with_object_in_plural_form_3(self):
        self.compare_potential_pair('Вам помогут разобраться люди, которые живут книгами', 7, False,
                                    5, 0)

    def test_potential_pair_multiple_objects_with_which_and_possesive_adjective_2(self):
        self.compare_potential_pair('Я видел кошку и кота, которые виляли своими хвостами.',
                                    4, False, 6, 2)

    def test_potential_pair_multiple_objects_with_which_and_possesive_adjective_3(self):
        self.compare_potential_pair('Я видел кошку и кота, которые виляли своими хвостами.',
                                    6, False, 8, 2)

    def test_potential_pair_reflexive_pronoun_different_gender(self):
        self.compare_potential_pair('Появилась компания, которая своим видом всех напугала', 1,
                                    False, 4, 2)

    def test_potential_pair_complex_number_name_with_reduction(self):
        self.compare_potential_pair('Мужчина потратил один млн. на книги. Он доволен', 3, False, 8,
                                    0)

    def test_potential_pair_plural_noun_with_nummod(self):
        self.compare_potential_pair('Я видел пять мужчин. Они гуляли', 3, False, 5, 2)

    def test_potential_pair_conjunction_with_negation(self):
        self.compare_potential_pair('Не рассказы, но книги, которые мы читали', 1, False, 6, 0)

    def test_potential_pair_conjunction_with_negation_2(self):
        self.compare_potential_pair('Не рассказы, но книги, которые мы читали', 4, False, 6, 2)

    def test_potential_pair_conjunction_with_negation_3(self):
        self.compare_potential_pair('Не рассказы, а книги, которые мы читали', 1, False, 6, 0)

    def test_potential_pair_conjunction_with_negation_4(self):
        self.compare_potential_pair('Не рассказы, а книги, которые мы читали', 4, False, 6, 2)

    def test_potential_pair_animate_subject_with_non_animate_object(self):
        self.compare_potential_pair('Женщина прочитала книгу. Ей очень понравилось', 0, False, 4, 2)

    def test_potential_pair_animate_subject_with_non_animate_object_2(self):
        self.compare_potential_pair('Женщина прочитала книгу. Ей очень понравилось', 2, False, 4, 0)

    def test_potential_pair_substantive_predicate(self):
        self.compare_potential_pair('Писатель любитель, который гулял', 1, False, 3, 0,
                                    excluded_nlps=['core_news_md', 'core_news_sm'])

    def test_potential_pair_substantive_predicate_2(self):
        self.compare_potential_pair('Писатель любитель, который гулял', 0, False, 3, 2)

    def test_potental_pair_complex_substantive_object(self):
        self.compare_potential_pair('Книга была написана писателем любителем, который гулял',
                                    3, False, 6, 2, excluded_nlps=['core_news_md'])

    def test_potental_pair_complex_substantive_object_2(self):
        self.compare_potential_pair('Книга была написана писателем любителем, который гулял',
                                    4, False, 6, 0, excluded_nlps=['core_news_md', 'core_news_sm'])

    def test_potential_pair_shorten_noun_with_position_semantics(self):
        self.compare_potential_pair('Акад. Петров был в парке. Он гулял', 0, False, 7, 0)

    def test_potential_pair_which(self):
        self.compare_potential_pair('Я видел мужчину, чья собака гуляла', 2, False, 4, 2)

    def test_potential_pair_subject_over_object_prioritize(self):
        self.compare_potential_pair('Книги о парках, в которых гуляли', 2, False, 5, 2)

    def test_potential_pair_subject_over_object_prioritize_2(self):
        self.compare_potential_pair('Книги о парках, в которых гуляли', 0, False, 5, 0)

    def test_potential_pair_substantive_adverbial_before_referred(self):
        self.compare_potential_pair('На книге обложка, которая была красной', 2, False, 4, 2)

    def test_potential_pair_substantive_adverbial_before_referred_2(self):
        self.compare_potential_pair('На книге обложка, которая была красной', 1, False, 4, 0)

    def test_potential_pair_complex_substantive_constructions_with_possesive(self):
        self.compare_potential_pair('О своем кофе мужина сказал, что он хороший', 1, False, 7, 0)

    def test_potential_pair_complex_substantive_constructions_with_possesive_2(self):
        self.compare_potential_pair('О своем кофе мужина сказал, что он хороший', 2, False, 7, 2)

    def test_potential_pair_complex_substantive_constructions_with_possesive_3(self):
        self.compare_potential_pair('О своем кофе мужина сказал, что он хороший', 3, False, 7, 0)

    def test_potential_pair_subject_and_object_same_person(self):
        self.compare_potential_pair('Мы довольны нами', 0, False, 2, 2)

    def test_potential_pair_subject_and_object_same_person_2(self):
        self.compare_potential_pair('Вы довольны вами', 0, False, 2, 2,
                                    excluded_nlps=['core_news_sm'])

    def test_potential_pair_subject_with_substantive_possesive_adjective(self):
        self.compare_potential_pair('Книга мужчины, которую тот читал', 1, False, 4, 2)

    def test_potential_pair_two_sentences_subjects_with_same_gender(self):
        self.compare_potential_pair('Парк большой. Мужчина писал книгу. Он гулял', 0, False, 7, 0)

    def test_potential_pair_two_sentences_subjects_with_same_gender_2(self):
        self.compare_potential_pair('Парк большой. Мужчина писал книгу. Он гулял', 3, False, 7, 2)

    def test_potential_pair_reflexive_pronoun(self):
        self.compare_potential_pair('Я увидел себя', 0, False, 2, 2)

    def test_potential_pair_reflexive_pronoun_2(self):
        self.compare_potential_pair('Кошка увидела себя', 0, False, 2, 2)

    def test_potential_pair_reflexive_pronoun_3(self):
        self.compare_potential_pair('Вы увидели себя', 0, False, 2, 2)

    def test_potential_pair_reflexive_pronoun_4(self):
        self.compare_potential_pair('Они увидели себя', 0, False, 2, 2)

    def test_potential_pair_conjuction_with_reflexive_pronoun(self):
        self.compare_potential_pair('Кошка и собака преследовали себя', 0, False, 4, 2)

    def test_potential_pair_conjuction_with_reflexive_pronoun_2(self):
        self.compare_potential_pair('Кошка и собака преследовали себя', 2, False, 4, 2)

    def test_potential_pair_nmod_conjuction_with_reflexive_pronoun(self):
        self.compare_potential_pair('Кошка c собакой преследовали себя', 0, False, 4, 2)

    def test_potential_pair_nmod_conjuction_with_reflexive_pronoun_2(self):
        self.compare_potential_pair('Кошка c собакой преследовали себя', 2, False, 4, 2)

    def test_first_second_person_conjuction(self):
        self.compare_potential_pair('Я и ты в парке. Мы гуляли', 0, False, 6, 2)

    def test_first_second_person_conjuction_2(self):
        self.compare_potential_pair('Я и ты в парке. Мы гуляли', 2, False, 6, 2)

    def test_first_second_person_conjuction_control(self):
        self.compare_potential_pair('Я и ты в парке. Они гуляли', 0, False, 6, 0)

    def test_first_second_person_conjuction_control_2(self):
        self.compare_potential_pair('Я и ты в парке. Они гуляли', 2, False, 6, 0)


    def compare_potential_reflexive_pair(self, doc_text, referred_index, include_dependent_siblings,
                                         referring_index, expected_truth, expected_reflexive_truth,
                                         is_reflexive_anaphor_truth, *, excluded_nlps=[]):

        def func(nlp):
            if nlp.meta['name'] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            assert rules_analyzer.is_independent_noun(doc[referred_index]) or \
                   rules_analyzer.is_potential_anaphor(doc[referred_index])
            assert rules_analyzer.is_potential_anaphor(doc[referring_index])
            referred_mention = Mention(doc[referred_index], include_dependent_siblings)
            self.assertEqual(expected_truth, rules_analyzer.is_potential_anaphoric_pair(
                referred_mention, doc[referring_index], True), nlp.meta['name'])
            self.assertEqual(expected_reflexive_truth, rules_analyzer.is_potential_reflexive_pair(
                referred_mention, doc[referring_index]), nlp.meta['name'])
            self.assertEqual(is_reflexive_anaphor_truth, rules_analyzer.is_reflexive_anaphor(
                doc[referring_index]), nlp.meta['name'])

        self.all_nlps(func)

    def compare_potentially_introducing(self, doc_text, index, expected_truth, *,
                                        excluded_nlps=[]):

        def func(nlp):
            if nlp.meta['name'] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            self.assertEqual(expected_truth,
                             rules_analyzer.is_potentially_introducing_noun(doc[index]),
                             nlp.meta['name'])

        self.all_nlps(func)

    def test_potentially_introducing_with_preposition(self):
        self.compare_potentially_introducing('Он живет с коллегой', 3, True)

    def test_potentially_introducing_with_ten_control(self):
        self.compare_potentially_introducing('Он живет с этим коллегой', 4, False)

    def test_potentially_introducing_with_ten_and_relative_clause(self):
        self.compare_potentially_introducing('Он живет с коллегой, которого вы знаете.', 3, True)

    def compare_potentially_referring_back_noun(self, doc_text, index, expected_truth, *,
                                                excluded_nlps=[]):

        def func(nlp):
            if nlp.meta['name'] in excluded_nlps:
                return
            doc = nlp(doc_text)
            rules_analyzer = RulesAnalyzerFactory.get_rules_analyzer(nlp)
            rules_analyzer.initialize(doc)
            self.assertEqual(expected_truth,
                             rules_analyzer.is_potentially_referring_back_noun(doc[index]),
                             nlp.meta['name'])

        self.all_nlps(func)

    def test_potentially_referring_back_noun_with_ten(self):
        self.compare_potentially_referring_back_noun('Он живет с этим коллегой', 4, True)

    def test_potentially_referring_back_noun_with_ten_and_relative_clause_control(self):
        self.compare_potentially_referring_back_noun('Он живет с коллегой, которого вы знаете', 3,
                                                     False)


if __name__ == '__main__':
    suppress_text = io.StringIO()
    sys.stdout = suppress_text
    unittest.main()
    sys.stdout = sys.__stdout__
