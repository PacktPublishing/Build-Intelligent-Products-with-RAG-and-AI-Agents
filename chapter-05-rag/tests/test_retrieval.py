import unittest

from corpus import RubricChunk
from retrieval import EmbeddedCorpus, RetrievalError, cosine_similarity, format_evidence, rank_matches


class RetrievalTests(unittest.TestCase):
    def test_cosine_similarity_is_one_for_identical_vectors(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 2.0], [1.0, 2.0]), 1.0)

    def test_cosine_similarity_rejects_invalid_shapes(self):
        with self.assertRaises(Exception):
            cosine_similarity([1.0], [1.0, 2.0])

    def test_evidence_is_labeled(self):
        chunk = RubricChunk("DA-01", "data analytics", "Data analyst evidence", "Use decision context.")
        match = type("Match", (), {"chunk": chunk, "score": 0.9})()
        evidence = format_evidence([match])
        self.assertIn("RUBRIC DA-01", evidence)
        self.assertIn("Use decision context.", evidence)

    def test_embedded_corpus_keeps_vectors_with_chunks(self):
        chunk = RubricChunk("GEN-01", "general", "General", "Useful evidence.")
        index = EmbeddedCorpus(chunks=[chunk], embeddings=[[0.2, 0.4]])
        self.assertEqual(index.chunks[0].chunk_id, "GEN-01")
        self.assertEqual(len(index.embeddings), 1)

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


if __name__ == "__main__":
    unittest.main()
