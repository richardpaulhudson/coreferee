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

from string import punctuation
from spacy.tokens import Token
from ...rules import RulesAnalyzer
from ...data_model import Mention


class LanguageSpecificRulesAnalyzer(RulesAnalyzer):
    random_word = "крот"

    or_lemmas = ("или", "либо")

    dependent_sibling_deps = "conj"

    conjunction_deps = ("cc", "punct")

    adverbial_clause_deps = ("ccomp", "dep", "advcl", "cop")

    entity_noun_dictionary = {
        "persName": ["человек", "персона", "мужчина", "женщина"],
        "placeName": ["место", "город", "область", "штат", "край", "страна"],
        "orgName": [
            "фирма",
            "компания",
            "организация",
            "группа",
            "проект",
            "предприятие",
        ],
    }

    quote_tuples = [
        ("'", "'"),
        ('"', '"'),
        ("„", "“"),
        ("‚", "‘"),
        ("«", "»"),
        ("»", "«"),
    ]

    term_operator_pos = ("DET", "ADP")

    clause_root_pos = ("VERB", "AUX")

    @staticmethod
    def is_reflexive_possessive_pronoun(token: Token) -> bool:
        return (
            token.pos_ == "DET" and token.tag_ == "DET" and token.lemma_ == "свой"
        ) or (token.pos_ == "PRON" and token.tag_ == "PRON" and token.lemma_ == "себя")

    def get_dependent_siblings(self, token: Token) -> list:
        def add_siblings_recursively(recursed_token: Token, visited_set: set) -> None:
            visited_set.add(recursed_token)
            siblings_set = set()
            if recursed_token.lemma_ in self.or_lemmas:
                token._.coref_chains.temp_has_or_coordination = True
            if (
                token != recursed_token
                and token.pos_ in ("VERB", "AUX")
                and recursed_token.pos_ in ("VERB", "AUX")
                and self.is_potential_anaphor(recursed_token)
                and self.is_potential_anaphor(token)
            ):
                # we treat two verb anaphors as having or coordination because two
                # singular anaphors do not give rise to a plural phrase
                token._.coref_chains.temp_has_or_coordination = True
            if (
                recursed_token.dep_ in self.dependent_sibling_deps
                or self.has_morph(recursed_token, "Case", "Ins")
            ) and recursed_token != token:
                siblings_set.add(recursed_token)
            for child in (
                child
                for child in recursed_token.children
                if child not in visited_set
                and (
                    child.dep_ in self.dependent_sibling_deps
                    or child.dep_ in self.conjunction_deps
                )
            ):
                child_siblings_set = add_siblings_recursively(child, visited_set)
                siblings_set |= child_siblings_set
            for child in (
                child
                for child in recursed_token.children
                if recursed_token.pos_ in self.noun_pos
                and child.pos_ in self.noun_pos
                and self.has_morph(child, "Case", "Ins")
                and child not in visited_set
            ):
                child_siblings_set = add_siblings_recursively(child, visited_set)
                siblings_set |= child_siblings_set
            for child in (
                child
                for child in recursed_token.children
                if recursed_token.pos_ in ("VERB", "AUX")
                and self.is_potential_anaphor(recursed_token)
                and child.pos_ in self.noun_pos
                and self.has_morph(child, "Case", "Ins")
                and child not in visited_set
            ):
                child_siblings_set = add_siblings_recursively(child, visited_set)
                siblings_set |= child_siblings_set
            if recursed_token.dep_ != self.root_dep:
                for child in (
                    child
                    for child in recursed_token.head.children
                    if recursed_token.pos_ in self.noun_pos
                    and child.pos_ in self.noun_pos
                    and self.has_morph(child, "Case", "Ins")
                    and child not in visited_set
                ):
                    child_siblings_set = add_siblings_recursively(child, visited_set)
                    siblings_set |= child_siblings_set
            return siblings_set

        if (
            token.dep_ not in self.conjunction_deps
            and token.dep_ not in self.dependent_sibling_deps
        ):
            siblings_set = add_siblings_recursively(token, set())
        else:
            siblings_set = set()
        return sorted(siblings_set)

    def is_independent_noun(self, token: Token) -> bool:
        if token.pos_ not in self.noun_pos or token.text in punctuation:
            return False
        # if token.lemma_ in ['мы', 'вы'] and self.has_morph(token, 'Case', 'Nom'):
        #    return True
        return not self.is_token_in_one_of_phrases(token, self.blacklisted_phrases)

    def is_potential_anaphor(self, token: Token) -> bool:
        # third-person pronoun
        if token.tag_ in ("PRON", "DET"):
            return True

        # reflexive possessive pronoun
        if self.is_reflexive_possessive_pronoun(token):
            return True

        if (
            token._.coref_chains.temp_governing_sibling is not None
            and len(
                [
                    child
                    for child in token._.coref_chains.temp_governing_sibling.children
                    if child.dep_.startswith("nsubj")
                ]
            )
            > 0
        ):
            return False

        if (
            token.pos_ == "AUX"
            and token.dep_ != self.root_dep
            and len(
                [
                    child
                    for child in token.head.children
                    if child.dep_.startswith("nsubj")
                ]
            )
            > 0
        ):
            return False

        return False

    def is_potential_anaphoric_pair(
        self, referred: Mention, referring: Token, directly: bool
    ) -> int:

        # masc:     'мужской род'
        # fem:      'женский род'
        # neut:     'средний род'

        def get_gender_number_info(token):
            masc = fem = neut = False
            if token.lemma_.capitalize() in self.female_names:
                fem = True
            elif token.lemma_.capitalize() in self.male_names:
                masc = True
            else:
                # spacy has some problems identifying people names lemmas
                if token.dep_ == "flat:name" and token.lemma_.endswith("у"):
                    if (token.lemma_[:-1] + "a").capitalize() in self.female_names:
                        fem = True
                else:
                    if self.has_morph(token, "Number", "Sing"):
                        if self.has_morph(token, "Gender", "Masc"):
                            masc = True
                        elif self.has_morph(token, "Gender", "Fem"):
                            fem = True
                        elif self.has_morph(token, "Gender", "Neut"):
                            neut = True
                    else:
                        # plural form doesn't have gender, so suppose that it can reffer to anything
                        masc = fem = neut = True
                    if token.pos_ == "PROPN" and not directly:
                        # common noun and proper noun in same chain may have different genders
                        masc = fem = neut = True
            return masc, fem, neut

        doc = referring.doc
        referred_root = doc[referred.root_index]
        uncertain = False

        if directly:
            if (
                self.is_potential_reflexive_pair(referred, referring)
                and self.is_reflexive_anaphor(referring) == 0
            ):
                return False

            if (
                not self.is_potential_reflexive_pair(referred, referring)
                and self.is_reflexive_anaphor(referring) == 2
            ):
                return False

            # possessive pronouns cannot refer back to the head within a genitive phrase.
            # This functionality is under 'directly' to improve performance.
            working_token = referring
            while working_token.dep_ != self.root_dep:
                if (
                    working_token.head.i in referred.token_indexes
                    and working_token.dep_ not in self.dependent_sibling_deps
                    and self.has_morph(working_token, "Case", "Gen")
                ):
                    return False

                if (
                    working_token.dep_ not in self.dependent_sibling_deps
                    and (
                        working_token.dep_ != "nmod"
                        or not self.has_morph(working_token, "Case", "Gen")
                    )
                    and not self.is_reflexive_possessive_pronoun(working_token)
                ):
                    break
                working_token = working_token.head

        referring_governing_sibling = referring
        if referring._.coref_chains.temp_governing_sibling is not None:
            referring_governing_sibling = (
                referring._.coref_chains.temp_governing_sibling
            )
        if (
            referring_governing_sibling.dep_.startswith("nsubj")
            and referring_governing_sibling.head.lemma_
            in self.verbs_with_personal_subject
        ) or referring.lemma_ in self.verbs_with_personal_subject:
            uncertain = True
            for working_token in (doc[index] for index in referred.token_indexes):
                if (
                    working_token.pos_ == self.propn_pos
                    or working_token.ent_type_ == "persName"
                ):
                    uncertain = False

        referring_masc, referring_fem, referring_neut = get_gender_number_info(
            referring
        )

        if self.is_involved_in_non_or_conjunction(referred_root):
            if referred_root._.coref_chains.temp_governing_sibling is not None:
                all_involved_referreds = [
                    referred_root._.coref_chains.temp_governing_sibling
                ]
            else:
                all_involved_referreds = [referred_root]
            all_involved_referreds.extend(
                all_involved_referreds[0]._.coref_chains.temp_dependent_siblings
            )
        else:
            all_involved_referreds = [referred_root]

        # e.g. 'Муж и жена... Они...'
        comitative_siblings = [
            c
            for c in referring._.coref_chains.temp_dependent_siblings
            if referring.pos_ in ("VERB", "AUX")
            and self.has_morph(referring, "Number", "Plur")
        ]

        if not directly and len(comitative_siblings) > 0:
            return 1 if uncertain else 2

            # e.g. 'Я и ты... Мы...'
        if self.has_morph(referred_root, "Person", "First") or self.has_morph(
            referred_root, "Person", "Second"
        ):
            if self.has_morph(
                referring, "Person", "First"
            ) or self.is_reflexive_possessive_pronoun(referring):
                return 1 if uncertain else 2
            else:
                # case 'Вы... вы...'
                if self.has_morph(referred_root, "Person", "Second") != self.has_morph(
                    referring, "Person", "Second"
                ):
                    return 0

        all_involved_referreds.extend(comitative_siblings)
        referreds_included_here = [doc[i] for i in referred.token_indexes]
        referreds_included_here.extend(comitative_siblings)
        referred_masc = referred_fem = referred_neut = False
        if len(all_involved_referreds) > 1:

            if len(referreds_included_here) == len(all_involved_referreds):
                if not self.has_morph(referring, "Gender", "Fem"):
                    return 1 if uncertain else 2

            referred_masc, referred_fem, referred_neut = get_gender_number_info(
                referred_root
            )

            referred_comitative_siblings = [
                child
                for child in referred_root._.coref_chains.temp_dependent_siblings
                if child.i != referring.i
                and referred_root.pos_ in ("VERB", "AUX")
                and self.has_morph(referring, "Number", "Plur")
                and not (
                    self.has_morph(referring, "Person", "First")
                    or self.has_morph(referring, "Person", "Second")
                )
            ]
            if not directly and len(referred_comitative_siblings):
                return 1 if uncertain else 2

        for working_token in (doc[index] for index in referred.token_indexes):
            working_masc, working_fem, working_neut = get_gender_number_info(
                working_token
            )
            referred_masc = referred_masc or working_masc
            referred_fem = referred_fem or working_fem
            referred_neut = referred_neut or working_neut
        if referring.lemma_ != "чей":

            if (
                not (referred_masc and referring_masc)
                and not (referred_fem and referring_fem)
                and not (referred_neut and referring_neut)
            ):
                if not (self.is_reflexive_possessive_pronoun(referring)):
                    return 0

        if (
            referred_masc + referred_fem + referred_neut
            != referring_masc + referring_fem + referring_neut
        ):

            if referred_root.dep_ not in self.dependent_sibling_deps:
                if sum(
                    get_gender_number_info(referring)
                ) > 2 or self.is_reflexive_possessive_pronoun(referring):
                    if (
                        not self.has_morph(referred_root, "Case", "Ins")
                        and self.has_morph(referred_root, "Animacy", "Anim")
                        >= self.has_morph(referred_root.head, "Animacy", "Anim")
                        and not [
                            child
                            for child in referred_root.children
                            if child.dep_ == "case" and child.lemma_ == "c"
                        ]
                    ):
                        if not self.is_reflexive_possessive_pronoun(referring):
                            return 0

                if not [
                    child
                    for child in referred_root.children
                    if child.dep_ in self.dependent_sibling_deps
                ] and not self.is_reflexive_possessive_pronoun(referring):
                    if referred_root.pos_ == "PRON":
                        if not [
                            child
                            for child in referred_root.head.children
                            if child.dep_ == "obj"
                        ] or not [
                            child
                            for child in referred_root.head.children
                            if child.dep_ == "obl"
                        ]:
                            return 0
                    else:
                        return 0

        if referred_root.dep_ == "obj":
            if [
                child
                for child in referred_root.children
                if child.dep_ in self.dependent_sibling_deps
                and get_gender_number_info(child)
                == get_gender_number_info(referred_root)
            ]:
                if self.has_morph(referring, "Number", "Sing"):
                    # spacy models have a bug where they
                    # identify female names as masculine proper nouns
                    # so need to implement additional check for that
                    if [
                        child
                        for child in referred_root.children
                        if child.lemma_.capitalize() in self.female_names
                        and self.has_morph(child, "Gender", "Masc")
                    ] and self.has_morph(referring, "Gender", "Masc"):
                        return 0

        if [child for child in referred_root.children if child.dep_ == "advmod"]:
            if [child for child in referred_root.children if child.lemma_ == "но"]:
                return 0
            if [
                child
                for child in referred_root.children
                if child.dep_ in self.dependent_sibling_deps
            ]:
                return 0

        if referred_root.dep_ == "nsubj" and referred_root.head.dep_ == self.root_dep:
            if referring.lemma_.startswith("котор") and not self.has_morph(
                referring, "Case", "Gen"
            ):
                if [
                    child
                    for child in referred_root.head.children
                    if child.dep_ in ("obj", "obl")
                    and get_gender_number_info(child)
                    == get_gender_number_info(referred_root)
                    and child.i < referring.i
                ]:
                    return 0

            if [
                child
                for child in referred_root.children
                if child.dep_ == "nmod" and child.i > referred_root.i
            ]:
                if not self.is_reflexive_possessive_pronoun(referring):
                    return 0

        if referring.lemma_.startswith("котор"):
            if self.has_morph(referring, "Case", "Loc"):
                if [
                    child
                    for child in referred_root.children
                    if child.dep_ == "nmod" and self.has_morph(child, "Case", "Loc")
                ]:
                    return 0

            if referred_root.i > referring.i:
                return 0

        if referred_root.dep_ == self.root_dep:
            if [child for child in referred_root.children if child.dep_ == "nsubj"]:
                return 0

            if len([child for child in referred_root.children]) == len(
                [child for child in referred_root.children if child.dep_ == "punct"]
            ):
                return 0

            if [child for child in referred_root.children if child.dep_ == "case"] and [
                child
                for child in referred_root.children
                if child.dep_ == "nmod" and child.i > referred_root.i
            ]:
                return 0

        if self.has_morph(referred_root, "Animacy", "Inan") and self.has_morph(
            referring, "Person", "Third"
        ):
            if [
                child
                for child in referred_root.head.children
                if self.has_morph(child, "Animacy", "Anim") and child != referring
            ]:
                if referred_root.head.lemma_ not in self.verbs_with_personal_subject:
                    return 0

        if referred_root.head.pos_ == "NOUN" and referred_root.dep_ == "nmod":
            if not (
                self.has_morph(referred_root, "Animacy", "Anim")
                and self.has_morph(referred_root.head, "Animacy", "Inan")
            ):
                if referred_root.pos_ == "PROPN":
                    return 0

                if not [
                    child for child in referred_root.children if child.tag_ == "ADP"
                ]:
                    if not self.has_morph(referred_root, "Case", "Nom"):
                        return 0

                    if (
                        self.has_morph(referred_root, "Animacy", "Anim")
                        and referred_root.morph == referred_root.head.morph
                    ):
                        return 0

        if referred_root.head.pos_ == "NOUN" and referred_root.dep_ == "appos":
            if (
                self.has_morph(referred_root, "Animacy", "Anim")
                and referred_root.morph == referred_root.head.morph
            ):
                return 0

        if referred_root.pos_ == "NOUN" and referring.dep_ == "obj":
            if not self.is_reflexive_possessive_pronoun(referring):
                if not self.has_morph(referred_root, "Animacy", "Anim"):
                    if [
                        child
                        for child in referred_root.children
                        if child.dep_ == "nmod"
                        and self.has_morph(child, "Animacy", "Anim")
                    ]:
                        return 0
                else:
                    if [
                        child
                        for child in referred_root.children
                        if child.dep_ == "nmod"
                    ]:
                        return 0

        if referred_root.lemma_ == "роль" and referred_root.head.lemma_ == "играть":
            return 0

        if referring.lemma_.startswith("какой"):
            return 0

        if (
            referred_root.lemma_.endswith(".")
            and referred_root.pos_ in self.propn_pos
            and self.has_morph(referred_root, "Animacy", "Anim")
        ):
            return 0

        if len(referred_root.lemma_) == 1 and referred_root.pos_ != "PRON":
            return 0

        if referring.pos_ == "DET":
            if referring.lemma_.startswith("наш"):
                if not (
                    referred_root.lemma_.startswith("наш")
                    or referred_root.lemma_.startswith("мы")
                ):
                    return 0

            if referring.lemma_.startswith("ваш"):
                if not (
                    referred_root.lemma_.startswith("ваш")
                    or referred_root.lemma_.startswith("вы")
                ):
                    return 0

            if referring.lemma_.startswith("весь") and self.has_morph(
                referring, "Case", "Nom"
            ):
                if not [child for child in referring.children if child.dep_ != "cc"]:
                    if referring.dep_ in ("ROOT", "conj"):
                        return 0

            if referring.head.pos_ == "NOUN":
                if not self.is_reflexive_possessive_pronoun(
                    referring
                ) and not self.has_morph(referring, "Case", "Nom"):
                    return 0

                if referring.head.dep_ in self.dependent_sibling_deps:
                    return 0

        if not self.is_reflexive_possessive_pronoun(referring):

            if (
                self.has_morph(referring, "Person", "First")
                and not self.has_morph(referred_root, "Person", "First")
            ) or (
                self.has_morph(referred_root, "Person", "First")
                and not self.has_morph(referring, "Person", "First")
            ):
                return 0

            if (
                self.has_morph(referring, "Person", "Second")
                and not self.has_morph(referred_root, "Person", "Second")
            ) or (
                self.has_morph(referred_root, "Person", "Second")
                and not self.has_morph(referring, "Person", "Second")
            ):
                return 0

        if self.is_reflexive_possessive_pronoun(referred_root):
            if (
                referred_root.head.pos_ == "NOUN"
                and referred_root.head.dep_ == "obj"
                and self.has_morph(referred_root.head, "Case", "Acc")
            ):
                return 0

            if self.has_morph(referred_root, "Case", "Loc") and get_gender_number_info(
                referred_root.head
            ) == get_gender_number_info(referring):
                return 0

        if self.has_morph(referred_root, "Case", "Nom"):
            if referred_root.head.lemma_ in self.verbs_with_personal_subject:
                if [
                    child
                    for child in referred_root.head.children
                    if child.tag_ in self.noun_pos
                ]:
                    return 0

        if self.has_morph(referred_root, "Animacy", "Anim"):
            if [
                child
                for child in referred_root.children
                if child.dep_ == "amod" and self.has_morph(child, "Animacy", "Anim")
            ]:
                return 0

        if [
            child
            for child in referred_root.children
            if child.dep_ in self.dependent_sibling_deps
        ]:
            if self.has_morph(referring, "Number", "Sing") and self.has_morph(
                referring.head, "Number", "Plur"
            ):
                return 0

        if referring.head == referred_root:
            return 0

        if referred_root.sent.text != referring.sent.text:
            # if there is a sentence inbetween then need to check if it contains potential anaphor
            # and if so, then current sentence can not have valid referred root
            if (
                " ".join([referred_root.sent.text, referring.sent.text]) not in doc.text
                and referred_root.i < referring.i
            ):
                temp_index = referring.i
                while True:
                    temp_index -= 1
                    temp_token = doc[temp_index]
                    if temp_index == referred_root.i:
                        break
                    if temp_token.sent.text == referring.sent.text:
                        continue
                    if self.is_independent_noun(temp_token):
                        if self.is_potential_anaphoric_pair(
                            Mention(doc[temp_token.i], False), referring, directly
                        ):
                            return 0

        return 1 if uncertain else 2

    def is_potentially_indefinite(self, token: Token) -> bool:

        if token.pos_ != "NOUN":
            return False
        for child in (
            child for child in token.children if child.pos_ in self.term_operator_pos
        ):
            if child.lemma_.lower() in ("тот", "этот", "такой"):
                return False
            # Какой-то
            if child.lemma_ == "-" and child.nbor().lemma_ == "то":
                return True
            if (
                child.pos_ == "DET"
                and child.tag_ == "ADJ"
                and child.dep_.startswith("det")
                and self.has_morph(child, "Poss", "Yes")
            ):
                return False
            if (
                child.pos_ == "DET"
                and child.tag_ == "DET"
                and child.lemma_.lower() != "какой"
            ):
                return False
        return True

    def is_potentially_definite(self, token: Token) -> bool:
        if token.pos_ == "PROPN":
            return True
        if token.pos_ != "NOUN":
            return False
        for child in (
            child for child in token.children if child.pos_ in self.term_operator_pos
        ):
            if child.lemma_.lower().startswith("как"):
                return False
        for child in (
            child for child in token.children if child.pos_ in self.term_operator_pos
        ):
            if child.tag_ in ("ADJ", "DET"):
                break
        else:
            return False
        return True

    def is_reflexive_anaphor(self, token: Token) -> int:
        if self.is_reflexive_possessive_pronoun(token):
            return 2
        if token.tag_ == "PRON":
            if token.dep_ == "nmod" and self.has_morph(token, "Case", "Acc"):
                return 1
            if (
                token.dep_ == "obl"
                and self.has_morph(token, "Case", "Ins")
                and not self.has_morph(token, "Person", "Third")
            ):
                # e.g. 'его, ее, их' or 'вами', 'нами'
                return 1
        return 0

    def is_potential_reflexive_pair(self, referred: Mention, referring: Token) -> bool:

        if referring.pos_ != "PRON" and not self.is_reflexive_possessive_pronoun(
            referring
        ):
            return False
        if referring.lemma_.startswith("котор"):
            return False
        referred_root = referring.doc[referred.root_index]

        if referred_root._.coref_chains.temp_governing_sibling is not None:
            referred_root = referred_root._.coref_chains.temp_governing_sibling

        if referring._.coref_chains.temp_governing_sibling is not None:
            referring = referring._.coref_chains.temp_governing_sibling

        if referred_root.dep_.startswith("nsubj") or (
            referred_root.pos_ in ("VERB", "AUX")
            and self.is_potential_anaphor(referred_root)
        ):
            referring_and_ancestors = [referring]
            referring_and_ancestors.extend(list(referring.ancestors))
            for referring_or_ancestor in referring_and_ancestors:

                # Loop up through the ancestors of the pronoun

                if (
                    referred_root == referring_or_ancestor
                    or referred_root in referring_or_ancestor.children
                ):
                    return True

                # Relative clauses
                if (
                    referring_or_ancestor.pos_ in ("VERB", "AUX")
                    and referring_or_ancestor.dep_.startswith("acl")
                    and (
                        referring_or_ancestor.head == referred_root
                        or referring_or_ancestor.head.i in referred.token_indexes
                    )
                ):
                    return True

                # The ancestor has its own subject, so stop here
                if [
                    t
                    for t in referring_or_ancestor.children
                    if t.dep_.startswith("nsubj") and t != referred_root
                ]:
                    return False

                if (
                    referring_or_ancestor._.coref_chains.temp_governing_sibling
                    == referred_root
                ):
                    return False

        return (
            referring.dep_ != self.root_dep
            and referred_root.dep_ != self.root_dep
            and (
                referring.head == referred_root.head
                or referring.head.i in referred.token_indexes
            )
            and referring.i > referred_root.i
        )
