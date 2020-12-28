import time
import unittest

from securepy import IOCage, IOTimedFunction, TimedFunction, TimedFunctionError


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

    @staticmethod
    def error_function():
        raise RuntimeError("some error")

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
        with self.assertRaises(TimeoutError):
            limiter.run_timed(self.slow_function)

    def test_function_error(self):
        """Test exception in internal function which runs timed."""
        limiter = TimedFunction(1)
        with self.assertRaisesRegex(TimedFunctionError, "some error"):
            limiter.run_timed(self.error_function)


class IOTimedFunctionTests(unittest.TestCase):
    """Tests for IOTimedFunction time limiting and capturing capabilities."""

    @staticmethod
    def fast_function():
        """This function is used as example test case."""
        time.sleep(0.3)
        print("test")
        return 1

    @staticmethod
    def slow_function():
        """This function is used as example test case."""
        time.sleep(3)
        print("test")
        return 1

    @staticmethod
    def error_function():
        raise RuntimeError("some error")

    def test_wrapper(self):
        """Test wrapper implementation of TimedFunction execution."""
        io_cage = IOCage()
        limiter = IOTimedFunction(time_limit=1, io_cage=io_cage)

        ret = limiter.run_timed(self.fast_function)

        self.assertEqual(ret, 1)
        self.assertEqual(io_cage.stdout, "test\n")

    def test_decorator(self):
        """Test wrapper implementation of TimedFunction execution."""
        io_cage = IOCage()

        @IOTimedFunction(time_limit=1, io_cage=io_cage)
        def fn():
            return self.fast_function()

        ret = fn()
        self.assertEqual(ret, 1)
        self.assertEqual(io_cage.stdout, "test\n")

    def test_timeout(self):
        """Test function over timelimit."""
        io_cage = IOCage()
        limiter = IOTimedFunction(time_limit=1, io_cage=io_cage)

        with self.assertRaises(TimeoutError):
            limiter.run_timed(self.slow_function)

    def test_function_error(self):
        """Test exception in internal function which runs timed."""
        io_cage = IOCage()
        limiter = IOTimedFunction(time_limit=1, io_cage=io_cage)
        with self.assertRaisesRegex(TimedFunctionError, "some error"):
            limiter.run_timed(self.error_function)

        # We should be raising `TimedFunctionError` only, not capturing traceback into stderr
        self.assertEqual(io_cage.stderr, "")
