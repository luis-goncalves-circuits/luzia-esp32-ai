import unittest

from luzia_core import parse_free_command


class FreeModeParserTests(unittest.TestCase):
    def test_blue_led(self):
        result = parse_free_command("LuzIA, acende o LED azul")
        self.assertEqual(result["tool"], "set_led")
        self.assertEqual(result["arguments"]["b"], 255)
        self.assertTrue(result["arguments"]["on"])

    def test_accented_color_and_brightness(self):
        result = parse_free_command("Acende cor-de-rosa a 40%")
        self.assertEqual(result["color_name"], "cor-de-rosa")
        self.assertEqual(result["arguments"]["brightness"], 40)

    def test_off(self):
        result = parse_free_command("Apaga o LED")
        self.assertFalse(result["arguments"]["on"])

    def test_beep_is_clamped(self):
        result = parse_free_command("Faz beep durante 9000 ms")
        self.assertEqual(result["arguments"]["duration_ms"], 2000)

    def test_unknown_message_is_not_guessed(self):
        self.assertIsNone(parse_free_command("Conta-me uma história sobre Marte"))

    def test_hex_color(self):
        result = parse_free_command("acende #12a0ff")
        self.assertEqual((result["arguments"]["r"], result["arguments"]["g"], result["arguments"]["b"]), (18, 160, 255))


if __name__ == "__main__":
    unittest.main()
