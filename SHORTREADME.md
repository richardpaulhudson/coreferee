*Current status*: Coreferee is maintained for compatibility with current spaCy releases. The current release supports Python 3.10–3.13 and spaCy 3.7–3.8, while retaining compatibility with selected earlier spaCy versions.

Coreferences are situations where two or more words within a text refer to the same entity, e.g. _**John** went home because **he** was tired_. Resolving coreferences is an important general task within the natural language processing field.

Coreferee is a Python 3 library for resolving coreferences in English, French, German and Polish texts using spaCy. It is designed to work effectively with the relatively limited amounts of annotated coreference data available for many languages. Language-specific grammatical rules eliminate implausible antecedents, while a neural ensemble using spaCy's syntactic, morphological and vector representations ranks the remaining candidates. The architecture separates language-specific rules from the common inference machinery, making it straightforward to add support for further languages.

Coreference decisions are made in the context of the emerging coreference chain rather than independently. When adding a new mention, the annotator checks compatibility with other members of the chain; if a later decision exposes an inconsistency, it can backtrack over recent assignments and try alternative antecedents.

The library was originally developed at [msg systems](https://www.msg.group/en) and was also maintained for a while at [Explosion AI](https://explosion.ai).

For more information, please see the [main documentation on GitHub](https://github.com/richardpaulhudson/coreferee).