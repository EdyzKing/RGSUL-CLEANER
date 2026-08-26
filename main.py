import os
import pandas as pd

from data_cleaning import (
    identificar_nomes_suspeitos,
    padronizar_bairros
)


# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

arquivo_entrada = "entrada/seu_arquivo.csv"
arquivo_saida = "saida/seu_arquivo_limpo.csv"

arquivo_sem_bairro = "saida/registros_sem_bairro.csv"
arquivo_nomes_numero = "saida/registros_nomes_com_numero.csv"

os.makedirs("saida", exist_ok=True)


# ==========================================================
# CARREGAMENTO
# ==========================================================

print("Carregando arquivo...")

try:
    dados = pd.read_csv(
        arquivo_entrada,
        sep=";",
        encoding="utf-8-sig",
        dtype=str,
        keep_default_na=False
    )

except UnicodeDecodeError:
    dados = pd.read_csv(
        arquivo_entrada,
        sep=";",
        encoding="latin1",
        dtype=str,
        keep_default_na=False
    )

print("Arquivo carregado com sucesso!")
print(f"Registros encontrados: {len(dados)}")
print(f"Colunas encontradas: {len(dados.columns)}")


# ==========================================================
# LIMPEZA INICIAL
# ==========================================================

# Remove espaços extras dos nomes das colunas
dados.columns = dados.columns.str.strip()

# Garante que Razão social e Bairro existam
if "Razão social" not in dados.columns:
    raise Exception("A coluna 'Razão social' não foi encontrada.")

if "Bairro" not in dados.columns:
    raise Exception("A coluna 'Bairro' não foi encontrada.")


# ==========================================================
# 1. SEPARAR REGISTROS SEM BAIRRO
# ==========================================================

print()
print("Separando registros sem bairro...")

sem_bairro = (
    dados["Bairro"]
    .astype(str)
    .str.strip()
    .eq("")
)

registros_sem_bairro = dados[sem_bairro].copy()

print(f"Registros sem bairro: {len(registros_sem_bairro)}")

if len(registros_sem_bairro) > 0:
    registros_sem_bairro.to_csv(
        arquivo_sem_bairro,
        sep=";",
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Arquivo gerado: {arquivo_sem_bairro}")

# Remove da lista principal
dados = dados[~sem_bairro].copy()


# ==========================================================
# 2. IDENTIFICAR RAZÃO SOCIAL COM NÚMERO NA FRENTE
# ==========================================================

print()
print("Identificando nomes com números na frente...")

# Exemplos que serão encontrados:
#
# 1 1
# 1 ANDREIA
# 2 CARLOS
# 2 2
# 123 EMPRESA
# 3N INDUSTRIA
#
# A regra procura número no início do campo,
# seguido por espaço ou texto.

razao_social = (
    dados["Razão social"]
    .astype(str)
    .str.strip()
)

nomes_com_numero = razao_social.str.match(
    r"^\d+(?:\s+|$)",
    na=False
)

registros_nomes_numero = dados[nomes_com_numero].copy()

print(
    f"Registros com número no início da Razão social: "
    f"{len(registros_nomes_numero)}"
)

if len(registros_nomes_numero) > 0:

    registros_nomes_numero.to_csv(
        arquivo_nomes_numero,
        sep=";",
        index=False,
        encoding="utf-8-sig"
    )

    print(
        f"Arquivo gerado: {arquivo_nomes_numero}"
    )


# ==========================================================
# 3. REMOVER DA LISTA PRINCIPAL
# ==========================================================

dados = dados[~nomes_com_numero].copy()

print(
    f"Registros restantes após remover nomes com número: "
    f"{len(dados)}"
)


# ==========================================================
# 4. PADRONIZAR BAIRROS
# ==========================================================

print()
print("Padronizando bairros...")

dados = padronizar_bairros(dados)


# ==========================================================
# 5. IDENTIFICAR OUTROS NOMES SUSPEITOS
# ==========================================================

print()
print("Identificando nomes suspeitos...")

registros_suspeitos = identificar_nomes_suspeitos(dados)

if registros_suspeitos is None:
    registros_suspeitos = pd.DataFrame(columns=dados.columns)

arquivo_suspeitos = "saida/registros_suspeitos.csv"

if len(registros_suspeitos) > 0:

    registros_suspeitos.to_csv(
        arquivo_suspeitos,
        sep=";",
        index=False,
        encoding="utf-8-sig"
    )

    print(
        f"Registros suspeitos adicionais: "
        f"{len(registros_suspeitos)}"
    )

    print(f"Arquivo: {arquivo_suspeitos}")


# ==========================================================
# 6. SALVAR ARQUIVO FINAL
# ==========================================================

dados.to_csv(
    arquivo_saida,
    sep=";",
    index=False,
    encoding="utf-8-sig"
)


# ==========================================================
# RESUMO
# ==========================================================

print()
print("=" * 50)
print("PROCESSAMENTO CONCLUÍDO")
print("=" * 50)

print(f"Registros originais: {len(dados) + len(registros_nomes_numero)}")
print(f"Registros removidos - sem bairro: {len(registros_sem_bairro)}")
print(f"Registros removidos - número no nome: {len(registros_nomes_numero)}")
print(f"Registros finais: {len(dados)}")

print()
print(f"Arquivo principal: {arquivo_saida}")
print(f"Sem bairro: {arquivo_sem_bairro}")
print(f"Nomes com número: {arquivo_nomes_numero}")

print("=" * 50)