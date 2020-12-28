import time
import unittest

from securepy import TimedFunction, TimedFunctionError


class TimedFunctionTests(unittest.TestCase):
    """Tests for TimedFunction time limiting capabilities."""

    @staticmethod
    def fast_function():
        """This function is used as example test case."""
        time.sleep(0.3)
        return 1

    @staticmethod
    def slow_function():
        """This function is used as example test case."""
        time.sleep(3)
        return 1

    def test_wrapper(self):
        """Test wrapper implementation of TimedFunction execution."""
        limiter = TimedFunction(1)
        ret = limiter.run_timed(self.fast_function)
        self.assertEqual(ret, 1)

    def test_decorator(self):
        """Test wrapper implementation of TimedFunction execution."""
        @TimedFunction(1)
        def fn():
            return self.fast_function()

        ret = fn()
        self.assertEqual(ret, 1)

    def test_timeout(self):
        """Test function over timelimit."""
        limiter = TimedFunction(1)
        limiter(self.slow_function)
        self.assertRaises(TimedFunctionError)
