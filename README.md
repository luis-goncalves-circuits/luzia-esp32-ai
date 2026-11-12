# LuzIA — assistente de IA para ESP32 RGB

A LuzIA junta um ESP32, um LED RGB, um buzzer opcional, um chat web e um servidor Python. Escreve «LuzIA, acende o LED azul»; o modelo pode decidir chamar `set_led()`, o servidor envia o comando ao ESP32 e só depois de receber a confirmação do dispositivo a LuzIA diz que o LED foi ligado.

## Três modos de funcionamento

| Modo | O que é | Custo |
|---|---|---|
| **Free** | Reconhecimento local de comandos conhecidos, sem LLM | Sem custo de API |
| **Ollama** | Modelo generativo a correr no computador, com tool calling | Sem custo por token; usa recursos e eletricidade do PC |
| **Claude** | Modelo Claude através da API oficial com tool use | Pago conforme utilização e preços da Anthropic |

> O modo Free não é uma IA generativa: é uma alternativa gratuita e previsível para testar o circuito. Para conversa livre sem API paga, usa Ollama com um modelo compatível com ferramentas.

## Conteúdo do repositório

- `luzia_server.py`: API FastAPI, seleção de modos e execução das ferramentas.
- `luzia_core.py`: parser local de comandos para o modo Free.
- `static/index.html`: painel web de chat e estado do LED.
- `firmware/luzia_esp32/luzia_esp32.ino`: servidor HTTP do ESP32.
- `firmware/luzia_esp32/secrets.h.example`: exemplo de configuração Wi-Fi.
- `requirements.txt`: dependências base.
- `requirements-claude.txt`: SDK opcional da Claude.
- `tests/`: testes automáticos do parser Free.

## Material necessário

1. ESP32 DevKit (ESP32-WROOM-32 ou equivalente).
2. LED RGB de 4 pinos, preferencialmente **cátodo comum**.
3. Três resistências de 220–330 Ω, uma por canal R/G/B.
4. Buzzer **ativo** de baixa tensão (opcional; confirma os requisitos elétricos do componente).
5. Breadboard, cabos jumper e computador Windows/macOS/Linux.

**Atenção:** o firmware fornecido é para LED RGB de 4 pinos, não para WS2812B/NeoPixel.

## Ligações sugeridas

| Componente | ESP32 | Nota |
|---|---:|---|
| RGB — R | GPIO 25 | Em série com resistência 220–330 Ω |
| RGB — G | GPIO 26 | Em série com resistência 220–330 Ω |
| RGB — B | GPIO 27 | Em série com resistência 220–330 Ω |
| RGB — terminal comum | GND | Para cátodo comum |
| Buzzer ativo (+) | GPIO 14 | Opcional |
| Buzzer ativo (−) | GND | — |

Não ligues LEDs sem resistências. Confirma o pinout do teu RGB, porque a ordem física dos pinos varia. Para LED de **ânodo comum**, muda `COMMON_ANODE` para `true` no firmware e liga o terminal comum a 3V3. Não alimentes cargas acima dos limites dos GPIO.

## 1. Preparar e gravar o ESP32

1. Instala o Arduino IDE e o suporte **esp32 by Espressif Systems** (core Arduino-ESP32 3.x).
2. Abre `firmware/luzia_esp32/`.
3. Copia `secrets.h.example` para `secrets.h` na mesma pasta.
4. Preenche `WIFI_SSID` e `WIFI_PASSWORD` com os dados da rede Wi-Fi de 2,4 GHz.
5. Liga o ESP32 por USB, seleciona a placa e a porta série e carrega `luzia_esp32.ino`.
6. Abre o Monitor Série a 115200 baud e anota o IP apresentado.

Testa no navegador, substituindo o IP:

- `http://192.168.1.42/status` — deve devolver JSON com `ok:true`.
- Para testar o LED, envia um POST para `/led?r=0&g=80&b=255&brightness=100&on=true`.

Exemplo com curl:

```bash
curl -X POST "http://192.168.1.42/led?r=0&g=80&b=255&brightness=100&on=true"
```

## 2. Instalar o servidor

É necessário Python 3.10 ou superior.

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Abre [http://127.0.0.1:8000](http://127.0.0.1:8000).

## 3. Configurar o endereço do ESP32

Edita o ficheiro local `.env` e altera `ESP32_URL` para o IP indicado no Monitor Série:

```dotenv
ESP32_URL=http://192.168.1.42
AI_MODE=free
```

Guarda e reinicia o servidor. O computador e o ESP32 têm de comunicar na mesma rede local. Recomenda-se reservar o IP do ESP32 no router.

## 4. Escolher o cérebro da LuzIA

O seletor no painel altera o modo em tempo de execução. A seleção mantém-se até reiniciares o servidor. Para escolher o modo inicial, altera `AI_MODE` no `.env`.

### A. Free — sem chave ou serviço externo

Deixa `AI_MODE=free`. Comandos reconhecidos incluem:

- `Acende o LED azul`
- `Acende o LED verde a 40%`
- `Põe a luz cor-de-rosa`
- `Apaga o LED`
- `Qual é o estado do LED?`
- `Faz beep durante 300 ms`
- `Acende #12a0ff`

O parser não interpreta qualquer frase. Se não reconhecer um pedido, explica os comandos suportados em vez de inventar uma resposta.

### B. Ollama — IA generativa local

1. Instala [Ollama](https://ollama.com/) e inicia o serviço.
2. Descarrega um modelo com suporte para tool calling. O exemplo usado é `qwen3`:

```bash
ollama pull qwen3
```

3. No `.env`, define:

```dotenv
AI_MODE=ollama
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3
```

4. Reinicia o servidor e seleciona **Ollama — IA local** no painel.

O desempenho depende da RAM, CPU/GPU e tamanho do modelo. O primeiro pedido pode demorar enquanto o modelo carrega. Podes usar outro modelo instalado que suporte chamadas de ferramentas.

### C. Claude API — IA na cloud

1. Cria uma chave na [consola da Anthropic](https://console.anthropic.com/).
2. Instala o SDK opcional no mesmo ambiente virtual:

```bash
pip install -r requirements-claude.txt
```

3. No `.env`, configura:

```dotenv
AI_MODE=claude
ANTHROPIC_API_KEY=COLOCA_A_TUA_CHAVE_AQUI
ANTHROPIC_MODEL=claude-sonnet-5
```

4. Reinicia o servidor e seleciona Claude no painel.

O SDK Anthropic não é importado nem necessário nos modos Free e Ollama; só é carregado quando o modo Claude recebe uma mensagem. Confirma o identificador de modelo e preços atuais na documentação da Anthropic antes de utilizar a API.

## Custos e privacidade

- **Free:** sem custos de API e sem envio das mensagens para serviços externos; só executa os padrões de comandos implementados.
- **Ollama local:** sem faturação por token para modelos executados localmente. O custo indireto é eletricidade e recursos do computador. Confirma que estás a usar um modelo local e não um serviço cloud.
- **Claude:** faturação conforme o modelo e os tokens de entrada/saída. Define limites na consola e consulta os preços atuais antes de usar.

A chave API fica no ficheiro local `.env`: nunca a coloques no firmware, HTML ou GitHub. O `.gitignore` exclui `.env`, ficheiros de ambiente e `secrets.h`.

## Testes

Com o ambiente virtual ativo:

```bash
python -m unittest discover -s tests -v
python -m compileall -q luzia_server.py luzia_core.py run.py
```

Os testes cobrem o parser do modo gratuito. Para validar o circuito real, liga o ESP32 à mesma rede e executa os testes HTTP indicados acima.

## Diagnóstico

| Problema | Verificações |
|---|---|
| ESP32 offline | IP em `ESP32_URL`, Wi-Fi 2,4 GHz, firewall e Monitor Série |
| LED não acende ou cor trocada | Pinout, resistências, cátodo/ânodo comum e `COMMON_ANODE` |
| Buzzer não toca | Tipo ativo, polaridade, tensão e GPIO 14 |
| Ollama não responde | Serviço ativo, `ollama list`, modelo instalado e URL `11434` |
| Claude diz que falta SDK | Instala `requirements-claude.txt` no ambiente virtual correto |
| Claude rejeita o modelo | Confirma o ID disponível na tua conta Anthropic |
| Porta 8000 ocupada | Altera `PORT` no `.env` |

## Segurança

Este é um projeto doméstico de laboratório. O servidor não tem autenticação, o firmware aceita pedidos na rede local e o tráfego HTTP não é cifrado. Mantém `HOST=127.0.0.1` por defeito; não abras portas no router nem exponhas diretamente o servidor ou ESP32 à Internet. Para acesso a partir de outro dispositivo da rede, configura `HOST=0.0.0.0` conscientemente e usa apenas uma rede privada de confiança.

## Licença

MIT — ver [LICENSE](LICENSE).

## Referências técnicas

- [Ollama — Tool calling](https://docs.ollama.com/capabilities/tool-calling)
- [Ollama — API /api/chat](https://docs.ollama.com/api/chat)
- [Anthropic — Python SDK](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/python)
- [Anthropic — Tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Anthropic — Model deprecations](https://docs.anthropic.com/en/docs/about-claude/model-deprecations)
- [Arduino-ESP32 — documentação](https://docs.espressif.com/projects/arduino-esp32/en/latest/)
