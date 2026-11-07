import unittest

import numpy as np

from scripts.replay_rcaeval import Replay, expected_gain, replay


class EvidenceReplayTest(unittest.TestCase):
    def test_identical_outcome_distributions_have_no_information_gain(self) -> None:
        likelihoods = np.array([[0.2, 0.3, 0.5], [0.2, 0.3, 0.5]])
        self.assertAlmostEqual(expected_gain(np.array([0.4, 0.6]), 1, likelihoods), 0.0)

    def test_first_choice_does_not_use_hidden_outcomes_or_the_label(self) -> None:
        likelihoods = np.array([[0.8, 0.1, 0.1], [0.1, 0.1, 0.8]])
        prior = np.array([0.6, 0.4])
        visible = np.zeros((2, 3))
        a = Replay("a", "api", ["api", "db"], visible, {"api": 0, "db": 2})
        b = Replay("b", "db", ["api", "db"], visible, {"api": 2, "db": 0})
        first = replay(a, prior, likelihoods, "information_gain")[1]["checks"][0]
        second = replay(b, prior, likelihoods, "information_gain")[1]["checks"][0]
        self.assertEqual(first["service"], second["service"])
        self.assertNotEqual(first["outcome_bin"], second["outcome_bin"])
