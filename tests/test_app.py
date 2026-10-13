import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server


class MatchingTests(unittest.TestCase):
    def setUp(self):
        self.profiles = server.SEED_PROFILES

    def test_has_25_fictional_demo_profiles(self):
        self.assertEqual(len(self.profiles), 25)
        self.assertTrue(all(p['is_demo'] for p in self.profiles))
        self.assertEqual(len({p['id'] for p in self.profiles}), 25)

    def test_demo_profiles_are_adults_and_have_two_or_more_interests(self):
        for p in self.profiles:
            self.assertGreaterEqual(p['age'], 18)
            self.assertGreaterEqual(len(p['interests']), 2)
            self.assertTrue(p['values'])

    def test_score_is_symmetric_and_bounded(self):
        a, b = self.profiles[0], self.profiles[1]
        ab = server.score_pair(a, b)
        ba = server.score_pair(b, a)
        self.assertEqual(ab['score'], ba['score'])
        self.assertGreaterEqual(ab['score'], 0)
        self.assertLessEqual(ab['score'], 100)

    def test_rankings_exclude_self_and_are_descending(self):
        profile = self.profiles[0]
        ranked = server.rankings_for(profile, self.profiles)
        self.assertEqual(len(ranked), 24)
        self.assertNotIn(profile['id'], [r['profile']['id'] for r in ranked])
        scores = [r['score'] for r in ranked]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_simulated_date_has_two_agents_and_never_contacts_people(self):
        date = server.simulate_date(self.profiles[0], self.profiles[1])
        self.assertEqual(len(date['dialogue']), 4)
        self.assertIn('does not contact anyone', date['notice'])
        self.assertGreaterEqual(date['match']['score'], 0)

    def test_only_exact_social_platform_hosts_are_accepted(self):
        self.assertTrue(server.validate_url('https://www.linkedin.com/in/example-person', 'linkedin.com'))
        self.assertTrue(server.validate_url('https://www.instagram.com/example.person/', 'instagram.com'))
        self.assertFalse(server.validate_url('https://notlinkedin.com/in/example', 'linkedin.com'))
        self.assertFalse(server.validate_url('https://linkedin.com.evil.example/in/x', 'linkedin.com'))
        self.assertFalse(server.validate_url('https://evil.linkedin.com/in/x', 'linkedin.com'))

    def test_profile_intake_requires_explicit_consent(self):
        payload = {
            'name': 'Sample Adult', 'age': 29, 'city': 'Delhi',
            'bio': 'I enjoy reading, cycling and thoughtful conversations.',
            'interests': ['reading', 'cycling'], 'values': ['kindness'],
            'goal': 'long-term relationship', 'style': 'thoughtful',
            'min_age': 24, 'max_age': 35,
            'linkedin_url': 'https://www.linkedin.com/in/sample-adult',
            'instagram_url': 'https://www.instagram.com/sample.adult/',
            'consent': False,
        }
        profile, errors = server.validate_profile(payload)
        self.assertIsNone(profile)
        self.assertTrue(any('explicitly agreed' in e for e in errors))
        payload['consent'] = True
        profile, errors = server.validate_profile(payload)
        self.assertEqual(errors, [])
        self.assertEqual(profile['age'], 29)
        self.assertFalse(profile['is_demo'])

    def test_profile_intake_rejects_minors(self):
        payload = {
            'name': 'Sample Person', 'age': 17, 'city': 'Delhi',
            'bio': 'I enjoy reading, cycling and thoughtful conversations.',
            'interests': ['reading', 'cycling'], 'values': ['kindness'],
            'goal': 'long-term relationship', 'style': 'thoughtful',
            'min_age': 18, 'max_age': 25,
            'linkedin_url': 'https://www.linkedin.com/in/sample-person',
            'instagram_url': 'https://www.instagram.com/sample.person/',
            'consent': True,
        }
        profile, errors = server.validate_profile(payload)
        self.assertIsNone(profile)
        self.assertTrue(any('adults' in e for e in errors))


if __name__ == '__main__':
    unittest.main(verbosity=2)
