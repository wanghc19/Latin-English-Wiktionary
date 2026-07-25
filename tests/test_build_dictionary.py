import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from build_dictionary import (  # noqa: E402
    DICTIONARY_NS,
    definition_for,
    parse_heading,
    render_entry,
)


def entry(word, pos, expansion=None, forms=None, senses=None, args=None):
    head_templates = []
    if expansion is not None:
        head_templates = [{"name": "head", "args": args or {}, "expansion": expansion}]
    return {
        "word": word,
        "pos": pos,
        "head_templates": head_templates,
        "forms": forms or [],
        "senses": senses or [],
    }


def parse_fragment(xml):
    wrapper = ET.fromstring(f'<root xmlns:d="{DICTIONARY_NS}">{xml}</root>')
    return wrapper[0]


class HeadingTests(unittest.TestCase):
    def test_dies_matches_reference_layout(self):
        source = entry(
            "dies",
            "noun",
            "diēs m or f (genitive diēī); fifth declension",
            senses=[{"glosses": ["A day", "A set day"]}],
        )
        heads, subtitle, fallback = parse_heading(source)
        self.assertEqual(heads, ["diēs"])
        self.assertEqual(subtitle, "m or f (genitive diēī); fifth declension")
        self.assertFalse(fallback)

        xml, _ = render_entry(source, 140)
        self.assertIn('<span class="gender">m</span> or <span class="gender">f</span>', xml)
        self.assertIn("1. A day — A set day", xml)

    def test_castra_keeps_neuter_and_plural_visibly_separate(self):
        source = entry(
            "castra",
            "noun",
            "castra n pl (genitive castrōrum); second declension",
            senses=[{"glosses": ["an encampment, military camp"]}],
        )
        xml, _ = render_entry(source, 12412)
        self.assertIn('<span class="gender">n</span> <span class="number">pl</span>', xml)
        self.assertNotIn(">npl<", xml)

    def test_ais_uses_italic_or_between_three_heads(self):
        source = entry(
            "ais",
            "verb",
            "ais or aīs or a͡is",
            senses=[
                {
                    "glosses": [
                        "second-person singular present active indicative of aiō"
                    ]
                }
            ],
        )
        xml, _ = render_entry(source, 16189)
        self.assertIn(
            '<span class="headword">ais</span> <em class="headword-separator">or</em> '
            '<span class="headword">aīs</span> <em class="headword-separator">or</em> '
            '<span class="headword">a͡is</span>',
            xml,
        )
        root = parse_fragment(xml)
        indexes = [
            node.attrib[f"{{{DICTIONARY_NS}}}value"]
            for node in root.findall(f"{{{DICTIONARY_NS}}}index")
        ]
        self.assertEqual(indexes, ["ais", "aīs", "a͡is"])
        self.assertNotIn("subhead", xml)

    def test_missing_template_falls_back_to_canonical_form(self):
        source = entry(
            "time",
            "verb",
            forms=[{"form": "timē", "tags": ["canonical"]}],
            senses=[{"glosses": ["imperative of timeō"]}],
        )
        heads, subtitle, fallback = parse_heading(source)
        self.assertEqual(heads, ["timē"])
        self.assertEqual(subtitle, "")
        self.assertTrue(fallback)

    def test_corrupt_canonical_fallback_uses_raw_word(self):
        source = entry(
            "summas",
            "adj",
            forms=[
                {
                    "form": "Third-declension one-termination adjective.",
                    "tags": ["canonical"],
                }
            ],
        )
        heads, _, fallback = parse_heading(source)
        self.assertEqual(heads, ["summas"])
        self.assertTrue(fallback)

    def test_canonical_metadata_does_not_pollute_heading(self):
        source = entry(
            "eo",
            "verb",
            "eō (present infinitive īre); irregular conjugation",
            forms=[
                {"form": "eō", "tags": ["canonical"]},
                {"form": "irregular conjugation", "tags": ["canonical"]},
            ],
            senses=[{"glosses": ["to go"]}],
        )
        heads, _, _ = parse_heading(source)
        self.assertEqual(heads, ["eō"])

    def test_missing_gloss_uses_form_of_fallback(self):
        source = entry(
            "veterans",
            "verb",
            "veterāns (genitive veterantis); participle",
            senses=[{"form_of": [{"word": "veterō"}]}],
        )
        xml, stats = render_entry(source, 8344)
        self.assertIn("1. form of veterō", xml)
        self.assertNotIn("Definition unavailable", xml)
        self.assertEqual(stats["missing_definition"], 0)

    def test_thesaurus_entry_uses_synonyms_when_gloss_is_missing(self):
        source = entry(
            "homo stultus",
            "noun",
            senses=[{"synonyms": [{"word": "asinus"}, {"word": "bārō"}]}],
        )
        xml, _ = render_entry(source, 883915)
        self.assertIn("1. synonyms: asinus, bārō", xml)

    def test_explicit_override_replaces_known_bad_source_fields(self):
        source = entry(
            "broken",
            "noun",
            "bad template output",
            senses=[{"glosses": ["bad definition"]}],
        )
        xml, stats = render_entry(
            source,
            10,
            {
                "heads": ["correct"],
                "subtitle": "n pl",
                "definitions": ["correct definition"],
            },
        )
        self.assertIn('d:title="correct"', xml)
        self.assertIn('<span class="gender">n</span> <span class="number">pl</span>', xml)
        self.assertIn("1. correct definition", xml)
        self.assertEqual(stats["overridden_heads"], 1)
        self.assertEqual(stats["overridden_subtitles"], 1)
        self.assertEqual(stats["overridden_definitions"], 1)

    def test_xml_special_characters_are_escaped(self):
        source = entry(
            "a&b",
            "phrase",
            "a&b",
            senses=[{"glosses": ["less < more & equal"]}],
        )
        xml, _ = render_entry(source, 1)
        parse_fragment(xml)
        self.assertIn("a&amp;b", xml)
        self.assertIn("less &lt; more &amp; equal", xml)


class DefinitionTests(unittest.TestCase):
    def test_repeated_parent_gloss_is_replaced_by_qualified_leaf(self):
        sense = {
            "glosses": ["blind", "blind (not seeing)"],
            "raw_glosses": ["blind", "(literally) blind (not seeing)"],
        }
        self.assertEqual(definition_for(sense), "(literally) blind (not seeing)")

    def test_distinct_parent_and_leaf_are_joined_as_a_hierarchy(self):
        sense = {
            "glosses": ["blind", "without buds or eyes"],
            "raw_glosses": [
                "blind",
                "(transferred sense, botany) without buds or eyes",
            ],
        }
        self.assertEqual(
            definition_for(sense),
            "blind — (transferred sense, botany) without buds or eyes",
        )

    def test_prefix_without_word_boundary_is_not_treated_as_repetition(self):
        sense = {"glosses": ["snail", "snailshell"]}
        self.assertEqual(definition_for(sense), "snail — snailshell")

    def test_colon_parent_sense_is_suppressed_before_its_children(self):
        source = entry(
            "mori",
            "noun",
            senses=[
                {
                    "glosses": ["inflection of mōrus"],
                    "raw_glosses": ["inflection of mōrus:"],
                },
                {"glosses": ["inflection of mōrus:", "nominative plural"]},
                {"glosses": ["inflection of mōrus:", "genitive singular"]},
            ],
        )
        xml, stats = render_entry(source, 1)
        self.assertNotIn("1. inflection of mōrus:</p>", xml)
        self.assertIn("1. inflection of mōrus: nominative plural", xml)
        self.assertIn("2. inflection of mōrus: genitive singular", xml)
        self.assertEqual(stats["suppressed_colon_parent_definitions"], 1)

    def test_non_colon_parent_sense_is_preserved(self):
        source = entry(
            "cum",
            "conj",
            senses=[
                {"glosses": ["[with indicative]"]},
                {"glosses": ["[with indicative]", "when, while"]},
            ],
        )
        xml, stats = render_entry(source, 1)
        self.assertIn("1. [with indicative]", xml)
        self.assertIn("2. [with indicative] — when, while", xml)
        self.assertEqual(stats["suppressed_colon_parent_definitions"], 0)

    def test_single_gloss_colon_extension_is_suppressed(self):
        source = entry(
            "passus",
            "noun",
            senses=[
                {"glosses": ["pace"]},
                {"glosses": ["pace: a Roman unit of length equal to five Roman feet"]},
            ],
        )
        xml, stats = render_entry(source, 1)
        self.assertNotIn(">1. pace</p>", xml)
        self.assertIn("1. pace: a Roman unit of length equal to five Roman feet", xml)
        self.assertEqual(stats["suppressed_colon_parent_definitions"], 1)

    def test_shared_colon_qualifier_does_not_suppress_a_definition(self):
        source = entry(
            "magnus",
            "adj",
            senses=[
                {
                    "glosses": ["great, large, big"],
                    "raw_glosses": ["(literally):", "great, large, big"],
                },
                {
                    "glosses": ["especially:", "great, much, abundant"],
                    "raw_glosses": [
                        "(literally):",
                        "especially:",
                        "great, much, abundant",
                    ],
                },
            ],
        )
        xml, stats = render_entry(source, 1)
        self.assertIn("1. (literally): great, large, big", xml)
        self.assertIn("2. (literally): especially: great, much, abundant", xml)
        self.assertEqual(stats["suppressed_colon_parent_definitions"], 0)


if __name__ == "__main__":
    unittest.main()
