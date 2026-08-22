import unittest

from corpus import RubricChunk
from retrieval import EmbeddedCorpus, RetrievalError, cosine_similarity, format_evidence, rank_matches


class RetrievalTests(unittest.TestCase):
    def test_cosine_similarity_is_one_for_identical_vectors(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 2.0], [1.0, 2.0]), 1.0)

    def test_evidence_is_labeled(self):
        chunk = RubricChunk("DA-01", "data analytics", "Data analyst evidence", "Use decision context.")
        match = type("Match", (), {"chunk": chunk, "score": 0.9})()
        self.assertIn("RUBRIC DA-01", format_evidence([match]))

    def test_ranking_returns_the_nearest_chunk(self):
        data = RubricChunk("DA-01", "data", "Data", "Data criteria")
        marketing = RubricChunk("MKT-01", "marketing", "Marketing", "Marketing criteria")
        index = EmbeddedCorpus(chunks=[data, marketing], embeddings=[[1.0, 0.0], [0.0, 1.0]])
        self.assertEqual(rank_matches([0.9, 0.1], index)[0].chunk.chunk_id, "DA-01")

    def test_ranking_refuses_an_unreliable_match(self):
        chunk = RubricChunk("GEN-01", "general", "General", "General criteria")
        index = EmbeddedCorpus(chunks=[chunk], embeddings=[[1.0, 0.0]])
        with self.assertRaises(RetrievalError):
            rank_matches([0.0, 1.0], index)
