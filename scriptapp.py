import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Dashboard Tomate E5 - Dados Reais", layout="wide")

# Título
st.title("🍅 Dashboard de Produção de Tomate - Talhão E5")
st.markdown("### **Análise com Dados Reais Informados**")
st.markdown("---")

# DADOS REAIS (APENAS OS INFORMADOS)
producao_total = 902
preco_caixa = 70
receita_total = producao_total * preco_caixa

# CUSTOS REAIS (APENAS OS INFORMADOS)
custos_reais = {
    'Sementes': 4000,
    'Viveiro Mudas': 500,
    'Sistema Gotejo': 800,
    'Plástico': 2450,
    'Fertilizantes': 3200
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
    st.metric("Lucro Líquido", f"R$ {lucro:,.0f}", "R$ 52.190")
with col4:
    st.metric("ROI", f"{roi:.1f}%", "476,6%")

st.markdown("---")

# GRÁFICO 1: EVOLUÇÃO DA PRODUÇÃO E RECEITA POR MÊS
st.subheader("📈 Evolução da Produção e Receita por Mês")

# Dados baseados nos arquivos PDF e Excel
evolucao_mensal = {
    'Mês': ['Jun/2025', 'Jul/2025', 'Ago/2025', 'Set/2025'],
    'Produção (caixas)': [280, 350, 163, 109],  # Baseado nos totais acumulados
    'Receita (R$)': [280*70, 350*70, 163*70, 109*70]
}

df_evolucao = pd.DataFrame(evolucao_mensal)

# Gráfico de barras com duas escalas
fig_evolucao = go.Figure()

# Barras para produção
fig_evolucao.add_trace(go.Bar(
    name='Produção (caixas)',
    x=df_evolucao['Mês'],
    y=df_evolucao['Produção (caixas)'],
    yaxis='y',
    marker_color='#1f77b4',
    text=df_evolucao['Produção (caixas)'],
    textposition='auto'
))

# Linha para receita
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
    yaxis=dict(
        title='Produção (caixas)',
        side='left',
        range=[0, max(df_evolucao['Produção (caixas)']) * 1.2]
    ),
    yaxis2=dict(
        title='Receita (R$)',
        side='right',
        overlaying='y',
        range=[0, max(df_evolucao['Receita (R$)']) * 1.2],
        tickformat=',.0f'
    ),
    legend=dict(x=0, y=1.1, orientation='h'),
    hovermode='x unified'
)

st.plotly_chart(fig_evolucao, use_container_width=True)

# GRÁFICO 2: DISTRIBUIÇÃO DOS CUSTOS REAIS
st.subheader("📊 Distribuição dos Custos Reais")

fig_custos = px.pie(
    values=list(custos_reais.values()), 
    names=list(custos_reais.keys()),
    title="Distribuição dos Custos Reais",
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
            'axis': {'range': [0, 500]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, 100], 'color': "red"},
                {'range': [100, 200], 'color': "orange"},
                {'range': [200, 500], 'color': "green"}
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

# GRÁFICO 4: COMPARAÇÃO RECEITA vs CUSTOS vs LUCRO
st.subheader("📊 Comparação Receita vs Custos vs Lucro")

fig_comparacao = go.Figure()
fig_comparacao.add_trace(go.Bar(name='Custos', x=['Custos'], y=[custo_total], marker_color='red'))
fig_comparacao.add_trace(go.Bar(name='Lucro', x=['Lucro'], y=[lucro], marker_color='green'))
fig_comparacao.add_trace(go.Bar(name='Receita', x=['Receita'], y=[receita_total], marker_color='blue'))
fig_comparacao.update_layout(
    title='Comparação: Receita vs Custos vs Lucro',
    yaxis=dict(tickformat=',.0f')
)
st.plotly_chart(fig_comparacao, use_container_width=True)

# ANÁLISE DA EVOLUÇÃO MENSAL
st.subheader("🔍 Análise da Evolução Mensal")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Produção Mensal:**")
    st.dataframe(df_evolucao[['Mês', 'Produção (caixas)']], use_container_width=True)

with col2:
    st.markdown("**Receita Mensal:**")
    df_receita_mensal = df_evolucao[['Mês', 'Receita (R$)']].copy()
    df_receita_mensal['Receita (R$)'] = df_receita_mensal['Receita (R$)'].apply(lambda x: f'R$ {x:,.0f}')
    st.dataframe(df_receita_mensal, use_container_width=True)

# RESUMO DA EVOLUÇÃO
st.info(f"""
**ANÁLISE DA EVOLUÇÃO MENSAL:**

- **🔺 Pico de Produção**: Julho/2025 (350 caixas = R$ 24.500)
- **📈 Tendência**: Produção crescente até julho, com estabilização após
- **💰 Receita Acumulada**: 
  - Junho: R$ 19.600
  - Julho: R$ 24.500 (pico)
  - Agosto: R$ 11.410
  - Setembro: R$ 7.630

**Total: R$ 63.140**
""")

# RESUMO EXECUTIVO
st.markdown("---")
st.subheader("🎯 Resumo Executivo - Dados Reais")

st.success(f"""
**RESULTADOS COM DADOS REAIS INFORMADOS:**

- ✅ **Produção Total**: 902 caixas (Jun-Set/2025)
- ✅ **Receita Bruta**: R$ {receita_total:,.0f}
- ✅ **Custo Total**: R$ {custo_total:,.0f}
- ✅ **Lucro Líquido**: R$ {lucro:,.0f}
- ✅ **ROI**: {roi:.1f}%
- ✅ **Margem de Lucro**: {margem_lucro:.1f}%
- ✅ **Custo por Caixa**: R$ {custo_por_caixa:.1f}

**CUSTOS CONSIDERADOS (APENAS OS INFORMADOS):**
- Sementes (5000 pés): R$ 4.000
- Viveiro de mudas: R$ 500
- Sistema de gotejo (2 rolos): R$ 800
- Plástico (1750m): R$ 2.450
- Fertilizantes: R$ 3.200
""")

# TABELA DE CUSTOS DETALHADA
st.subheader("📋 Detalhamento dos Custos")

df_custos = pd.DataFrame({
    'Item': list(custos_reais.keys()),
    'Custo (R$)': list(custos_reais.values()),
    'Percentual do Total': [f"{(custo/custo_total)*100:.1f}%" for custo in custos_reais.values()]
})

st.dataframe(df_custos, use_container_width=True)

st.markdown("---")
st.caption(f"Dashboard baseado apenas nos dados reais informados | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
