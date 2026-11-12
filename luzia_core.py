"""Small deterministic command parser used by LuzIA's free mode."""
from __future__ import annotations

import re
import unicodedata
from typing import Any


COLOR_MAP: dict[str, tuple[int, int, int]] = {
    "azul": (0, 80, 255),
    "vermelho": (255, 0, 0),
    "encarnado": (255, 0, 0),
    "verde": (0, 255, 40),
    "amarelo": (255, 190, 0),
    "branco": (255, 255, 255),
    "roxo": (150, 0, 255),
    "violeta": (150, 0, 255),
    "rosa": (255, 20, 120),
    "cor-de-rosa": (255, 20, 120),
    "laranja": (255, 75, 0),
    "ciano": (0, 220, 255),
    "turquesa": (0, 210, 180),
    "magenta": (255, 0, 180),
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", text).strip()


def parse_free_command(message: str) -> dict[str, Any] | None:
    """Return a tool call description, or None when this is not a known command."""
    text = normalize(message)

    if any(term in text for term in ("estado do led", "estado da luz", "status", "que cor esta", "qual e a cor", "como esta o led")):
        return {"tool": "get_led_status", "arguments": {}}

    if any(term in text for term in ("apita", "faz beep", "faz um beep", "toca", "buzzer", "faz barulho")):
        match = re.search(r"(\d{2,4})\s*(ms|milissegundos)?", text)
        duration = int(match.group(1)) if match else 250
        return {"tool": "beep", "arguments": {"duration_ms": max(50, min(duration, 2000))}}

    if any(term in text for term in ("apaga", "desliga", "desligar", "apagar", "desliga a luz", "led off", "luz off")) or re.search(r"\boff\b", text):
        return {"tool": "set_led", "arguments": {"r": 0, "g": 0, "b": 0, "brightness": 100, "on": False}}

    # Match longer names first (e.g. cor-de-rosa before rosa).
    for color_name in sorted(COLOR_MAP, key=len, reverse=True):
        if re.search(rf"\b{re.escape(color_name)}\b", text):
            r, g, b = COLOR_MAP[color_name]
            brightness_match = re.search(r"(?:a|com|para)\s*(\d{1,3})\s*%", text)
            brightness = max(1, min(int(brightness_match.group(1)), 100)) if brightness_match else 100
            return {
                "tool": "set_led",
                "arguments": {"r": r, "g": g, "b": b, "brightness": brightness, "on": True},
                "color_name": color_name,
            }

    hex_match = re.search(r"#?([0-9a-f]{6})\b", text)
    if hex_match:
        value = hex_match.group(1)
        r, g, b = (int(value[i:i + 2], 16) for i in (0, 2, 4))
        return {"tool": "set_led", "arguments": {"r": r, "g": g, "b": b, "brightness": 100, "on": True}}

    return None


def free_mode_help() -> str:
    return (
        "No modo gratuito ainda não tenho um modelo de linguagem completo; uso comandos locais "
        "e não envio mensagens para serviços externos. Experimenta: «acende azul», «fica vermelho», "
        "«acende rosa a 40%», «apaga o LED», «qual é o estado do LED?» ou «faz beep». "
        "Para conversa livre, escolhe Ollama (local) ou Claude (API)."
    )
