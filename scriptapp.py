# scriptapp.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import requests
import urllib.parse
import sqlite3
import json
import os
import subprocess
import sys
from datetime import date, datetime
from io import BytesIO
from pathlib import Path

# ========== AUTO-INSTALL (reportlab) ==========
# tenta importar reportlab, se faltar instala (útil no Streamlit Cloud quando não quer editar requirements)
try:
    import reportlab
except Exception:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
        import reportlab
    except Exception:
        # se falhar, apenas continue — o app tratará a ausência na hora de gerar PDF
        pass

# ========== CONFIG INICIAIS ==========
st.set_page_config(page_title="🌱 Painel Integrado — Sitio", layout="wide", initial_sidebar_state="expanded")
plt.style.use("dark_background")
sns.set_theme(style="darkgrid")

DB_FILE = "dados_sitio.db"
API_KEY = "eef20bca4e6fb1ff14a81a3171de5cec"  # troque se precisar
DEFAULT_CITY = "Londrina"

# ========== DB HELPERS ==========
def get_conn():
    Path(DB_FILE).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # tabela producao
    cur.execute("""
    CREATE TABLE IF NOT EXISTS producao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        local TEXT,
        produto TEXT,
        caixas INTEGER,
        caixas_segunda INTEGER,
        temperatura REAL,
        umidade REAL,
        chuva REAL,
        observacao TEXT
    )
    """)
    # tabela insumos
    cur.execute("""
    CREATE TABLE IF NOT EXISTS insumos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        local TEXT,
        produto TEXT,
        tipo TEXT,
        quantidade REAL,
        unidade TEXT,
        custo_total REAL,
        observacao TEXT
    )
    """)
    # tabela fenologia
    cur.execute("""
    CREATE TABLE IF NOT EXISTS fenologia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cultura TEXT,
        estagio TEXT,
        dias TEXT,
        recomendacao TEXT,
        adubo_kg REAL
    )
    """)
    # tabela config (key,value)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS config (
        chave TEXT PRIMARY KEY,
        valor TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ========== CONFIG READ / WRITE ==========
def get_config(defaults=None):
    if defaults is None:
        defaults = {
            "cidade_padrao": DEFAULT_CITY,
            "alerta_pct_segunda": "25.0",
            "alerta_prod_baixo_pct": "30.0"
        }
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT chave, valor FROM config")
    rows = cur.fetchall()
    cfg = defaults.copy()
    for k, v in rows:
        cfg[k] = v
    conn.close()
    return cfg

def set_config(chave, valor):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO config(chave, valor) VALUES (?, ?)", (chave, str(valor)))
    conn.commit()
    conn.close()

# ========== CRUD PRODUÇÃO ==========
def inserir_producao(data, local, produto, caixas, caixas_segunda, temp, umidade, chuva, obs=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO producao(data, local, produto, caixas, caixas_segunda, temperatura, umidade, chuva, observacao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data, local, produto, caixas, caixas_segunda, temp, umidade, chuva, obs))
    conn.commit()
    conn.close()

def query_producao(filters=None):
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM producao", conn, parse_dates=["data"])
    conn.close()
    if filters:
        # filters: dict with keys 'local', 'produto', 'start_date', 'end_date'
        if filters.get("local"):
            df = df[df["local"].isin(filters["local"])]
        if filters.get("produto"):
            df = df[df["produto"].isin(filters["produto"])]
        if filters.get("start_date"):
            df = df[df["data"] >= pd.to_datetime(filters["start_date"])]
        if filters.get("end_date"):
            df = df[df["data"] <= pd.to_datetime(filters["end_date"])]
    return df

def delete_producao_by_ids(ids):
    conn = get_conn()
    cur = conn.cursor()
    cur.executemany("DELETE FROM producao WHERE id = ?", [(int(i),) for i in ids])
    conn.commit()
    conn.close()

# ========== CRUD INSUMOS ==========
def inserir_insumo(data, local, produto, tipo, quantidade, unidade, custo_total, obs=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO insumos(data, local, produto, tipo, quantidade, unidade, custo_total, observacao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (data, local, produto, tipo, quantidade, unidade, custo_total, obs))
    conn.commit()
    conn.close()

def query_insumos(filters=None):
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM insumos", conn, parse_dates=["data"])
    conn.close()
    if filters:
        if filters.get("start_date"):
            df = df[df["data"] >= pd.to_datetime(filters["start_date"])]
        if filters.get("end_date"):
            df = df[df["data"] <= pd.to_datetime(filters["end_date"])]
        if filters.get("local"):
            df = df[df["local"].isin(filters["local"])]
    return df

def delete_insumos_by_ids(ids):
    conn = get_conn()
    cur = conn.cursor()
    cur.executemany("DELETE FROM insumos WHERE id = ?", [(int(i),) for i in ids])
    conn.commit()
    conn.close()

# ========== CRUD FENOLOGIA ==========
def inserir_fenologia(cultura, estagio, dias, recomendacao, adubo_kg):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO fenologia(cultura, estagio, dias, recomendacao, adubo_kg)
        VALUES (?, ?, ?, ?, ?)
    """, (cultura, estagio, dias, recomendacao, adubo_kg))
    conn.commit()
    conn.close()

def listar_fenologia():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM fenologia", conn)
    conn.close()
    return df

def update_fenologia(id_, cultura, estagio, dias, recomendacao, adubo_kg):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE fenologia SET cultura=?, estagio=?, dias=?, recomendacao=?, adubo_kg=? WHERE id=?
    """, (cultura, estagio, dias, recomendacao, adubo_kg, id_))
    conn.commit()
    conn.close()

def delete_fenologia(id_):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM fenologia WHERE id=?", (id_,))
    conn.commit()
    conn.close()

# ========== UTILITÁRIOS ==========
def normalizar_colunas_df(df):
    df = df.copy()
    col_map = {
        "Estufa":"local", "Área":"local", "Produção":"caixas", "Primeira":"caixas",
        "Segunda":"caixas_segunda", "Qtd":"caixas", "Quantidade":"caixas"
    }
    df.rename(columns={c:col_map.get(c,c) for c in df.columns}, inplace=True)
    # ensure columns
    for col in ["data","local","produto","caixas","caixas_segunda","temperatura","umidade","chuva"]:
        if col not in df.columns:
            if col in ["caixas","caixas_segunda"]:
                df[col] = 0
            else:
                df[col] = ""
    # parse data
    try:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
    except Exception:
        pass
    return df

# porcentuais util
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
def clima_atual_e_forecast(cidade):
    try:
        q = urllib.parse.quote(cidade)
        url_cur = f"https://api.openweathermap.org/data/2.5/weather?q={q}&appid={API_KEY}&units=metric&lang=pt_br"
        r1 = requests.get(url_cur, timeout=10)
        if r1.status_code != 200:
            return None, None
        data = r1.json()
        atual = {"temp": data["main"]["temp"], "umidade": data["main"]["humidity"], "descricao": data["weather"][0]["description"]}
        # forecast 5 dias
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
    """Gera PDF com reportlab, retorna BytesIO ou None se reportlab faltar."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        from reportlab.lib.utils import ImageReader
    except Exception:
        st.error("A biblioteca reportlab não está disponível. Para gerar PDF adicione 'reportlab' ao requirements ou permita instalação.")
        return None

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    # Título e KPIs
    c.setFont("Helvetica-Bold", 18)
    c.drawString(2*cm, H-2*cm, "Relatório de Produção - Sitio")
    c.setFont("Helvetica", 10)
    y = H - 3*cm
    for k, v in kpis.items():
        c.drawString(2*cm, y, f"{k}: {v}")
        y -= 0.6*cm

    # Gráfico: total por produto (matplotlib -> imagem)
    if not df_prod.empty:
        fig, ax = plt.subplots(figsize=(6, 3))
        df_plot = df_prod.copy().sort_values("caixas", ascending=False)
        sns.barplot(data=df_plot, x="produto", y="caixas", ax=ax, palette="Set2")
        ax.set_title("Total 1ª por Produto")
        ax.set_xlabel("")
        ax.set_ylabel("Caixas")
        for cont in ax.containers:
            ax.bar_label(cont, fmt="%.0f")
        img = BytesIO()
        fig.tight_layout()
        fig.savefig(img, format="png", dpi=150)
        plt.close(fig)
        img.seek(0)
        c.drawImage(ImageReader(img), 2*cm, H-14*cm, width=16*cm, height=6*cm)

    c.showPage()
    # Página 2: percentuais
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, H-2*cm, "Percentual de 2ª Linha")
    if not df_prod_pct.empty:
        fig, ax = plt.subplots(figsize=(6,3))
        dfp = df_prod_pct.sort_values("pct_2a", ascending=False)
        sns.barplot(data=dfp, x="produto", y="pct_2a", ax=ax, palette="viridis")
        ax.set_ylabel("% 2ª")
        for cont in ax.containers:
            ax.bar_label(cont, fmt="%.1f%%")
        img2 = BytesIO()
        fig.tight_layout()
        fig.savefig(img2, format="png", dpi=150)
        plt.close(fig)
        img2.seek(0)
        c.drawImage(ImageReader(img2), 2*cm, H-12*cm, width=16*cm, height=8*cm)

    c.save()
    buf.seek(0)
    return buf

# ========== UI ==========
cfg = get_config()
st.sidebar.title("📌 Menu")
page = st.sidebar.radio("Ir para", ["Dashboard","Cadastro Produção","Cadastro Insumos","Fenologia","Análises (Matplotlib)","Análises (Plotly)","Clima","Configurações","Admin"])

# ---------------- DASHBOARD ----------------
if page == "Dashboard":
    st.title("🌱 Painel Integrado - Dashboard")
    st.markdown("Resumo rápido das últimas entradas e KPIs.")

    # últimos registros
    df_all = query_producao()
    if df_all.empty:
        st.info("Nenhum registro de produção ainda. Vá para 'Cadastro Produção' para adicionar.")
    else:
        st.markdown("### Últimos registros")
        st.dataframe(df_all.sort_values("data", ascending=False).head(10), use_container_width=True)

        # KPIs
        df_all["total"] = df_all["caixas"] + df_all["caixas_segunda"]
        total = int(df_all["total"].sum())
        media = float(df_all["total"].mean())
        pct_segunda = (df_all["caixas_segunda"].sum() / total * 100) if total>0 else 0.0

        c1,c2,c3 = st.columns(3)
        c1.metric("Total de Caixas", f"{total:,}")
        c2.metric("Média por Registro", f"{media:.2f}")
        c3.metric("% 2ª Linha (Geral)", f"{pct_segunda:.1f}%")

        # mini gráfico plotly total por produto
        prod = df_all.groupby("produto")["total"].sum().reset_index().sort_values("total", ascending=False)
        if not prod.empty:
            fig = px.bar(prod, x="produto", y="total", title="Total de Caixas por Produto")
            st.plotly_chart(fig, use_container_width=True)

# ---------------- CADASTRO PRODUÇÃO ----------------
if page == "Cadastro Produção":
    st.title("📝 Cadastro de Produção")
    with st.form("form_prod"):
        col1, col2, col3 = st.columns(3)
        with col1:
            data_input = st.date_input("Data", value=date.today())
            local = st.text_input("Local / Estufa")
        with col2:
            produto = st.text_input("Produto")
            caixas = st.number_input("Caixas (1ª)", min_value=0, step=1, value=0)
        with col3:
            caixas2 = st.number_input("Caixas (2ª)", min_value=0, step=1, value=0)
            obs = st.text_input("Observação (opcional)")
        # clima automático
        city = st.sidebar.text_input("Cidade para clima", value=cfg.get("cidade_padrao", DEFAULT_CITY))
        clima_cur, _ = clima_atual_e_forecast(city)
        if clima_cur:
            st.markdown(f"Clima atual: {clima_cur['temp']}°C | {clima_cur['umidade']}% | {clima_cur.get('descricao','')}")
            temp_val = float(clima_cur["temp"])
            umid_val = float(clima_cur["umidade"])
            chuva_val = 0.0
        else:
            temp_val = st.number_input("Temperatura (°C)", value=0.0, step=0.1)
            umid_val = st.number_input("Umidade (%)", value=0.0, step=0.1)
            chuva_val = st.number_input("Chuva (mm)", value=0.0, step=0.1)
        submitted = st.form_submit_button("Salvar Produção ✅")
        if submitted:
            inserir_producao(str(pd.to_datetime(data_input)), local.strip(), produto.strip(), int(caixas), int(caixas2), float(temp_val), float(umid_val), float(chuva_val), obs.strip())
            st.success("Registro salvo!")

    # mostrar tabela e permitir exclusão
    st.markdown("---")
    st.markdown("### Gerenciar registros de produção")
    dfp = query_producao()
    if not dfp.empty:
        dfp_display = dfp.sort_values("data", ascending=False)
        st.dataframe(dfp_display, use_container_width=True)
        ids_del = st.multiselect("Selecione IDs para excluir (produção)", options=dfp_display["id"].tolist())
        if st.button("Excluir registros selecionados"):
            if ids_del:
                delete_producao_by_ids(ids_del)
                st.success(f"{len(ids_del)} registros excluídos.")
            else:
                st.warning("Nenhum ID selecionado.")
    else:
        st.info("Sem registros para mostrar.")

# ---------------- CADASTRO INSUMOS ----------------
if page == "Cadastro Insumos":
    st.title("📦 Cadastro de Insumos")
    with st.form("form_insumos"):
        col1, col2, col3 = st.columns(3)
        with col1:
            data_i = st.date_input("Data", value=date.today())
            local_i = st.text_input("Local/Estufa")
        with col2:
            produto_i = st.text_input("Produto (opcional)")
            tipo_i = st.text_input("Tipo (ex: Fertilizante)")
        with col3:
            qtd_i = st.number_input("Quantidade", min_value=0.0, step=0.1)
            unidade_i = st.text_input("Unidade (kg/L/un)", value="kg")
        custo_i = st.number_input("Custo total (R$)", min_value=0.0, step=0.01)
        obs_i = st.text_input("Observação (opcional)")
        sub_i = st.form_submit_button("Salvar Insumo ✅")
        if sub_i:
            inserir_insumo(str(pd.to_datetime(data_i)), local_i.strip(), produto_i.strip(), tipo_i.strip(), float(qtd_i), unidade_i.strip(), float(custo_i), obs_i.strip())
            st.success("Insumo salvo!")

    st.markdown("---")
    st.markdown("### Gerenciar Insumos")
    ins_df = query_insumos()
    if not ins_df.empty:
        st.dataframe(ins_df.sort_values("data", ascending=False), use_container_width=True)
        ids_del_ins = st.multiselect("IDs para excluir (insumos)", options=ins_df["id"].tolist())
        if st.button("Excluir insumos selecionados"):
            if ids_del_ins:
                delete_insumos_by_ids(ids_del_ins)
                st.success(f"{len(ids_del_ins)} insumos excluídos.")
            else:
                st.warning("Nenhum ID selecionado.")
    else:
        st.info("Sem insumos cadastrados.")

# ---------------- FENOLOGIA ----------------
if page == "Fenologia":
    st.title("🌿 Fenologia & Nutrição")
    st.markdown("Defina estágios fenológicos por cultura.")
    fen = listar_fenologia()
    cols = st.columns(2)
    with cols[0]:
        st.markdown("#### Adicionar estágio")
        cultura = st.text_input("Cultura (ex: Tomate)", key="f_cultura")
        estagio = st.text_input("Nome do estágio", key="f_estagio")
        dias = st.text_input("Período (dias)", key="f_dias", value="0-20")
        adubo = st.number_input("Adubo (kg) recomendado", min_value=0.0, step=0.1, key="f_adubo")
        rec = st.text_area("Recomendação / Observação", key="f_rec")
        if st.button("Adicionar estágio"):
            inserir_fenologia(cultura.strip(), estagio.strip(), dias.strip(), rec.strip(), float(adubo))
            st.success("Estágio adicionado.")
    with cols[1]:
        st.markdown("#### Estágios cadastrados")
        if fen.empty:
            st.info("Nenhum estágio cadastrado.")
        else:
            st.dataframe(fen, use_container_width=True)
            sel = st.selectbox("Selecionar ID para editar/excluir", options=fen["id"].tolist())
            row = fen[fen["id"]==sel].iloc[0]
            st.markdown("Editar:")
            nc = st.text_input("Cultura", value=row["cultura"], key="edit_cultura")
            ne = st.text_input("Estágio", value=row["estagio"], key="edit_estagio")
            nd = st.text_input("Dias", value=row["dias"], key="edit_dias")
            nad = st.number_input("Adubo (kg)", value=float(row["adubo_kg"] if not np.isnan(row["adubo_kg"]) else 0.0), key="edit_adubo")
            nrec = st.text_area("Recomendação", value=row["recomendacao"], key="edit_rec")
            if st.button("Salvar edição"):
                update_fenologia(int(sel), nc.strip(), ne.strip(), nd.strip(), nrec.strip(), float(nad))
                st.success("Estágio atualizado.")
            if st.button("Excluir estágio"):
                delete_fenologia(int(sel))
                st.success("Estágio excluído.")

# ---------------- ANÁLISES (Matplotlib/Seaborn) ----------------
if page == "Análises (Matplotlib)":
    st.title("📊 Análises (Matplotlib/Seaborn)")
    df_all = query_producao()
    if df_all.empty:
        st.info("Sem dados para análise.")
    else:
        df_all["total"] = df_all["caixas"] + df_all["caixas_segunda"]
        # período
        min_d = df_all["data"].min().date()
        max_d = df_all["data"].max().date()
        date_range = st.sidebar.date_input("Período", value=(min_d, max_d), min_value=min_d, max_value=max_d)
        try:
            s, e = date_range
        except Exception:
            s = e = date_range
        df_f = df_all[(df_all["data"] >= pd.to_datetime(s)) & (df_all["data"] <= pd.to_datetime(e))]
        st.markdown(f"Registros no período: {len(df_f)}")

        # Total por local (matplotlib)
        st.subheader("Total por Local")
        fig, ax = plt.subplots(figsize=(10,4))
        plot_df = df_f.groupby("local")["total"].sum().reset_index().sort_values("total", ascending=False)
        sns.barplot(data=plot_df, x="local", y="total", ax=ax, palette="tab20")
        ax.set_xlabel("")
        for cont in ax.containers:
            ax.bar_label(cont, fmt="%.0f")
        st.pyplot(fig)

        # Comparativo 1ª vs 2ª
        st.subheader("Comparativo 1ª vs 2ª por Produto")
        df_comp = df_f.groupby("produto")[["caixas","caixas_segunda"]].sum().reset_index().melt(id_vars="produto", value_vars=["caixas","caixas_segunda"], var_name="tipo", value_name="qtd")
        fig2, ax2 = plt.subplots(figsize=(12,5))
        sns.barplot(data=df_comp, x="produto", y="qtd", hue="tipo", ax=ax2)
        for cont in ax2.containers:
            ax2.bar_label(cont, fmt="%.0f")
        ax2.set_xlabel("")
        st.pyplot(fig2)

        # Percentuais
        st.subheader("Percentual de 2ª Linha")
        prod_pct, loc_pct = compute_percentuais_from_df(df_f)
        if not prod_pct.empty:
            fig3, ax3 = plt.subplots(figsize=(10,4))
            sns.barplot(data=prod_pct.sort_values("pct_2a", ascending=False), x="produto", y="pct_2a", ax=ax3, palette="viridis")
            ax3.set_ylabel("% 2ª")
            for cont in ax3.containers:
                ax3.bar_label(cont, fmt="%.1f%%")
            st.pyplot(fig3)
        else:
            st.info("Sem percentuais para exibir.")

        # Exportar excel
        buf = BytesIO()
        df_f.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)
        st.download_button("📥 Exportar dados filtrados (Excel)", data=buf, file_name="dados_filtrados.xlsx")

# ---------------- ANÁLISES (Plotly) ----------------
if page == "Análises (Plotly)":
    st.title("📈 Análises Interativas (Plotly)")
    df_all = query_producao()
    if df_all.empty:
        st.info("Sem dados para análise.")
    else:
        df_all["total"] = df_all["caixas"] + df_all["caixas_segunda"]
        min_d = df_all["data"].min().date()
        max_d = df_all["data"].max().date()
        date_range = st.sidebar.date_input("Período (Plotly)", value=(min_d, max_d), min_value=min_d, max_value=max_d)
        try:
            s, e = date_range
        except:
            s = e = date_range
        df_f = df_all[(df_all["data"] >= pd.to_datetime(s)) & (df_all["data"] <= pd.to_datetime(e))].sort_values("data")

        # série temporal total
        st.subheader("Produção ao longo do tempo")
        fig = px.bar(df_f, x="data", y="total", color="produto", title="Produção (total) por data")
        st.plotly_chart(fig, use_container_width=True)

        # linha temp média por dia
        if "temperatura" in df_f.columns:
            st.subheader("Temperatura média por dia")
            temp_df = df_f.groupby(df_f["data"].dt.date)["temperatura"].mean().reset_index().rename(columns={"data":"date"})
            if not temp_df.empty:
                fig2 = px.line(temp_df, x="data", y="temperatura", markers=True, title="Temperatura média por dia")
                st.plotly_chart(fig2, use_container_width=True)

        # heatmap interativo (estufa x semana)
        st.subheader("Heatmap: produção por local vs semana")
        df_f["week"] = df_f["data"].dt.isocalendar().week
        heat = df_f.groupby(["local","week"])["total"].sum().reset_index()
        if not heat.empty:
            pivot = heat.pivot(index="local", columns="week", values="total").fillna(0)
            st.dataframe(pivot, use_container_width=True)
            fig3 = px.imshow(pivot, labels=dict(x="Semana", y="Local", color="Total Caixas"), aspect="auto", title="Produção por Local x Semana")
            st.plotly_chart(fig3, use_container_width=True)

# ---------------- CLIMA ----------------
if page == "Clima":
    st.title("🌤️ Clima & Previsão")
    city = st.text_input("Cidade (para consulta de clima)", value=cfg.get("cidade_padrao", DEFAULT_CITY))
    if st.button("Buscar clima"):
        atual, df_fore = clima_atual_e_forecast(city)
        if atual is None:
            st.error("Não foi possível obter dados de clima. Verifique a API_KEY / conexão.")
        else:
            c1, c2 = st.columns(2)
            c1.metric("Temperatura (°C)", f"{atual['temp']:.1f}")
            c2.metric("Umidade (%)", f"{atual['umidade']:.0f}")
            if df_fore is not None and not df_fore.empty:
                st.markdown("### Previsão (lista)")
                st.dataframe(df_fore.head(40), use_container_width=True)
                fig = px.line(df_fore, x="dt", y=["temp_min","temp","temp_max"], title="Temp min/média/max (próximos dias)")
                st.plotly_chart(fig, use_container_width=True)

# ---------------- CONFIGURAÇÕES ----------------
if page == "Configurações":
    st.title("⚙️ Configurações")
    st.markdown("Ajuste as preferências do app.")
    cidade_new = st.text_input("Cidade padrão (clima)", value=cfg.get("cidade_padrao", DEFAULT_CITY))
    alerta_pct = st.number_input("Alerta % de 2ª (geral)", min_value=0.0, max_value=100.0, value=float(cfg.get("alerta_pct_segunda", "25.0")))
    alerta_prod_baixo = st.number_input("Alerta produto < X% da média", min_value=0.0, max_value=100.0, value=float(cfg.get("alerta_prod_baixo_pct", "30.0")))
    if st.button("Salvar configurações"):
        set_config("cidade_padrao", cidade_new)
        set_config("alerta_pct_segunda", alerta_pct)
        set_config("alerta_prod_baixo_pct", alerta_prod_baixo)
        st.success("Configurações salvas. Recarregue a página se necessário.")

# ---------------- ADMIN ----------------
if page == "Admin":
    st.title("🔧 Admin")
    st.markdown("Operações avançadas: exportar DB, gerar PDF do período, backup, limpar dados.")
    df_all = query_producao()
    if not df_all.empty:
        st.markdown("### Exportar Produção (Excel)")
        b = BytesIO()
        df_all.to_excel(b, index=False, engine="openpyxl")
        b.seek(0)
        st.download_button("📥 Baixar produção completa (Excel)", data=b, file_name="producao_completa.xlsx")

    st.markdown("---")
    st.markdown("### Gerar relatório PDF personalizado")
    if st.button("Gerar PDF com KPIs e gráficos"):
        dfp = query_producao()
        if dfp.empty:
            st.info("Sem dados para gerar relatório.")
        else:
            dfp["total"] = dfp["caixas"] + dfp["caixas_segunda"]
            prod_pct, loc_pct = compute_percentuais_from_df(dfp)
            kpis = {
                "Total de Caixas": f"{int(dfp['total'].sum()):,}",
                "Média por Registro": f"{dfp['total'].mean():.2f}",
                "% 2ª Linha (Geral)": f"{(dfp['caixas_segunda'].sum()/dfp['total'].sum()*100) if dfp['total'].sum()>0 else 0:.1f}%",
                "Registros": f"{len(dfp):,}"
            }
            pdf = gerar_pdf_relatorio_simple(dfp, prod_pct, loc_pct, kpis)
            if pdf:
                st.download_button("📥 Baixar Relatório (PDF)", data=pdf, file_name="relatorio_producao.pdf", mime="application/pdf")

    st.markdown("---")
    st.markdown("### Backup do banco (.db)")
    if st.button("📦 Baixar backup do DB"):
        with open(DB_FILE, "rb") as f:
            st.download_button("📥 Baixar DB", data=f, file_name=DB_FILE)

    st.markdown("---")
    st.markdown("### Resetar dados (CUIDADO)")
    if st.checkbox("Confirme que deseja limpar todas as tabelas"):
        if st.button("Apagar todos os registros"):
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM producao")
            cur.execute("DELETE FROM insumos")
            cur.execute("DELETE FROM fenologia")
            conn.commit()
            conn.close()
            st.success("Todas as tabelas limpas.")

# final note
st.sidebar.markdown("---")
st.sidebar.markdown("Desenvolvido para gestão de produção · Integre sensores/IoT no futuro para automatizar coleta.")
