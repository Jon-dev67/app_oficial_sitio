import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import requests
import urllib.parse
import json
from io import BytesIO
from datetime import date, datetime
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import os

# ===============================
# CONFIGURAÇÕES INICIAIS
# ===============================
st.set_page_config(page_title="🌱 Gerenciador Integrado de Produção", layout="wide")
plt.style.use("dark_background")
sns.set_theme(style="darkgrid")

DB_NAME = "dados_sitio.db"
CONFIG_FILE = "config.json"
API_KEY = "eef20bca4e6fb1ff14a81a3171de5cec"  # OpenWeather API Key
CIDADE_PADRAO = "Londrina"

# ===============================
# BANCO DE DADOS
# ===============================
def criar_tabelas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS producao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        estufa TEXT,
        cultura TEXT,
        caixas INTEGER,
        caixas_segunda INTEGER,
        temperatura REAL,
        umidade REAL,
        chuva REAL,
        observacao TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS insumos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        estufa TEXT,
        cultura TEXT,
        tipo TEXT,
        quantidade REAL,
        unidade TEXT,
        custo_total REAL
    )
    """)
    conn.commit()
    conn.close()

def inserir_tabela(nome_tabela, df):
    conn = sqlite3.connect(DB_NAME)
    df.to_sql(nome_tabela, conn, if_exists="append", index=False)
    conn.close()

def carregar_tabela(nome_tabela):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql(f"SELECT * FROM {nome_tabela}", conn)
    conn.close()
    return df

def excluir_linha(nome_tabela, row_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {nome_tabela} WHERE id=?", (row_id,))
    conn.commit()
    conn.close()

criar_tabelas()

# ===============================
# CONFIGURAÇÕES
# ===============================
def carregar_config():
    if not os.path.exists(CONFIG_FILE):
        cfg = {"cidade": CIDADE_PADRAO,
               "fenologia":{"estagios":[{"nome":"Estágio 1","dias":"0-20","adubo":2},
                                        {"nome":"Estágio 2","dias":"21-40","adubo":4},
                                        {"nome":"Estágio 3","dias":"41-60","adubo":6}]},
               "alerta_pct_segunda":25.0,
               "alerta_prod_baixo_pct":30.0}
        with open(CONFIG_FILE,"w",encoding="utf-8") as f:
            json.dump(cfg,f,ensure_ascii=False, indent=4)
        return cfg
    with open(CONFIG_FILE,"r",encoding="utf-8") as f:
        return json.load(f)

def salvar_config(cfg):
    with open(CONFIG_FILE,"w",encoding="utf-8") as f:
        json.dump(cfg,f,ensure_ascii=False, indent=4)

config = carregar_config()

# ===============================
# FUNÇÕES UTILITÁRIAS
# ===============================
def buscar_clima(cidade):
    try:
        city_encoded = urllib.parse.quote(cidade)
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city_encoded}&appid={API_KEY}&units=metric&lang=pt_br"
        r = requests.get(url, timeout=10)
        data = r.json()
        if r.status_code != 200: return None, None
        atual = {"temp": float(data["main"]["temp"]),
                 "umidade": float(data["main"]["humidity"]),
                 "chuva": float(data.get("rain", {}).get("1h", 0) or 0.0)}
        # previsão
        url_forecast = f"https://api.openweathermap.org/data/2.5/forecast?q={city_encoded}&appid={API_KEY}&units=metric&lang=pt_br"
        forecast = requests.get(url_forecast).json()
        previsao=[]
        if forecast.get("cod")=="200":
            for item in forecast["list"]:
                previsao.append({
                    "Data": item["dt_txt"],
                    "Temp Real (°C)": item["main"]["temp"],
                    "Temp Média (°C)": (item["main"]["temp_min"] + item["main"]["temp_max"])/2,
                    "Temp Min (°C)": item["main"]["temp_min"],
                    "Temp Max (°C)": item["main"]["temp_max"],
                    "Umidade (%)": item["main"]["humidity"]
                })
        return atual, pd.DataFrame(previsao)
    except:
        return None, None

def normalizar_colunas(df):
    df = df.copy()
    col_map = {"Estufa":"estufa","Área":"estufa","Produção":"caixas","Primeira":"caixas",
               "Segunda":"caixas_segunda","Qtd":"caixas","Quantidade":"caixas"}
    df.rename(columns={c:col_map.get(c,c) for c in df.columns}, inplace=True)
    if "data" in df.columns: df["data"]=pd.to_datetime(df["data"], errors="coerce")
    for col in ["caixas","caixas_segunda","temperatura","umidade","chuva"]:
        if col not in df.columns: df[col]=0
    if "estufa" not in df.columns: df["estufa"]=""
    if "cultura" not in df.columns: df["cultura"]=""
    return df

def plot_bar_sum(ax, df, x, y, titulo, ylabel, palette="tab20"):
    g = df.groupby(x)[y].sum().reset_index()
    if g.empty: ax.set_axis_off(); return
    sns.barplot(data=g, x=x, y=y, ax=ax, palette=palette)
    ax.set_title(titulo, fontsize=14)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for c in ax.containers: ax.bar_label(c, fmt="%.0f")

# ===============================
# SIDEBAR / MENU
# ===============================
st.sidebar.title("📌 Menu")
pagina = st.sidebar.radio("Escolha a página:", ["Cadastro Produção","Cadastro Insumos","Análise","Configurações"])

# ===============================
# PÁGINA: CADASTRO PRODUÇÃO
# ===============================
if pagina=="Cadastro Produção":
    st.title("📝 Cadastro de Produção")
    df = carregar_tabela("producao")
    cidade = st.sidebar.text_input("🌍 Cidade para clima", value=config.get("cidade",CIDADE_PADRAO))

    with st.form("form_cadastro_producao", clear_on_submit=True):
        col1,col2,col3 = st.columns(3)
        with col1: data_val=st.date_input("Data", value=date.today()); estufa=st.text_input("Estufa")
        with col2: cultura=st.text_input("Cultura"); caixas=st.number_input("Caixas (1ª)", min_value=0, step=1)
        with col3: caixas2=st.number_input("Caixas (2ª)", min_value=0, step=1)
        st.markdown("#### Clima")
        clima=buscar_clima(cidade)[0]
        if clima: temperatura, umidade, chuva = clima["temp"], clima["umidade"], clima["chuva"]; st.info(f"🌡️ {temperatura:.1f}°C | 💧 {umidade:.0f}% | 🌧️ {chuva:.1f}mm")
        else: c1,c2,c3 = st.columns(3); temperatura = st.number_input("Temperatura (°C)"); umidade = st.number_input("Umidade (%)"); chuva=st.number_input("Chuva (mm)")

        enviado = st.form_submit_button("Salvar Registro ✅")
        if enviado:
            novo = pd.DataFrame([{"data":str(data_val),"estufa":estufa.strip(),"cultura":cultura.strip(),
                                 "caixas":int(caixas),"caixas_segunda":int(caixas2),
                                 "temperatura":float(temperatura),"umidade":float(umidade),"chuva":float(chuva),"observacao":""}])
            inserir_tabela("producao",novo)
            st.success("Registro salvo com sucesso!")

    if not df.empty:
        st.markdown("### 📋 Registros recentes")
        st.dataframe(df.sort_values("data").tail(15), use_container_width=True)
        # Excluir linha
        ids = st.multiselect("Selecione ID(s) para excluir", df["id"].tolist())
        if st.button("Excluir selecionados"):
            for i in ids: excluir_linha("producao",i)
            st.success("✅ Linhas excluídas!")

    # Import Excel
    st.subheader("📂 Importar Excel")
    uploaded_file = st.file_uploader("Envie planilha Excel (Produção)", type=["xlsx"])
    if uploaded_file:
        df_excel = pd.read_excel(uploaded_file)
        df_excel = normalizar_colunas(df_excel)
        inserir_tabela("producao", df_excel)
        st.success("✅ Dados importados do Excel!")

# ===============================
# PÁGINA: CADASTRO INSUMOS
# ===============================
elif pagina=="Cadastro Insumos":
    st.title("📦 Cadastro de Insumos")
    df_ins = carregar_tabela("insumos")
    with st.form("form_insumos", clear_on_submit=True):
        c1,c2,c3,c4 = st.columns(4)
        with c1: data_i=st.date_input("Data", value=date.today()); estufa_i=st.text_input("Estufa")
        with c2: cultura_i=st.text_input("Cultura (opcional)"); tipo_i=st.text_input("Tipo")
        with c3: qtd_i=st.number_input("Quantidade", min_value=0.0, step=0.1); un_i=st.text_input("Unidade", value="kg")
        with c4: custo_i=st.number_input("Custo Total", min_value=0.0, step=0.01)
        enviado_i=st.form_submit_button("Salvar Insumo ✅")
        if enviado_i:
            novo=pd.DataFrame([{"data":str(data_i),"estufa":estufa_i,"cultura":cultura_i,"tipo":tipo_i,"quantidade":qtd_i,"unidade":un_i,"custo_total":custo_i}])
            inserir_tabela("insumos",novo)
            st.success("Insumo salvo!")

    st.subheader("📋 Insumos recentes")
    st.dataframe(df_ins.sort_values("data").tail(20), use_container_width=True)

    # Import Excel
    st.subheader("📂 Importar Excel (Insumos)")
    uploaded_file = st.file_uploader("Envie planilha Excel (Insumos)", type=["xlsx"])
    if uploaded_file:
        df_excel = pd.read_excel(uploaded_file)
        df_excel.rename(columns=lambda x:x.lower(), inplace=True)
        inserir_tabela("insumos", df_excel)
        st.success("✅ Dados importados do Excel!")

# ===============================
# PÁGINA: ANÁLISE
# ===============================
elif pagina=="Análise":
    st.title("📊 Análise de Produção")
    df = carregar_tabela("producao")
    if df.empty: st.warning("Nenhum registro para análise!"); st.stop()

    st.subheader("🔥 KPIs")
    total_caixas = df["caixas"].sum()
    total_segunda = df["caixas_segunda"].sum()
    st.metric("Caixas 1ª", total_caixas)
    st.metric("Caixas 2ª", total_segunda)
    st.metric("Total", total_caixas + total_segunda)

    st.subheader("📈 Produção por Estufa")
    fig,ax=plt.subplots(figsize=(10,5))
    plot_bar_sum(ax, df, "estufa", "caixas", "Produção 1ª por Estufa","Caixas")
    st.pyplot(fig)

    st.subheader("📊 Comparativo 1ª x 2ª")
    df_plot = df.melt(id_vars=["estufa"], value_vars=["caixas","caixas_segunda"], var_name="Tipo", value_name="Caixas")
    fig2 = px.bar(df_plot, x="estufa", y="Caixas", color="Tipo", barmode="group")
    st.plotly_chart(fig2,use_container_width=True)

    st.subheader("📉 Percentual de 2ª sobre total")
    df["pct_segunda"] = df["caixas_segunda"] / (df["caixas"] + df["caixas_segunda"]) * 100
    st.bar_chart(df.groupby("estufa")["pct_segunda"].mean())

# ===============================
# PÁGINA: CONFIGURAÇÕES
# ===============================
elif pagina=="Configurações":
    st.title("⚙️ Configurações")
    cidade_new = st.text_input("Cidade padrão para clima", value=config.get("cidade",CIDADE_PADRAO))
    pct_alert = st.number_input("Alerta % de segunda sobre total", value=config.get("alerta_pct_segunda",25.0))
    if st.button("Salvar Configurações"):
        config["cidade"]=cidade_new
        config["alerta_pct_segunda"]=pct_alert
        salvar_config(config)
        st.success("Configurações salvas!")

# ===============================
# EXPORTAR PRODUÇÃO
# ===============================
st.sidebar.subheader("⬇️ Exportar Produção")
if st.sidebar.button("Exportar Produção Excel"):
    df_export = carregar_tabela("producao")
    output = BytesIO()
    df_export.to_excel(output,index=False,sheet_name="Produção")
    output.seek(0)
    st.sidebar.download_button("📥 Baixar Excel", data=output, file_name="producao_exportada.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
