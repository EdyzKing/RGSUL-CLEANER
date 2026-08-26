import pandas as pd


def analisar_qualidade(dados):

    print()
    print("==========================================")
    print("ANÁLISE DE QUALIDADE DOS DADOS")
    print("==========================================")

    # ======================================
    # INFORMAÇÕES GERAIS
    # ======================================

    print()
    print("INFORMAÇÕES GERAIS")
    print("------------------------------------------")

    print(f"Total de registros: {len(dados)}")
    print(f"Total de colunas: {len(dados.columns)}")

    # ======================================
    # CAMPOS VAZIOS
    # ======================================

    print()
    print("CAMPOS VAZIOS")
    print("------------------------------------------")

    vazios = dados.isna().sum()

    for coluna, quantidade in vazios.items():

        if quantidade > 0:

            percentual = (quantidade / len(dados)) * 100

            print(
                f"{coluna}: "
                f"{quantidade} vazios "
                f"({percentual:.2f}%)"
            )

    # ======================================
    # DUPLICIDADES
    # ======================================

    print()
    print("DUPLICIDADES")
    print("------------------------------------------")

    if "ID" in dados.columns:

        duplicados_id = dados["ID"].duplicated().sum()

        print(f"IDs duplicados: {duplicados_id}")

    if "CNPJ/CPF" in dados.columns:

        duplicados_documento = (
            dados["CNPJ/CPF"].duplicated().sum()
        )

        print(
            f"CPF/CNPJ duplicados: "
            f"{duplicados_documento}"
        )

    # ======================================
    # VALORES ÚNICOS
    # ======================================

    print()
    print("VALORES ÚNICOS")
    print("------------------------------------------")

    for coluna in dados.columns:

        quantidade = dados[coluna].nunique()

        print(
            f"{coluna}: "
            f"{quantidade} valores únicos"
        )

    # ======================================
    # ANÁLISE DE COLUNAS CATEGÓRICAS
    # ======================================

    print()
    print("==========================================")
    print("ANÁLISE DE VALORES CATEGÓRICOS")
    print("==========================================")

    colunas_categoricas = [
        "Ativo",
        "Prospecção",
        "Cidade",
        "UF",
        "País",
        "Filial",
        "Canal de venda",
        "Tipo pessoa",
        "Status prospecção",
        "Negativação Ativa"
    ]

    for coluna in colunas_categoricas:

        if coluna not in dados.columns:
            continue

        print()
        print(f"[ {coluna} ]")
        print("------------------------------------------")

        valores = dados[coluna].value_counts(
            dropna=False
        )

        for valor, quantidade in valores.items():

            if pd.isna(valor):
                valor = "[VAZIO]"

            print(
                f"{valor}: "
                f"{quantidade}"
            )