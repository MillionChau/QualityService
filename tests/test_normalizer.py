from app.dictionary.aho_corasick import DictionaryAutomaton
from app.clients.elasticsearch_client import ElasticsearchClient
from app.pipeline.normalizer import TextNormalizer


def test_normalizer_aho_corasick_replacement():
    automaton = DictionaryAutomaton()
    automaton.load_dictionary()
    es_client = ElasticsearchClient()  # Disabled mode by default
    normalizer = TextNormalizer(automaton, es_client)

    raw_text = "Học javscript thấy ko hiểu nhưng đc cái vui."
    normalized, issues, counts = normalizer.normalize(raw_text)

    assert "javascript" in normalized
    assert "không" in normalized
    assert "được" in normalized

    assert counts["teencode_count"] >= 2
    assert counts["typo_count"] >= 1
    assert len(issues) >= 3
