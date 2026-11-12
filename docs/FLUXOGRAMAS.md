# Fluxogramas da LuzIA

Este documento representa os fluxos observados no código actual do projecto. Não define funcionalidades futuras.

## 1. Arquitectura geral

```mermaid
flowchart TD
    U[Utilizador] --> W[Interface Web<br/>static/index.html]
    W -->|POST /api/chat| API[Servidor Python<br/>FastAPI]
    API --> M{Modo activo}
    M -->|free| F[Parser determinístico<br/>luzia_core.py]
    M -->|ollama| O[Modelo Ollama<br/>tool calling]
    M -->|claude| C[API Anthropic<br/>tool use]
    F --> T[Execução de ferramentas]
    O --> T
    C --> T
    T -->|HTTP na rede local| E[ESP32<br/>servidor WebServer]
    E --> L[LED RGB<br/>GPIO 25, 26, 27]
    E --> B[Buzzer<br/>GPIO 14]
    E -->|JSON de resposta| T
    T --> API
    API -->|resposta JSON| W
    W -->|actualização periódica| S[GET /api/status]
    S --> API
    API -->|GET /status| E
```

## 2. Arranque do firmware ESP32

```mermaid
flowchart TD
    A([Início / reset]) --> B[Inicializar Serial e GPIO]
    B --> C[Configurar PWM e apagar LED]
    C --> D[Iniciar Wi-Fi em modo estação]
    D --> E[Activar auto-reconexão]
    E --> F[Registar rotas HTTP]
    F --> G[Iniciar servidor na porta 80]
    G --> H{{Ciclo loop}}
    H --> I[Processar pedidos HTTP]
    I --> J{Buzzer activo e prazo terminou?}
    J -->|Sim| K[Desligar buzzer]
    J -->|Não / ainda a tocar| L{Wi-Fi ligado?}
    K --> L
    L -->|Sim| M{Ligação já anunciada?}
    M -->|Não| N[Mostrar endereço IP]
    M -->|Sim| H
    N --> H
    L -->|Não| O{Passaram 10 segundos desde a última tentativa?}
    O -->|Não| H
    O -->|Sim| P[Solicitar WiFi.reconnect]
    P --> H
```

## 3. Recepção e processamento de uma mensagem

```mermaid
flowchart TD
    A([Utilizador envia mensagem]) --> B[Interface envia POST /api/chat]
    B --> C{Token configurado?}
    C -->|Sim| D{Token válido?}
    D -->|Não| E[Responder HTTP 401]
    D -->|Sim| F[Validar mensagem e histórico]
    C -->|Não| F
    F --> G{Validação correcta?}
    G -->|Não| H[Responder HTTP 422]
    G -->|Sim| I{Modo activo}
    I -->|free| J[Interpretar comando local]
    I -->|ollama| K[Enviar mensagens e ferramentas ao Ollama]
    I -->|claude| L[Enviar mensagens e ferramentas à Anthropic]
    J --> M[Obter resposta e acções]
    K --> M
    L --> M
    M --> N[Devolver reply, actions e mode]
    N --> O[Interface apresenta resposta]
    O --> P[Actualizar estado do dispositivo]
    P --> Q([Fim])
```

## 4. Modo Free — interpretação de comandos

```mermaid
flowchart TD
    A([Mensagem recebida]) --> B[Normalizar texto<br/>minúsculas e remoção de acentos]
    B --> C{Pedido de estado?}
    C -->|Sim| D[Ferramenta get_led_status]
    C -->|Não| E{Pedido de buzzer?}
    E -->|Sim| F[Extrair duração<br/>limitar a 50–2000 ms]
    E -->|Não| G{Pedido para apagar?}
    G -->|Sim| H[set_led com on=false]
    G -->|Não| I{Cor conhecida?}
    I -->|Sim| J[Converter cor em RGB<br/>e obter brilho opcional]
    I -->|Não| K{Código hexadecimal RGB?}
    K -->|Sim| L[Converter hexadecimal em RGB]
    K -->|Não| M[Apresentar ajuda<br/>sem executar acção]
    D --> N[Executar ferramenta]
    F --> N
    H --> N
    J --> N
    L --> N
    N --> O{ESP32 confirmou ok=true?}
    O -->|Sim| P[Formatar confirmação]
    O -->|Não| Q[Informar que a acção não foi confirmada]
    P --> R([Responder])
    Q --> R
    M --> R
```

## 5. Modos Ollama e Claude — ciclo de ferramentas

```mermaid
flowchart TD
    A([Mensagem e histórico]) --> B[Enviar pedido ao modelo<br/>com ferramentas disponíveis]
    B --> C{Resposta contém<br/>chamadas de ferramentas?}
    C -->|Não| D[Extrair texto da resposta]
    C -->|Sim| E[Adicionar resposta do modelo ao histórico]
    E --> F[Executar cada ferramenta solicitada]
    F --> G{Ferramenta reconhecida<br/>e execução confirmada?}
    G -->|Sim| H[Registar resultado da ferramenta]
    G -->|Não| I[Registar erro no resultado]
    H --> J[Enviar resultados ao modelo]
    I --> J
    J --> K{Ainda há rondas<br/>disponíveis?}
    K -->|Sim| B
    K -->|Não| L[Responder com limite de operações atingido]
    D --> M([Devolver resposta e acções])
    L --> M
```

Nota: o servidor limita o ciclo a `MAX_TOOL_ROUNDS + 1` iterações. O formato de chamada de ferramentas difere entre a API Ollama e a API Messages da Anthropic, mas ambas usam as ferramentas definidas pelo servidor.

## 6. Comunicação com o ESP32 e confirmação de acções

```mermaid
sequenceDiagram
    participant UI as Interface Web
    participant API as FastAPI
    participant TOOL as Esp32Client
    participant ESP as ESP32

    UI->>API: POST /api/chat + X-LuzIA-Token
    API->>API: Validar token se configurado
    alt Token inválido
        API-->>UI: HTTP 401
    else Acesso autorizado
        API->>TOOL: Executar ferramenta seleccionada
        TOOL->>ESP: POST /led ou POST /beep / GET /status
        ESP->>ESP: Aplicar PWM, temporizar buzzer ou ler estado
        ESP-->>TOOL: JSON com ok e dados
        alt Resposta válida com ok=true
            TOOL-->>API: Resultado confirmado
            API-->>UI: reply e actions
            UI->>API: GET /api/status
            API->>ESP: GET /status
            ESP-->>API: Estado actual do LED
            API-->>UI: connected=true e device
        else Erro HTTP, resposta inválida ou sem ok=true
            TOOL-->>API: Resultado de falha
            API-->>UI: Não foi possível confirmar a acção
        end
    end
```

## 7. Actualização periódica do estado na interface

```mermaid
flowchart TD
    A([Inicialização da interface]) --> B[GET /api/config]
    B --> C[Seleccionar modo indicado pelo servidor]
    C --> D[GET /api/status]
    D --> E{Servidor e ESP32 respondem?}
    E -->|Sim| F[Actualizar ligação e cor do LED]
    E -->|Não| G[Mostrar dispositivo sem resposta]
    F --> H[Aguardar ciclo de 5 segundos]
    G --> H
    H --> D
```

## 8. Autenticação opcional da interface

```mermaid
flowchart TD
    A([Abrir interface]) --> B[GET /api/config]
    B --> C{auth_required?}
    C -->|Não| D[Carregar estado e permitir utilização]
    C -->|Sim| E[Mostrar janela de acesso]
    E --> F[Utilizador introduz token]
    F --> G[GET /api/status com X-LuzIA-Token]
    G --> H{Token válido?}
    H -->|Não| I[Mostrar erro e pedir novo token]
    I --> F
    H -->|Sim| J[Guardar token em sessionStorage]
    J --> K[Permitir chat e controlo]
    D --> L([Interface pronta])
    K --> L
```

O token é opcional e protege os endpoints de controlo do servidor Python. Não autentica directamente o ESP32 nem cifra o tráfego HTTP.
