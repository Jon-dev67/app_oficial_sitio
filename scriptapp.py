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

# DADOS REAIS CORRIGIDOS
producao_total = 902
preco_caixa = 70
receita_total = producao_total * preco_caixa

# CUSTOS REAIS CORRIGIDOS
custos_reais = {
    'Sementes': 4000,
    'Viveiro Mudas': 500,
    'Sistema Gotejo': 800,
    'Plástico': 2450,
    'Fertilizantes': 8000  # CORRIGIDO PARA R$ 8.000
}

custo_total = sum(custos_reais.values())
lucro = receita_total - custo_total
roi = (lucro / custo_total) * 100
margem_lucro = (lucro / receita_total) * 100
custo_por_caixa = custo_total / producao_total

# KPI's PRINCIPAIS
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Produção Total", f"{producao_total} caixas", "902 caixas")
with col2:
    st.metric("Receita Total", f"R$ {receita_total:,.0f}", "R$ 63.140")
with col3:
    st.metric("Lucro Líquido", f"R$ {lucro:,.0f}", "R$ 47.390")
with col4:
    st.metric("ROI", f"{roi:.1f}%", "300,9%")

st.markdown("---")

# GRÁFICO 1: EVOLUÇÃO DA PRODUÇÃO E RECEITA
st.subheader("📈 Evolução da Produção e Receita por Mês")

evolucao_mensal = {
    'Mês': ['Jun/2025', 'Jul/2025', 'Ago/2025', 'Set/2025'],
    'Produção (caixas)': [280, 350, 163, 109],
    'Receita (R$)': [280*70, 350*70, 163*70, 109*70]
}

df_evolucao = pd.DataFrame(evolucao_mensal)

fig_evolucao = go.Figure()
fig_evolucao.add_trace(go.Bar(
    name='Produção (caixas)',
    x=df_evolucao['Mês'],
    y=df_evolucao['Produção (caixas)'],
    yaxis='y',
    marker_color='#1f77b4',
    text=df_evolucao['Produção (caixas)'],
    textposition='auto'
))
fig_evolucao.add_trace(go.Scatter(
    name='Receita (R$)',
    x=df_evolucao['Mês'],
    y=df_evolucao['Receita (R$)'],
    yaxis='y2',
    mode='lines+markers+text',
    line=dict(color='#ff7f0e', width=4),
    marker=dict(size=8),
    text=[f'R$ {rec:,.0f}' for rec in df_evolucao['Receita (R$)']],
    textposition='top center'
))

fig_evolucao.update_layout(
    title='Evolução Mensal da Produção e Receita',
    xaxis=dict(title='Mês'),
    yaxis=dict(title='Produção (caixas)', side='left', range=[0, 400]),
    yaxis2=dict(title='Receita (R$)', side='right', overlaying='y', range=[0, 30000], tickformat=',.0f'),
    legend=dict(x=0, y=1.1, orientation='h'),
    hovermode='x unified'
)

st.plotly_chart(fig_evolucao, use_container_width=True)

# GRÁFICO 2: DISTRIBUIÇÃO DOS CUSTOS REAIS CORRIGIDOS
st.subheader("📊 Distribuição dos Custos Reais (Com Fertilizantes Corrigidos)")

fig_custos = px.pie(
    values=list(custos_reais.values()), 
    names=list(custos_reais.keys()),
    title="Distribuição dos Custos Reais - Fertilizantes: 51% do Total",
    hole=0.4,
    color_discrete_sequence=px.colors.qualitative.Set3
)
fig_custos.update_traces(textposition='inside', textinfo='percent+label+value')
st.plotly_chart(fig_custos, use_container_width=True)

# GRÁFICO 3: ANÁLISE DE RENTABILIDADE
st.subheader("💰 Análise de Rentabilidade")

col1, col2, col3 = st.columns(3)

with col1:
    fig_roi = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = roi,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "ROI (%)"},
        gauge = {
            'axis': {'range': [0, 400]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, 100], 'color': "red"},
                {'range': [100, 200], 'color': "orange"},
                {'range': [200, 400], 'color': "green"}
            ]
        }
    ))
    st.plotly_chart(fig_roi, use_container_width=True)

with col2:
    fig_margem = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = margem_lucro,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Margem de Lucro (%)"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "blue"},
            'steps': [
                {'range': [0, 30], 'color': "red"},
                {'range': [30, 60], 'color': "orange"},
                {'range': [60, 100], 'color': "green"}
            ]
        }
    ))
    st.plotly_chart(fig_margem, use_container_width=True)

with col3:
    fig_custo_caixa = go.Figure(go.Indicator(
        mode = "number",
        value = custo_por_caixa,
        number = {'prefix': "R$ "},
        title = {'text': "Custo por Caixa"}
    ))
    st.plotly_chart(fig_custo_caixa, use_container_width=True)

# RESUMO EXECUTIVO CORRIGIDO
st.markdown("---")
st.subheader("🎯 Resumo Executivo - Com Custos Reais")

st.success(f"""
**RESULTADOS COM CUSTOS REAIS CORRIGIDOS:**

- ✅ **Produção Total**: 902 caixas
- ✅ **Receita Bruta**: R$ {receita_total:,.0f}
- ✅ **Custo Total**: R$ {custo_total:,.0f} (Fertilizantes: R$ 8.000)
- ✅ **Lucro Líquido**: R$ {lucro:,.0f}
- ✅ **ROI**: {roi:.1f}%
- ✅ **Margem de Lucro**: {margem_lucro:.1f}%
- ✅ **Custo por Caixa**: R$ {custo_por_caixa:.1f}

**DESTAQUE:** Os fertilizantes representam **51% do custo total**, mostrando a importância 
do manejo eficiente da fertirrigação.
""")

# TABELA DE CUSTOS CORRIGIDA
st.subheader("📋 Detalhamento dos Custos Reais")

df_custos = pd.DataFrame({
    'Item': list(custos_reais.keys()),
    'Custo (R$)': list(custos_reais.values()),
    'Percentual do Total': [f"{(custo/custo_total)*100:.1f}%" for custo in custos_reais.values()]
})

st.dataframe(df_custos, use_container_width=True)

# ANÁLISE DOS FERTILIZANTES
st.subheader("🌱 Análise dos Fertilizantes")

st.info(f"""
**INFORMAÇÕES SOBRE FERTILIZANTES:**
- **33 aplicações** entre abril e julho/2025
- **Investimento total**: R$ 8.000
- **Representa**: 51% do custo total
- **Eficiência**: Produção de 902 caixas = 0,11 caixas por R$ 1 investido em fertilizantes

**CUSTO-BENEFÍCIO:** Cada real investido em fertilizantes retornou R$ 5,92 em receita.
""")

st.markdown("---")
st.caption(f"Dashboard com custos reais corrigidos | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
