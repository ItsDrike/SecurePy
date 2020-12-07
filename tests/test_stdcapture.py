import unittest

from securepy.stdcapture import LimitedStringIO, MemoryOverflow


class LimitedStringIOTests(unittest.TestCase):
    """Tests for StringIO with limiting maximum memory."""

    def test_valid_limits(self):
        """Make sure writing within given limits works properly."""
        test_cases = (
            (LimitedStringIO(1_000_000), ("test")),  # Under specified limit
            (LimitedStringIO(1_000_000), ("test", "hi", "hello")),  # Multiple writes under limit
            (LimitedStringIO(103), ("hello")),  # Exactly at the limit
        )

        for limitedStringIO, test_strings in test_cases:
            with self.subTest(memory_size=limitedStringIO.max_memory, test_strings=test_strings):
                for test_string in test_strings:
                    limitedStringIO.write(test_string)
                self.assertEqual(limitedStringIO.getvalue(), "".join(test_strings))

    def test_invalid_limits(self):
        """Make sure writing strings over allowed size won't work."""
        test_cases = (
            (LimitedStringIO(1), ("test",), 102),  # 101 above the limit
            (LimitedStringIO(102), ("hello"), 103),  # 1 above the limit
            (LimitedStringIO(120), ("hello", "hey there", "hi", "itsdrike"), 122)  # Multiple writes, fail on last
        )

        for limitedStringIO, test_strings, test_memory in test_cases:
            with self.subTest(max_memory_size=limitedStringIO.max_memory, given_memory_size=test_memory, test_strings=test_strings):
                try:
                    for test_string in test_strings:
                        limitedStringIO.write(test_string)
                except Exception as e:
                    self.assertIsInstance(e, MemoryOverflow)
                    if isinstance(e, MemoryOverflow):
                        self.assertEqual(e.used_memory, test_memory)
