import unittest

from luzia_core import parse_free_command


class FreeModeBoundaryTests(unittest.TestCase):
    def test_color_matching_is_case_and_accent_insensitive(self):
        result = parse_free_command("ACENDE O LED VERMÉLHO")
        self.assertEqual(result["color_name"], "vermelho")
        self.assertEqual(result["arguments"]["r"], 255)

    def test_brightness_is_limited_to_hundred_percent(self):
        result = parse_free_command("Acende azul a 180%")
        self.assertEqual(result["arguments"]["brightness"], 100)

    def test_brightness_never_becomes_zero(self):
        result = parse_free_command("Acende azul a 0%")
        self.assertEqual(result["arguments"]["brightness"], 1)

    def test_off_command_takes_precedence_over_color(self):
        result = parse_free_command("Apaga o LED azul")
        self.assertFalse(result["arguments"]["on"])

    def test_status_request_is_recognised(self):
        result = parse_free_command("Qual é o estado do LED?")
        self.assertEqual(result["tool"], "get_led_status")

    def test_beep_default_duration(self):
        result = parse_free_command("Faz beep")
        self.assertEqual(result["arguments"]["duration_ms"], 250)

    def test_beep_duration_lower_bound(self):
        result = parse_free_command("Faz beep durante 10 ms")
        self.assertEqual(result["arguments"]["duration_ms"], 50)

    def test_color_hexadecimal_without_hash(self):
        result = parse_free_command("Acende 12a0ff")
        self.assertEqual(
            (result["arguments"]["r"], result["arguments"]["g"], result["arguments"]["b"]),
            (18, 160, 255),
        )


if __name__ == "__main__":
    unittest.main()
