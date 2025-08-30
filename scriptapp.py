# scriptapp.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import requests
import urllib.parse
import json
import os
import subprocess
import sys
from datetime import date, datetime
from io import BytesIO
from pathlib import Path

# ========== AUTO-INSTALL (reportlab) ==========
try:
    import reportlab
except Exception:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
        import reportlab
    except Exception:
        pass

# ========== CONFIG INICIAIS ==========
st.set_page_config(page_title="🌱 Painel Integrado — Sitio", layout="wide", initial_sidebar_state="expanded")
plt.style.use("dark_background")
sns.set_theme(style="darkgrid")

DEFAULT_CITY = "Londrina"

# ========== DIRETÓRIOS E ARQUIVOS ==========
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
PRODUCAO_FILE = DATA_DIR / "producao.xlsx"
INSUMOS_FILE = DATA_DIR / "insumos.xlsx"
FENOLOGIA_FILE = DATA_DIR / "fenologia.xlsx"
CONFIG_FILE = DATA_DIR / "config.json"

# ========== FUNÇÕES DE ARQUIVOS ==========
def load_table(nome):
    f = DATA_DIR / f"{nome}.xlsx"
    if f.exists():
        return pd.read_excel(f, parse_dates=["data"] if "data" in pd.read_excel(f).columns else None)
    else:
        if nome == "producao":
            cols = ["id","data","local","produto","caixas","caixas_segunda","temperatura","umidade","chuva","observacao"]
        elif nome == "insumos":
            cols = ["id","data","local","produto","tipo","quantidade","unidade","custo_total","observacao"]
        elif nome == "fenologia":
            cols = ["id","cultura","estagio","dias","recomendacao","adubo_kg"]
        else:
            cols = []
        return pd.DataFrame(columns=cols)

def save_table(df, nome):
    f = DATA_DIR / f"{nome}.xlsx"
    df.to_excel(f, index=False, engine="openpyxl")

def load_config(defaults=None):
    if defaults is None:
        defaults = {"cidade_padrao":DEFAULT_CITY,"alerta_pct_segunda":25.0,"alerta_prod_baixo_pct":30.0}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE,"r") as f:
            cfg = json.load(f)
        defaults.update(cfg)
    return defaults

def save_config(cfg):
    with open(CONFIG_FILE,"w") as f:
        json.dump(cfg,f, indent=4)

# ========== CRUD PRODUÇÃO ==========
def inserir_producao(data, local, produto, caixas, caixas_segunda, temp, umidade, chuva, obs=""):
    df = load_table("producao")
    next_id = df["id"].max()+1 if not df.empty else 1
    df = pd.concat([df, pd.DataFrame([{
        "id": next_id,
        "data": pd.to_datetime(data),
        "local": local,
        "produto": produto,
        "caixas": caixas,
        "caixas_segunda": caixas_segunda,
        "temperatura": temp,
        "umidade": umidade,
        "chuva": chuva,
        "observacao": obs
    }])], ignore_index=True)
    save_table(df, "producao")

def query_producao(filters=None):
    df = load_table("producao")
    if filters:
        if "local" in filters: df = df[df["local"].isin(filters["local"])]
        if "produto" in filters: df = df[df["produto"].isin(filters["produto"])]
        if "start_date" in filters: df = df[df["data"]>=pd.to_datetime(filters["start_date"])]
        if "end_date" in filters: df = df[df["data"]<=pd.to_datetime(filters["end_date"])]
    return df

def delete_producao_by_ids(ids):
    df = load_table("producao")
    df = df[~df["id"].isin(ids)]
    save_table(df, "producao")

# ========== CRUD INSUMOS ==========
def inserir_insumo(data, local, produto, tipo, quantidade, unidade, custo_total, obs=""):
    df = load_table("insumos")
    next_id = df["id"].max()+1 if not df.empty else 1
    df = pd.concat([df, pd.DataFrame([{
        "id": next_id,
        "data": pd.to_datetime(data),
        "local": local,
        "produto": produto,
        "tipo": tipo,
        "quantidade": quantidade,
        "unidade": unidade,
        "custo_total": custo_total,
        "observacao": obs
    }])], ignore_index=True)
    save_table(df, "insumos")

def query_insumos(filters=None):
    df = load_table("insumos")
    if filters:
        if "local" in filters: df = df[df["local"].isin(filters["local"])]
        if "start_date" in filters: df = df[df["data"]>=pd.to_datetime(filters["start_date"])]
        if "end_date" in filters: df = df[df["data"]<=pd.to_datetime(filters["end_date"])]
    return df

def delete_insumos_by_ids(ids):
    df = load_table("insumos")
    df = df[~df["id"].isin(ids)]
    save_table(df, "insumos")

# ========== CRUD FENOLOGIA ==========
def inserir_fenologia(cultura, estagio, dias, recomendacao, adubo_kg):
    df = load_table("fenologia")
    next_id = df["id"].max()+1 if not df.empty else 1
    df = pd.concat([df, pd.DataFrame([{
        "id": next_id,
        "cultura": cultura,
        "estagio": estagio,
        "dias": dias,
        "recomendacao": recomendacao,
        "adubo_kg": adubo_kg
    }])], ignore_index=True)
    save_table(df, "fenologia")

def listar_fenologia():
    return load_table("fenologia")

def update_fenologia(id_, cultura, estagio, dias, recomendacao, adubo_kg):
    df = load_table("fenologia")
    df.loc[df["id"]==id_, ["cultura","estagio","dias","recomendacao","adubo_kg"]] = [cultura, estagio, dias, recomendacao, adubo_kg]
    save_table(df, "fenologia")

def delete_fenologia(id_):
    df = load_table("fenologia")
    df = df[df["id"]!=id_]
    save_table(df, "fenologia")

# ========== UTILITÁRIOS ==========
def normalizar_colunas_df(df):
    df = df.copy()
    col_map = {
        "Estufa":"local", "Área":"local", "Produção":"caixas", "Primeira":"caixas",
        "Segunda":"caixas_segunda", "Qtd":"caixas", "Quantidade":"caixas"
    }
    df.rename(columns={c:col_map.get(c,c) for c in df.columns}, inplace=True)
    for col in ["data","local","produto","caixas","caixas_segunda","temperatura","umidade","chuva"]:
        if col not in df.columns:
            if col in ["caixas","caixas_segunda"]:
                df[col] = 0
            else:
                df[col] = ""
    try:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
    except Exception:
        pass
    return df

def compute_percentuais_from_df(df):
    df = df.copy()
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    prod = df.groupby("produto")[["caixas","caixas_segunda"]].sum().reset_index()
    prod["total"] = prod["caixas"] + prod["caixas_segunda"]
    prod["pct_2a"] = np.where(prod["total"]>0, (prod["caixas_segunda"]/prod["total"])*100, 0.0)
    loc = df.groupby("local")[["caixas","caixas_segunda"]].sum().reset_index()
    loc["total"] = loc["caixas"] + loc["caixas_segunda"]
    loc["pct_2a"] = np.where(loc["total"]>0, (loc["caixas_segunda"]/loc["total"])*100, 0.0)
    return prod, loc

# ========== CLIMA (OpenWeather) ==========
API_KEY = "eef20bca4e6fb1ff14a81a3171de5cec"
def clima_atual_e_forecast(cidade):
    try:
        q = urllib.parse.quote(cidade)
        url_cur = f"https://api.openweathermap.org/data/2.5/weather?q={q}&appid={API_KEY}&units=metric&lang=pt_br"
        r1 = requests.get(url_cur, timeout=10)
        if r1.status_code != 200:
            return None, None
        data = r1.json()
        atual = {"temp": data["main"]["temp"], "umidade": data["main"]["humidity"], "descricao": data["weather"][0]["description"]}
        url_f = f"https://api.openweathermap.org/data/2.5/forecast?q={q}&appid={API_KEY}&units=metric&lang=pt_br"
        r2 = requests.get(url_f, timeout=10)
        df_fore = None
        if r2.status_code == 200:
            js = r2.json()
            rows = []
            for it in js.get("list", []):
                rows.append({
                    "dt": it["dt_txt"],
                    "temp": it["main"]["temp"],
                    "temp_min": it["main"]["temp_min"],
                    "temp_max": it["main"]["temp_max"],
                    "umidade": it["main"]["humidity"],
                    "descricao": it["weather"][0]["description"]
                })
            if rows:
                df_fore = pd.DataFrame(rows)
                df_fore["dt"] = pd.to_datetime(df_fore["dt"])
        return atual, df_fore
    except Exception:
        return None, None

# ========== PDF RELATÓRIO ==========
def gerar_pdf_relatorio_simple(df_prod, df_prod_pct, df_loc_pct, kpis):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        from reportlab.lib.utils import ImageReader
    except Exception:
        st.error("A biblioteca reportlab não está disponível.")
        return None

    pdf_path = DATA_DIR / f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, height-2*cm, "Relatório de Produção — Sitio")
    c.setFont("Helvetica", 10)
    y = height-3*cm
    for k,v in kpis.items():
        c.drawString(2*cm, y, f"{k}: {v}")
        y -= 0.5*cm
    c.showPage()
    c.save()
    return pdf_path

# ========== CARREGAR CONFIG ==========
cfg = load_config()

# ========== PÁGINAS STREAMLIT ==========
st.sidebar.title("Menu")
page = st.sidebar.radio("Ir para:", ["Painel Integrado","Produção","Insumos","Fenologia","Análises","Clima","Relatórios"])

if page == "Painel Integrado":
    st.title("🌱 Painel Integrado")
    st.write("Configurações atuais:")
    st.json(cfg)
    cidade_new = st.text_input("Cidade padrão:", value=cfg["cidade_padrao"])
    alerta_pct = st.number_input("Alerta % Segunda:", value=cfg["alerta_pct_segunda"])
    alerta_prod_baixo = st.number_input("Alerta % Prod. baixo:", value=cfg["alerta_prod_baixo_pct"])
    if st.button("Salvar Configurações"):
        cfg["cidade_padrao"] = cidade_new
        cfg["alerta_pct_segunda"] = alerta_pct
        cfg["alerta_prod_baixo_pct"] = alerta_prod_baixo
        save_config(cfg)
        st.success("Configurações salvas!")

elif page == "Produção":
    st.title("📦 Produção")
    df_prod = load_table("producao")
    st.dataframe(df_prod)
    st.write("Upload de arquivo Excel")
    file = st.file_uploader("Escolha arquivo", type=["xlsx"])
    if file:
        df_up = pd.read_excel(file)
        df_up = normalizar_colunas_df(df_up)
        df_all = pd.concat([df_prod, df_up], ignore_index=True)
        save_table(df_all, "producao")
        st.success("Dados inseridos com sucesso!")
        st.experimental_rerun()

elif page == "Insumos":
    st.title("🧾 Insumos")
    df_ins = load_table("insumos")
    st.dataframe(df_ins)

elif page == "Fenologia":
    st.title("🌿 Fenologia")
    df_fen = load_table("fenologia")
    st.dataframe(df_fen)

elif page == "Análises":
    st.title("📊 Análises")
    df_prod = load_table("producao")
    prod_pct, loc_pct = compute_percentuais_from_df(df_prod)
    st.subheader("Percentual por Produto")
    st.dataframe(prod_pct)
    st.subheader("Percentual por Local")
    st.dataframe(loc_pct)

elif page == "Clima":
    st.title("☀️ Clima")
    atual, forecast = clima_atual_e_forecast(cfg["cidade_padrao"])
    if atual:
        st.write("Clima Atual:", atual)
    if forecast is not None:
        st.line_chart(forecast[["temp","temp_min","temp_max"]])

elif page == "Relatórios":
    st.title("📄 Relatórios")
    df_prod = load_table("producao")
    prod_pct, loc_pct = compute_percentuais_from_df(df_prod)
    kpis = {"Total Caixas": df_prod["caixas"].sum(), "Total Caixas 2a": df_prod["caixas_segunda"].sum()}
    pdf_file = gerar_pdf_relatorio_simple(df_prod, prod_pct, loc_pct, kpis)
    if pdf_file:
        with open(pdf_file,"rb") as f:
            st.download_button("Baixar PDF", f, file_name=pdf_file.name)
