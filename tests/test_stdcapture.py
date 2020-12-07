import sys
import unittest

from securepy.stdcapture import LimitedStringIO, MemoryOverflow, StdCapture


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


class StdCaptureTests(unittest.TestCase):
    """Tests for the STDOUT/STDERR capturing."""

    def test_manual_capture(self):
        _original_stdout = sys.stdout
        captured = StdCapture()

        captured.override_std()
        print("hello")
        self.assertIsNot(sys.stdout, _original_stdout)
        captured.restore_std()
        self.assertIs(sys.stdout, _original_stdout)

    def test_context_manager(self):
        """Make sure context manager implementation of StdCapture works."""
        _original_stdout = sys.stdout
        captured = StdCapture()

        with captured:
            self.assertIsNot(sys.stdout, _original_stdout)
            print("test string")

        self.assertEqual(captured.stdout, "test string\n")
        self.assertIs(sys.stdout, _original_stdout)

    def test_decorator(self):
        """Make sure context manager implementation of StdCapture works."""
        _original_stdout = sys.stdout
        captured = StdCapture()

        @captured
        def foo():
            self.assertIsNot(sys.stdout, _original_stdout)
            print("test string")

        foo()

        self.assertEqual(captured.stdout, "test string\n")
        self.assertIs(sys.stdout, _original_stdout)

    def test_decorator_arguments(self):
        """Make sure context manager implementation of StdCapture works."""
        _original_stdout = sys.stdout
        captured = StdCapture()

        @captured
        def foo(my_string, my_kwarg="default"):
            self.assertIsNot(sys.stdout, _original_stdout)
            print(my_string + my_kwarg)

        foo("test ", my_kwarg="string")

        self.assertEqual(captured.stdout, "test string\n")
        self.assertIs(sys.stdout, _original_stdout)

    def test_wrapper(self):
        """Make sure context manager implementation of StdCapture works."""
        _original_stdout = sys.stdout
        captured = StdCapture()

        def foo():
            self.assertIsNot(sys.stdout, _original_stdout)
            print("test string")

        captured.capture(foo)

        self.assertEqual(captured.stdout, "test string\n")
        self.assertIs(sys.stdout, _original_stdout)

    def test_wrapper_arguments(self):
        _original_stdout = sys.stdout
        captured = StdCapture()

        def foo(my_string, my_kwarg="default"):
            self.assertIsNot(sys.stdout, _original_stdout)
            print(my_string + my_kwarg)

        captured.capture(foo, args=("test ", ), kwargs={"my_kwarg": "string"})

        self.assertEqual(captured.stdout, "test string\n")
        self.assertIs(sys.stdout, _original_stdout)

    def test_capture(self):
        test_cases = (
            ("foo",),  # Single print
            ("python", "is", "cool"),  # Multiple prints
            (None, ),  # No print
        )

        for test_prints in test_cases:
            with self.subTest(test_prints=test_prints):
                capture = StdCapture()

                with capture:
                    for test_print in test_prints:
                        if test_print is not None:
                            print(test_print)

                expected_stdout = "\n".join(s for s in test_prints if s is not None)
                expected_stdout = expected_stdout + "\n" if not expected_stdout == "" else expected_stdout
                self.assertEqual(capture.stdout, expected_stdout)

    def test_auto_reset(self):
        captured = StdCapture(auto_reset=True)

        with captured:
            print("print1")
        self.assertEqual(captured.stdout, "print1\n")

        with captured:
            print("print2")
        self.assertEqual(captured.stdout, "print2\n")

    def test_no_auto_reset(self):
        captured = StdCapture(auto_reset=False)

        with captured:
            print("print1")

        with captured:
            print("print2")

        self.assertEqual(captured.stdout, "print1\nprint2\n")

    def test_manual_reset(self):
        captured = StdCapture(auto_reset=False)

        with captured:
            print("print1")
        self.assertEqual(captured.stdout, "print1\n")

        captured.reset()

        with captured:
            print("print2")
        self.assertEqual(captured.stdout, "print2\n")
