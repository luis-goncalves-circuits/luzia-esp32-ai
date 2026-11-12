# Esquema eléctrico e lista de componentes

![Esquema eléctrico de referência](ESQUEMA_ELETRICO.svg)

O diagrama corresponde ao firmware actual e à configuração documentada no projecto: LED RGB de quatro pinos, cátodo comum, e buzzer activo opcional.

## Ligações

| Sinal | ESP32 | Ligação |
|---|---:|---|
| Canal vermelho | GPIO 25 | GPIO → resistência 220–330 Ω → terminal R do LED |
| Canal verde | GPIO 26 | GPIO → resistência 220–330 Ω → terminal G do LED |
| Canal azul | GPIO 27 | GPIO → resistência 220–330 Ω → terminal B do LED |
| Comum do LED | GND | Cátodo comum → GND |
| Buzzer positivo | GPIO 14 | Apenas para buzzer activo compatível com o nível lógico e corrente do GPIO |
| Buzzer negativo | GND | Massa comum |

## Lista de material (BOM)

| Quantidade | Componente | Especificação |
|---:|---|---|
| 1 | Placa ESP32 DevKit | ESP32-WROOM-32 ou equivalente |
| 1 | LED RGB | 4 pinos, cátodo comum |
| 3 | Resistência | 220–330 Ω, uma por canal |
| 1 | Buzzer | Activo, baixa tensão, opcional |
| 1 | Breadboard | Compatível com a placa |
| Vários | Cabos jumper | Macho-macho conforme a montagem |
| 1 | Cabo USB | Dados e alimentação da placa |

## Notas de segurança eléctrica

- O esquema é para LED RGB discreto de quatro pinos; não é compatível com WS2812B/NeoPixel.
- Não ligar qualquer canal do LED directamente ao GPIO: cada canal precisa da sua resistência limitadora.
- Confirmar a disposição dos terminais no datasheet do LED. A ordem física dos pinos varia entre fabricantes.
- Para LED de ânodo comum, a ligação e a lógica PWM são diferentes; o firmware tem de ser configurado com `COMMON_ANODE = true` e o terminal comum ligado a 3V3.
- Não alimentar um buzzer que exceda a corrente admissível do GPIO directamente a partir do pino. Usar um transistor de comutação e alimentação adequada quando necessário.
- O esquema é uma referência de ligação, não substitui a verificação dos datasheets dos componentes concretos antes de energizar o circuito.

## Relação com o firmware

Os GPIO e o tipo de LED indicados são os valores definidos em `firmware/luzia_esp32/luzia_esp32.ino`. Se alterares os pinos ou o tipo de LED, actualiza também este esquema.
