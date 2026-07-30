import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date

st.set_page_config(page_title="Gestão de Treinamentos", page_icon="📘", layout="wide")

DATA_FILE = Path(__file__).parent / "treinamentos.csv"
COLUNAS = ["Setor", "Treinamento", "Quantidade", "Data"]


def carregar_dados():
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE, parse_dates=["Data"])
        return df
    return pd.DataFrame(columns=COLUNAS)


def salvar_dados(df):
    df.to_csv(DATA_FILE, index=False)


if "df" not in st.session_state:
    st.session_state.df = carregar_dados()

df = st.session_state.df

st.title("📘 Gestão de Treinamentos")
st.caption("Registre os treinamentos realizados por setor.")

# ---------- Formulário de cadastro ----------
with st.form("novo_treinamento", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns([1.3, 1.7, 0.8, 1])

    setores_existentes = sorted(df["Setor"].unique().tolist()) if not df.empty else []
    with col1:
        setor = st.selectbox(
            "Setor",
            options=["+ Novo setor"] + setores_existentes,
            index=0,
        )
        if setor == "+ Novo setor":
            setor = st.text_input("Nome do novo setor", key="novo_setor")

    with col2:
        treinamento = st.text_input("Treinamento", placeholder="Ex: NR-35")
    with col3:
        quantidade = st.number_input("Quantidade", min_value=1, value=1, step=1)
    with col4:
        data_treinamento = st.date_input("Data", value=date.today())

    enviado = st.form_submit_button("➕ Adicionar", use_container_width=True)

    if enviado:
        if not setor or not treinamento:
            st.warning("Preencha o setor e o nome do treinamento.")
        else:
            nova_linha = pd.DataFrame(
                [[setor, treinamento, int(quantidade), pd.to_datetime(data_treinamento)]],
                columns=COLUNAS,
            )
            st.session_state.df = pd.concat([df, nova_linha], ignore_index=True)
            salvar_dados(st.session_state.df)
            st.rerun()

df = st.session_state.df

if df.empty:
    st.info("Nenhum treinamento registrado ainda. Use o formulário acima para começar.")
    st.stop()

st.divider()

# ---------- Métricas gerais ----------
resumo_setor = df.groupby("Setor")["Quantidade"].sum().sort_values(ascending=False)
total_geral = int(df["Quantidade"].sum())
setor_destaque = resumo_setor.index[0] if not resumo_setor.empty else "—"

m1, m2, m3 = st.columns(3)
m1.metric("Total de treinamentos", total_geral)
m2.metric("Setor com mais treinamentos", setor_destaque)
m3.metric("Setores cadastrados", df["Setor"].nunique())

# ---------- Gráfico por setor ----------
st.subheader("Treinamentos por setor")
st.bar_chart(resumo_setor)

st.divider()

# ---------- Filtro e tabela ----------
st.subheader("Registros")

filtro = st.selectbox("Filtrar por setor", options=["Todos"] + sorted(df["Setor"].unique().tolist()))

df_visivel = df if filtro == "Todos" else df[df["Setor"] == filtro]
df_visivel = df_visivel.sort_values("Data", ascending=False).reset_index(drop=True)
df_visivel["Data"] = df_visivel["Data"].dt.strftime("%d/%m/%Y")
df_visivel.insert(0, "Excluir", False)

editado = st.data_editor(
    df_visivel,
    use_container_width=True,
    hide_index=True,
    disabled=["Setor", "Treinamento", "Quantidade", "Data"],
    column_config={"Excluir": st.column_config.CheckboxColumn(required=True)},
)

if st.button("🗑️ Excluir selecionados"):
    linhas_para_excluir = editado[editado["Excluir"]].index
    if len(linhas_para_excluir) > 0:
        indices_originais = df_visivel.loc[linhas_para_excluir].index if filtro != "Todos" else linhas_para_excluir
        # Remove pelas colunas-chave para evitar problemas de índice após filtro
        chaves_excluir = editado[editado["Excluir"]][["Setor", "Treinamento", "Quantidade", "Data"]]
        df_full = st.session_state.df.copy()
        df_full["Data_str"] = df_full["Data"].dt.strftime("%d/%m/%Y")
        mask = ~df_full.set_index(["Setor", "Treinamento", "Quantidade", "Data_str"]).index.isin(
            chaves_excluir.set_index(["Setor", "Treinamento", "Quantidade", "Data"]).index
        )
        df_full = df_full[mask].drop(columns=["Data_str"]).reset_index(drop=True)
        st.session_state.df = df_full
        salvar_dados(df_full)
        st.rerun()
    else:
        st.info("Selecione ao menos um registro para excluir.")
