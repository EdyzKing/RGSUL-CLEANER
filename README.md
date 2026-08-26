# Limpeza de Base CSV

Aplicação web em Python + Streamlit para importar uma base CSV, selecionar regras de limpeza e baixar o resultado.

## Como executar

1. Instale o Python.
2. Abra o terminal dentro desta pasta.
3. Execute:

```bash
pip install -r requirements.txt
```

4. Depois execute:

```bash
streamlit run app.py
```

5. O navegador abrirá a aplicação.

## Estrutura

- `app.py` - interface web e fluxo de processamento.
- `data_cleaning.py` - regras de limpeza.
- `requirements.txt` - dependências.

## Colunas obrigatórias

O CSV precisa possuir:

- `Razão social`
- `Bairro`

O sistema trabalha com `;` como separador e tenta UTF-8, depois Latin-1.
