from pathlib import Path
import io
import re
import pandas as pd
import unicodedata
import streamlit as st

from data_cleaning import (
    padronizar_bairros,
    separar_registros_sem_bairro,
    separar_nomes_iniciados_por_numero,
    identificar_nomes_numericos,
    identificar_nomes_muito_curtos,
    identificar_nomes_de_teste,
)

# =============================
# VALIDAÇÃO DE BAIRROS
# =============================
BAIRROS_PATH = Path("dados") / "bairros_validos.csv"

def normalizar_para_comparacao(valor):
    if pd.isna(valor) or valor is None:
        return ""
    # Converte para string e limpa espaços nas pontas
    texto = str(valor).strip()
    # Remove acentos
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    # Converte tudo para MAIÚSCULAS
    texto = texto.upper()
    # Substitui múltiplos espaços por um único espaço
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

@st.cache_data
def carregar_bairros_validos():
    if not BAIRROS_PATH.exists():
        return pd.DataFrame(columns=["Cidade", "Bairro"])
    
    # Tenta ler com utf-8-sig e fallback para latin1
    try:
        base = pd.read_csv(BAIRROS_PATH, sep=";", dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except UnicodeDecodeError:
        base = pd.read_csv(BAIRROS_PATH, sep=";", dtype=str, keep_default_na=False, encoding="latin1")

    base.columns = [str(c).strip() for c in base.columns]
    
    if "Cidade" not in base.columns or "Bairro" not in base.columns:
        return pd.DataFrame(columns=["Cidade", "Bairro"])
    
    base["Cidade_cmp"] = base["Cidade"].apply(normalizar_para_comparacao)
    base["Bairro_cmp"] = base["Bairro"].apply(normalizar_para_comparacao)
    return base

def validar_bairros_por_cidade(dados):
    if "Cidade" not in dados.columns or "Bairro" not in dados.columns:
        return dados.copy(), pd.DataFrame(columns=dados.columns)

    validos = carregar_bairros_validos()
    if validos.empty:
        return dados.copy(), pd.DataFrame(columns=dados.columns)

    # Conjunto com as chaves (Cidade, Bairro) totalmente em maiúsculas e sem acento
    chaves_validas = set(zip(validos["Cidade_cmp"], validos["Bairro_cmp"]))

    cidade_cmp = dados["Cidade"].apply(normalizar_para_comparacao)
    bairro_cmp = dados["Bairro"].apply(normalizar_para_comparacao)

    # Bairro vazio continua sendo tratado pela regra de "sem bairro".
    preenchido = bairro_cmp != ""
    chave = list(zip(cidade_cmp, bairro_cmp))
    
    invalido = preenchido & pd.Series(
        [k not in chaves_validas for k in chave], index=dados.index
    )

    registros_invalidos = dados.loc[invalido].copy()
    registros_validos = dados.loc[~invalido].copy()
    return registros_validos, registros_invalidos

# Configuração da página Streamlit
st.set_page_config(
    page_title="Limpeza de CSV",
    page_icon="🧹",
    layout="wide"
)

st.title("🧹 Limpeza de Base CSV")
st.caption("Importe sua base, escolha as regras de limpeza e baixe o arquivo tratado.")

st.divider()

arquivo = st.file_uploader(
    "Selecione o arquivo CSV",
    type=["csv"],
    help="O sistema tenta automaticamente UTF-8 e, se necessário, Latin-1."
)

if arquivo is not None:
    try:
        conteudo = arquivo.getvalue()

        try:
            dados_original = pd.read_csv(
                io.BytesIO(conteudo),
                sep=";",
                encoding="utf-8-sig",
                dtype=str,
                keep_default_na=False
            )
        except UnicodeDecodeError:
            dados_original = pd.read_csv(
                io.BytesIO(conteudo),
                sep=";",
                encoding="latin1",
                dtype=str,
                keep_default_na=False
            )

        dados_original.columns = dados_original.columns.str.strip()

        st.success("Arquivo carregado com sucesso!")

        with st.expander("📋 Colunas encontradas no arquivo"):
            st.write(", ".join(dados_original.columns.tolist()))

        col1, col2, col3 = st.columns(3)
        col1.metric("Registros", len(dados_original))
        col2.metric("Colunas", len(dados_original.columns))
        col3.metric("Arquivo", arquivo.name)

        st.subheader("Regras de limpeza")
        st.write("Marque as operações que deseja aplicar:")

        c1, c2 = st.columns(2)

        with c1:
            remover_sem_bairro = st.checkbox(
                "Remover registros sem bairro",
                value=True
            )
            remover_inicio_numero = st.checkbox(
                "Remover nomes iniciados por número",
                value=True
            )
            padronizar = st.checkbox(
                "Padronizar bairros",
                value=True
            )
            validar_bairros = st.checkbox(
                "Validar bairros contra a base oficial (Cidade + Bairro)",
                value=False
            )

        with c2:
            remover_numericos = st.checkbox(
                "Remover nomes somente numéricos",
                value=False
            )
            remover_curtos = st.checkbox(
                "Remover nomes muito curtos (até 2 caracteres)",
                value=False
            )
            remover_teste = st.checkbox(
                "Remover nomes contendo TESTE/TEST",
                value=False
            )

        st.info(
            "As opções da coluna à direita e a validação oficial são desativadas por padrão "
            "porque podem remover registros que talvez precisem apenas de revisão."
        )

        st.divider()

        if st.button("🧹 PROCESSAR ARQUIVO", type="primary", use_container_width=True):

            erros_colunas = []
            precisa_razao = (remover_inicio_numero or remover_numericos or remover_curtos or remover_teste)
            precisa_bairro = remover_sem_bairro or padronizar or validar_bairros
            precisa_cidade = validar_bairros

            if precisa_razao and "Razão social" not in dados_original.columns:
                erros_colunas.append("• 'Razão social' é necessária para as regras de limpeza de nomes.")
            if precisa_bairro and "Bairro" not in dados_original.columns:
                erros_colunas.append("• 'Bairro' é necessária para as regras de limpeza/padronização de bairros.")
            if precisa_cidade and "Cidade" not in dados_original.columns:
                erros_colunas.append("• 'Cidade' é necessária para a validação de bairros oficiais.")

            if erros_colunas:
                st.error("O arquivo não possui todas as colunas necessárias para as opções selecionadas.")
                for erro in erros_colunas:
                    st.warning(erro)
                st.info("Desmarque as opções relacionadas às colunas ausentes e processe novamente.")
                st.stop()

            dados = dados_original.copy()

            # Relatórios
            removidos_sem_bairro = pd.DataFrame(columns=dados.columns)
            removidos_inicio_numero = pd.DataFrame(columns=dados.columns)
            removidos_numericos = pd.DataFrame(columns=dados.columns)
            removidos_curtos = pd.DataFrame(columns=dados.columns)
            removidos_teste = pd.DataFrame(columns=dados.columns)
            removidos_bairros_invalidos = pd.DataFrame(columns=dados.columns)

            # 1 - Remover sem bairro
            if remover_sem_bairro:
                dados, removidos_sem_bairro = separar_registros_sem_bairro(dados)

            # 2 - Validar bairros oficiais (Cidade + Bairro em caixa alta)
            if validar_bairros:
                dados, removidos_bairros_invalidos = validar_bairros_por_cidade(dados)

            # 3 - Remover nomes iniciados por número
            if remover_inicio_numero:
                dados, removidos_inicio_numero = separar_nomes_iniciados_por_numero(dados)

            # 4 - Remover somente numéricos
            if remover_numericos:
                encontrados = identificar_nomes_numericos(dados)
                removidos_numericos = encontrados.copy()
                dados = dados.drop(index=encontrados.index)

            # 5 - Remover muito curtos
            if remover_curtos:
                encontrados = identificar_nomes_muito_curtos(dados)
                removidos_curtos = encontrados.copy()
                dados = dados.drop(index=encontrados.index)

            # 6 - Remover teste/test
            if remover_teste:
                encontrados = identificar_nomes_de_teste(dados)
                removidos_teste = encontrados.copy()
                dados = dados.drop(index=encontrados.index)

            # 7 - Padronizar bairros
            if padronizar:
                dados = padronizar_bairros(dados)

            total_removidos = (
                len(removidos_sem_bairro)
                + len(removidos_bairros_invalidos)
                + len(removidos_inicio_numero)
                + len(removidos_numericos)
                + len(removidos_curtos)
                + len(removidos_teste)
            )

            st.session_state["dados_limpos"] = dados
            st.session_state["relatorios"] = {
                "sem_bairro": removidos_sem_bairro,
                "bairros_invalidos": removidos_bairros_invalidos,
                "inicio_numero": removidos_inicio_numero,
                "numericos": removidos_numericos,
                "curtos": removidos_curtos,
                "teste": removidos_teste,
            }
            st.session_state["estatisticas"] = {
                "originais": len(dados_original),
                "sem_bairro": len(removidos_sem_bairro),
                "bairros_invalidos": len(removidos_bairros_invalidos),
                "inicio_numero": len(removidos_inicio_numero),
                "numericos": len(removidos_numericos),
                "curtos": len(removidos_curtos),
                "teste": len(removidos_teste),
                "removidos": total_removidos,
                "finais": len(dados),
            }

            st.success("Processamento concluído!")

    except Exception as erro:
        st.error(f"Não foi possível processar o arquivo: {erro}")

if "dados_limpos" in st.session_state:

    dados_limpos = st.session_state["dados_limpos"]
    stats = st.session_state["estatisticas"]
    relatorios = st.session_state["relatorios"]

    st.subheader("Resultado")

    m1, m2, m3 = st.columns(3)
    m1.metric("Registros originais", stats["originais"])
    m2.metric("Registros removidos", stats["removidos"])
    m3.metric("Registros finais", stats["finais"])

    st.write("### Detalhamento")

    detalhes = pd.DataFrame({
        "Regra": [
            "Sem bairro",
            "Bairro não encontrado na base oficial",
            "Nome iniciado por número",
            "Nome somente numérico",
            "Nome muito curto",
            "Nome contendo TESTE/TEST",
        ],
        "Registros encontrados/removidos": [
            stats["sem_bairro"],
            stats["bairros_invalidos"],
            stats["inicio_numero"],
            stats["numericos"],
            stats["curtos"],
            stats["teste"],
        ],
    })

    st.dataframe(detalhes, use_container_width=True, hide_index=True)

    st.divider()
    st.write("### ⬇️ Arquivos separados")

    arquivos_relatorios = [
        ("sem_bairro", "📍 BAIXAR REGISTROS SEM BAIRRO", "registros_sem_bairro.csv"),
        ("bairros_invalidos", "🏘️ BAIXAR BAIRROS NÃO ENCONTRADOS", "registros_bairros_invalidos.csv"),
        ("inicio_numero", "🔢 BAIXAR NOMES INICIADOS POR NÚMERO", "registros_nomes_com_numero.csv"),
        ("numericos", "🔢 BAIXAR NOMES SOMENTE NUMÉRICOS", "registros_nomes_numericos.csv"),
        ("curtos", "✏️ BAIXAR NOMES MUITO CURTOS", "registros_nomes_muito_curtos.csv"),
        ("teste", "🧪 BAIXAR NOMES COM TESTE/TEST", "registros_nomes_teste.csv"),
    ]

    for chave, rotulo, nome_arquivo in arquivos_relatorios:
        df = relatorios[chave]
        if len(df) > 0:
            csv_relatorio = df.to_csv(sep=";", index=False, encoding="utf-8-sig")
            st.download_button(
                label=f"{rotulo} ({len(df)} registros)",
                data=csv_relatorio,
                file_name=nome_arquivo,
                mime="text/csv",
                use_container_width=True,
                key=f"download_{chave}"
            )

    st.write("### Prévia da base limpa")
    st.dataframe(
        dados_limpos.head(50),
        use_container_width=True,
        hide_index=True
    )

    csv_limpo = dados_limpos.to_csv(
        sep=";",
        index=False,
        encoding="utf-8-sig"
    )

    st.download_button(
        label="⬇️ BAIXAR CSV LIMPO",
        data=csv_limpo,
        file_name="arquivo_limpo.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True
    )