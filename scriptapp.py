import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Dashboard Tomate E5 - Análise Premium", layout="wide")

# Título
st.title("🍅 Dashboard de Produção de Tomate - Talhão E5")
st.markdown("### **Análise com Valor de Venda: R$ 70,00 por caixa**")
st.markdown("---")

# DADOS REAIS CORRIGIDOS
producao_total = 902
preco_caixa = 70
receita_total = producao_total * preco_caixa

custos = {
    'Fertilizantes': 3200,
    'Mão de Obra': 3000,
    'Irrigação/Energia': 1200,
    'Outros': 600
}

custo_total = sum(custos.values())
lucro = receita_total - custo_total
roi = (lucro / custo_total) * 100

# KPI's PRINCIPAIS
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Produção Total", f"{producao_total} caixas", "902 caixas")
with col2:
    st.metric("Receita Total", f"R$ {receita_total:,.0f}", "R$ 63.140", delta_color="off")
with col3:
    st.metric("Lucro Líquido", f"R$ {lucro:,.0f}", "R$ 55.140")
with col4:
    st.metric("ROI", f"{roi:.1f}%", "689,3%")

st.markdown("---")

# GRÁFICO 1: EVOLUÇÃO DA PRODUÇÃO
st.subheader("📈 Evolução da Produção e Receita")

producao_mensal = {
    'Mês': ['Jun/25', 'Jul/25', 'Ago/25', 'Set/25'],
    'Produção (cx)': [280, 350, 163, 109],
    'Receita (R$)': [280*70, 350*70, 163*70, 109*70]
}

df_mensal = pd.DataFrame(producao_mensal)

fig = go.Figure()
fig.add_trace(go.Bar(name='Produção (cx)', x=df_mensal['Mês'], y=df_mensal['Produção (cx)'],
                    yaxis='y', offsetgroup=1))
fig.add_trace(go.Scatter(name='Receita (R$)', x=df_mensal['Mês'], y=df_mensal['Receita (R$)'],
                        yaxis='y2', line=dict(color='red', width=3)))

fig.update_layout(
    title='Produção Mensal vs Receita',
    xaxis=dict(title='Mês'),
    yaxis=dict(title='Produção (caixas)', side='left'),
    yaxis2=dict(title='Receita (R$)', side='right', overlaying='y'),
    legend=dict(x=0, y=1.1, orientation='h')
)

st.plotly_chart(fig, use_container_width=True)

# GRÁFICO 2: ANÁLISE FINANCEIRA DETALHADA
st.subheader("💰 Análise Financeira Detalhada")

col1, col2 = st.columns(2)

with col1:
    # Distribuição de custos
    fig_custos = px.pie(values=list(custos.values()), names=list(custos.keys()),
                       title="Distribuição de Custos", hole=0.4)
    fig_custos.update_traces(textposition='inside', textinfo='percent+label+value')
    st.plotly_chart(fig_custos, use_container_width=True)

with col2:
    # Comparação Receita vs Lucro
    categorias = ['Custos', 'Lucro']
    valores = [custo_total, lucro]
    cores = ['#FF6B6B', '#51CF66']
    
    fig_comparacao = px.bar(x=categorias, y=valores, title='Lucro vs Custos',
                           color=categorias, color_discrete_sequence=cores)
    fig_comparacao.update_layout(showlegend=False)
    st.plotly_chart(fig_comparacao, use_container_width=True)

# GRÁFICO 3: ROI E MARGEM DE LUCRO
st.subheader("📊 Indicadores de Rentabilidade")

col1, col2, col3 = st.columns(3)

with col1:
    margem_lucro = (lucro / receita_total) * 100
    fig_margem = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = margem_lucro,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Margem de Lucro (%)"},
        gauge = {'axis': {'range': [0, 100]},
                'bar': {'color': "green"},
                'steps': [{'range': [0, 50], 'color': "lightgray"},
                         {'range': [50, 100], 'color': "gray"}]}
    ))
    st.plotly_chart(fig_margem, use_container_width=True)

with col2:
    fig_roi = go.Figure(go.Indicator(
        mode = "number+delta",
        value = roi,
        number = {'prefix': "", 'suffix': "%"},
        title = {'text': "ROI (Retorno sobre Investimento)"},
        delta = {'reference': 100, 'relative': False}
    ))
    st.plotly_chart(fig_roi, use_container_width=True)

with col3:
    custo_por_caixa = custo_total / producao_total
    fig_custo_caixa = go.Figure(go.Indicator(
        mode = "number",
        value = custo_por_caixa,
        number = {'prefix': "R$ "},
        title = {'text': "Custo por Caixa"}
    ))
    st.plotly_chart(fig_custo_caixa, use_container_width=True)

# RESUMO EXECUTIVO
st.markdown("---")
st.subheader("🎯 Resumo Executivo")

st.success(f"""
**RESULTADOS FINANCEIROS COM R$ 70/CAIXA:**

- ✅ **Receita Bruta**: R$ {receita_total:,.0f}
- ✅ **Custo Total**: R$ {custo_total:,.0f}
- ✅ **Lucro Líquido**: R$ {lucro:,.0f}
- ✅ **ROI**: {roi:.1f}% (Excelente!)
- ✅ **Margem de Lucro**: {margem_lucro:.1f}%
- ✅ **Custo por Caixa**: R$ {custo_por_caixa:.1f}

**CONCLUSÃO:** O cultivo de tomate no talhão E5 apresentou **rentabilidade excepcional** com 
um ROI de quase 700%, demonstrando alta eficiência produtiva e excelente retorno financeiro.
""")

# RECOMENDAÇÕES
st.subheader("💡 Recomendações para Melhoria Contínua")

recomendacoes = """
1. **Manter estratégia de fertirrigação** - mostrou-se eficiente
2. **Expandir área plantada** - ROI muito atraente
3. **Diversificar variedades** - explorar tomates com maior valor agregado
4. **Melhorar logística de colheita** - reduzir perdas pós-colheita
5. **Negociar contratos futuros** - travar preços vantajosos
"""

st.info(recomendacoes)

st.markdown("---")
st.caption("Dashboard gerado em " + datetime.now().strftime("%d/%m/%Y %H:%M"))
