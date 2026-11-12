import unittest
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from pydantic import ValidationError

from luzia_server import (
    ChatMessage,
    ChatRequest,
    Esp32Client,
    bounded_int,
    is_access_token_valid,
    parse_boolean,
    app,
)


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


    def test_access_token_is_optional_for_local_default(self):
        self.assertTrue(is_access_token_valid(None, ""))

    def test_access_token_accepts_correct_value(self):
        self.assertTrue(is_access_token_valid("local-secret", "local-secret"))

    def test_access_token_rejects_missing_or_wrong_value(self):
        self.assertFalse(is_access_token_valid(None, "local-secret"))
        self.assertFalse(is_access_token_valid("wrong", "local-secret"))


    def test_control_endpoint_rejects_missing_token_when_configured(self):
        from unittest.mock import patch

        with patch("luzia_server.LUZIA_ACCESS_TOKEN", "test-secret"):
            client = TestClient(app)
            denied = client.post("/api/mode", json={"mode": "free"})
            allowed = client.post(
                "/api/mode",
                json={"mode": "free"},
                headers={"X-LuzIA-Token": "test-secret"},
            )
        self.assertEqual(denied.status_code, 401)
        self.assertEqual(allowed.status_code, 200)

    def test_chat_history_is_limited_to_twenty_messages(self):
        history = [ChatMessage(role="user", content=f"Mensagem {index}") for index in range(21)]
        with self.assertRaises(ValidationError):
            ChatRequest(message="Teste", history=history)



class Esp32ToolArgumentTests(unittest.IsolatedAsyncioTestCase):
    async def test_set_led_requires_all_rgb_channels(self):
        client = Esp32Client()
        with self.assertRaises(ValueError):
            await client.set_led({"r": 10, "g": 20})

    async def test_string_false_is_sent_as_false(self):
        client = Esp32Client()
        client._request = AsyncMock(return_value={"ok": True})
        await client.set_led({"r": 10, "g": 20, "b": 30, "on": "false"})
        params = client._request.await_args.args[2]
        self.assertEqual(params["on"], "false")

    async def test_led_values_are_clamped_before_http_request(self):
        client = Esp32Client()
        client._request = AsyncMock(return_value={"ok": True})
        await client.set_led({"r": 300, "g": -5, "b": 10, "brightness": 150})
        params = client._request.await_args.args[2]
        self.assertEqual((params["r"], params["g"], params["b"]), (255, 0, 10))
        self.assertEqual(params["brightness"], 100)

    async def test_beep_duration_is_clamped(self):
        client = Esp32Client()
        client._request = AsyncMock(return_value={"ok": True})
        await client.beep({"duration_ms": 9000})
        self.assertEqual(client._request.await_args.args[2]["duration_ms"], 2000)


if __name__ == "__main__":
    unittest.main()
