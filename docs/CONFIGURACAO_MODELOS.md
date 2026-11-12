# Configuração dos modelos

O valor sugerido no exemplo de configuração para a API Anthropic é:

```dotenv
ANTHROPIC_MODEL=claude-sonnet-5
```

Os nomes dos modelos disponíveis podem mudar. Consulta a página oficial [Model deprecations](https://docs.anthropic.com/en/docs/about-claude/model-deprecations) e a tua consola Anthropic para confirmar o identificador ativo antes de usar a API.

A integração Claude é opcional: o pacote `anthropic` só é importado quando o modo Claude é escolhido. Free e Ollama não precisam da chave API da Anthropic.
