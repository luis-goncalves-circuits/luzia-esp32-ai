import unittest

from pydantic import ValidationError

from luzia_server import ChatMessage, ChatRequest, bounded_int, parse_boolean


class ToolArgumentValidationTests(unittest.TestCase):
    def test_string_false_is_false(self):
        self.assertFalse(parse_boolean("false"))

    def test_string_true_is_true(self):
        self.assertTrue(parse_boolean("true"))

    def test_boolean_parser_rejects_ambiguous_values(self):
        with self.assertRaises(ValueError):
            parse_boolean("maybe")

    def test_integer_values_are_clamped(self):
        self.assertEqual(bounded_int(300, default=100, minimum=0, maximum=255), 255)
        self.assertEqual(bounded_int(-5, default=100, minimum=0, maximum=255), 0)

    def test_integer_parser_rejects_booleans(self):
        with self.assertRaises(ValueError):
            bounded_int(True, default=100, minimum=0, maximum=255)

    def test_integer_parser_rejects_floats(self):
        with self.assertRaises(ValueError):
            bounded_int(12.5, default=100, minimum=0, maximum=255)

    def test_integer_parser_accepts_integer_strings(self):
        self.assertEqual(bounded_int("42", default=100, minimum=0, maximum=255), 42)

    def test_chat_history_is_limited_to_twenty_messages(self):
        history = [ChatMessage(role="user", content=f"Mensagem {index}") for index in range(21)]
        with self.assertRaises(ValidationError):
            ChatRequest(message="Teste", history=history)


if __name__ == "__main__":
    unittest.main()
