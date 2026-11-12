# Arquitetura da LuzIA

```text
Browser (chat web)
       |
       | X-LuzIA-Token (se configurado)
       | POST /api/chat
       v
Python / FastAPI (máquina local)
       |
       +-- free: parser local de comandos conhecidos
       |
       +-- ollama: modelo local + tool calling
       |
       +-- claude: Anthropic Messages API + tool use
       |
       |  set_led / get_led_status / beep
       v
HTTP na rede Wi-Fi local
       |
       v
ESP32 (servidor HTTP)
       |
       +-- PWM RGB: GPIO 25, 26, 27
       +-- controlo do buzzer via NPN: GPIO 14
```

## Princípio de fiabilidade

O modelo não controla diretamente GPIO nem recebe credenciais Wi-Fi. O servidor valida os argumentos e faz pedidos HTTP ao ESP32. Uma ação só é apresentada como concluída quando o ESP32 devolve JSON com `ok: true`. Se o dispositivo não responder, a interface mostra uma falha de ligação.

## Modos

- `free`: parser determinístico, sem API e sem modelo generativo. Reconhece um conjunto declarado de comandos em português.
- `ollama`: envia conversa e ferramentas para `POST /api/chat` do Ollama local. O modelo escolhido tem de suportar tool calling.
- `claude`: usa o SDK oficial `anthropic` e a API Messages com ferramentas definidas pelo projeto. O pacote é importado apenas quando este modo é executado.

## Limites deliberados

- O modo Free não tenta responder a perguntas gerais como se fosse um LLM.
- O servidor aceita um token opcional `LUZIA_ACCESS_TOKEN` nos endpoints de controlo. Mantém `HOST=127.0.0.1` por defeito; se o partilhares na rede, configura um token longo e aleatório.
- O firmware exemplo é para LED RGB de 4 pinos (não WS2812/NeoPixel) e buzzer ativo.
- O token protege apenas a API Python. A comunicação entre servidor e ESP32 continua sem TLS nem autenticação; usa apenas numa rede doméstica de confiança.
