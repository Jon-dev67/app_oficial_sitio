import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Dashboard Tomate E5 - Custo Real", layout="wide")

# Título
st.title("🍅 Dashboard de Produção de Tomate - Talhão E5")
st.markdown("### **Análise com Custo Real de Fertilizantes: R$ 8.000**")
st.markdown("---")

# ======================
# DADOS REAIS - CEASA
# ======================

# Produção real
producao_mensal = {
    "Jun/2025": 280,
    "Jul/2025": 350,
    "Ago/2025": 163,
    "Set/2025": 109
}

# Preços reais CEASA Londrina (média cx 20kg)
preco_mensal = {
    "Jun/2025": 57,
    "Jul/2025": 80,
    "Ago/2025": 98,
    "Set/2025": 105
}

# Receita por mês
receita_mensal = {mes: producao_mensal[mes] * preco_mensal[mes] for mes in producao_mensal}

# Totais
producao_total = sum(producao_mensal.values())
receita_total = sum(receita_mensal.values())
preco_medio_ponderado = receita_total / producao_total

# CUSTOS REAIS
custos_reais = {
    'Sementes': 4000,
    'Viveiro Mudas': 500,
    'Sistema Gotejo': 800,
    'Plástico': 2450,
    'Fertilizantes': 8000
}
custo_total = sum(custos_reais.values())

# Métricas
lucro = receita_total - custo_total
roi = (lucro / custo_total) * 100
margem_lucro = (lucro / receita_total) * 100
custo_por_caixa = custo_total / producao_total

# ======================
# KPI's PRINCIPAIS
# ======================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Produção Total", f"{producao_total} caixas")
with col2:
    st.metric("Receita Total", f"R$ {receita_total:,.0f}")
with col3:
    st.metric("Lucro Líquido", f"R$ {lucro:,.0f}")
with col4:
    st.metric("ROI", f"{roi:.1f}%")

st.markdown("---")

# ======================
# GRÁFICO 1: EVOLUÇÃO
# ======================

st.subheader("📈 Evolução da Produção e Receita por Mês")

df_evolucao = pd.DataFrame({
    "Mês": list(producao_mensal.keys()),
    "Produção (caixas)": list(producao_mensal.values()),
    "Preço Médio (R$/cx)": [preco_mensal[m] for m in producao_mensal],
    "Receita (R$)": list(receita_mensal.values())
})

fig_evolucao = go.Figure()
fig_evolucao.add_trace(go.Bar(
    name="Produção (caixas)",
    x=df_evolucao["Mês"],
    y=df_evolucao["Produção (caixas)"],
    marker_color="#1f77b4",
    text=df_evolucao["Produção (caixas)"],
    textposition="auto"
))
fig_evolucao.add_trace(go.Scatter(
    name="Receita (R$)",
    x=df_evolucao["Mês"],
    y=df_evolucao["Receita (R$)"],
    mode="lines+markers+text",
    line=dict(color="#ff7f0e", width=4),
    marker=dict(size=8),
    text=[f'R$ {rec:,.0f}' for rec in df_evolucao["Receita (R$)"]],
    textposition="top center"
))

fig_evolucao.update_layout(
    title="Evolução Mensal da Produção e Receita (Preços CEASA Reais)",
    xaxis=dict(title="Mês"),
    yaxis=dict(title="Produção (caixas)", side="left"),
    yaxis2=dict(title="Receita (R$)", side="right", overlaying="y"),
    legend=dict(x=0, y=1.1, orientation="h"),
    hovermode="x unified"
)

st.plotly_chart(fig_evolucao, use_container_width=True)

# ======================
# GRÁFICO 2: CUSTOS
# ======================

st.subheader("📊 Distribuição dos Custos Reais (Com Fertilizantes Corrigidos)")

fig_custos = px.pie(
    values=list(custos_reais.values()),
    names=list(custos_reais.keys()),
    title=f"Distribuição dos Custos Reais - Fertilizantes: {custos_reais['Fertilizantes']/custo_total:.0%} do Total",
    hole=0.4,
    color_discrete_sequence=px.colors.qualitative.Set3
)
fig_custos.update_traces(textposition="inside", textinfo="percent+label+value")
st.plotly_chart(fig_custos, use_container_width=True)

# ======================
# GRÁFICO 3: RENTABILIDADE
# ======================

st.subheader("💰 Análise de Rentabilidade")

col1, col2, col3 = st.columns(3)

with col1:
    fig_roi = go.Figure(go.Indicator(
        mode="gauge+number",
        value=roi,
        title={"text": "ROI (%)"},
        gauge={
            "axis": {"range": [0, 400]},
            "bar": {"color": "green"},
            "steps": [
                {"range": [0, 100], "color": "red"},
                {"range": [100, 200], "color": "orange"},
                {"range": [200, 400], "color": "green"}
            ]
        }
    ))
    st.plotly_chart(fig_roi, use_container_width=True)

with col2:
    fig_margem = go.Figure(go.Indicator(
        mode="gauge+number",
        value=margem_lucro,
        title={"text": "Margem de Lucro (%)"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "blue"},
            "steps": [
                {"range": [0, 30], "color": "red"},
                {"range": [30, 60], "color": "orange"},
                {"range": [60, 100], "color": "green"}
            ]
        }
    ))
    st.plotly_chart(fig_margem, use_container_width=True)

with col3:
    fig_custo_caixa = go.Figure(go.Indicator(
        mode="number",
        value=custo_por_caixa,
        number={"prefix": "R$ "},
        title={"text": "Custo por Caixa"}
    ))
    st.plotly_chart(fig_custo_caixa, use_container_width=True)

# ======================
# RESUMO EXECUTIVO
# ======================

st.markdown("---")
st.subheader("🎯 Resumo Executivo - Com Custos Reais e Preços CEASA")

st.success(f"""
**RESULTADOS REAIS (Jun-Set/2025):**

* ✅ **Produção Total**: {producao_total} caixas
* ✅ **Receita Bruta**: R$ {receita_total:,.0f}
* ✅ **Custo Total**: R$ {custo_total:,.0f} (Fertilizantes: R$ 8.000)
* ✅ **Lucro Líquido**: R$ {lucro:,.0f}
* ✅ **ROI**: {roi:.1f}%
* ✅ **Margem de Lucro**: {margem_lucro:.1f}%
* ✅ **Custo por Caixa**: R$ {custo_por_caixa:.2f}
* ✅ **Preço Médio Ponderado da Caixa**: R$ {preco_medio_ponderado:.2f}

**DESTAQUE:** Os fertilizantes representam **{custos_reais['Fertilizantes']/custo_total:.0%} do custo total**.
""")

# ======================
# TABELA DE CUSTOS
# ======================

st.subheader("📋 Detalhamento dos Custos Reais")

df_custos = pd.DataFrame({
    "Item": list(custos_reais.keys()),
    "Custo (R$)": list(custos_reais.values()),
    "Percentual do Total": [f"{(custo/custo_total)*100:.1f}%" for custo in custos_reais.values()]
})
st.dataframe(df_custos, use_container_width=True)

# ======================
# ANÁLISE DOS FERTILIZANTES
# ======================

st.subheader("🌱 Análise dos Fertilizantes")

st.info(f"""
**INFORMAÇÕES SOBRE FERTILIZANTES:**

* **33 aplicações** entre abril e julho/2025
* **Investimento total**: R$ {custos_reais['Fertilizantes']:,.0f}
* **Representa**: {custos_reais['Fertilizantes']/custo_total:.0%} do custo total
* **Eficiência**: Produção de {producao_total} caixas = {producao_total/custos_reais['Fertilizantes']:.2f} caixas por R$ 1 investido

**CUSTO-BENEFÍCIO:** Cada real investido em fertilizantes retornou R$ {receita_total/custos_reais['Fertilizantes']:.2f} em receita.
""")

st.markdown("---")
st.caption(f"Dashboard com custos reais corrigidos e preços CEASA | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
