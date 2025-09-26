import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Dashboard Tomate E5 - Custo Completo", layout="wide")

# Título
st.title("🍅 Dashboard de Produção de Tomate - Talhão E5")
st.markdown("### **Análise com Custos Totais Incluindo Insutos**")
st.markdown("---")

# DADOS REAIS ATUALIZADOS
producao_total = 902
preco_caixa = 70
receita_total = producao_total * preco_caixa

# NOVOS CUSTOS DETALHADOS
custos_detalhados = {
    'Sementes': 4000,
    'Viveiro Mudas': 500,
    'Sistema Gotejo': 800,
    'Plástico': 2450,
    'Fertilizantes': 3200,
    'Mão de Obra': 3000,
    'Irrigação/Energia': 1200,
    'Outros': 600
}

custo_total = sum(custos_detalhados.values())
lucro = receita_total - custo_total
roi = (lucro / custo_total) * 100
margem_lucro = (lucro / receita_total) * 100

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

# GRÁFICO 1: DISTRIBUIÇÃO DETALHADA DE CUSTOS
st.subheader("📊 Distribuição Detalhada dos Custos")

# Agrupar custos por categoria
custos_agrupados = {
    'Insumos Iniciais': custos_detalhados['Sementes'] + custos_detalhados['Viveiro Mudas'] + 
                       custos_detalhados['Sistema Gotejo'] + custos_detalhados['Plástico'],
    'Fertilizantes': custos_detalhados['Fertilizantes'],
    'Mão de Obra': custos_detalhados['Mão de Obra'],
    'Operacionais': custos_detalhados['Irrigação/Energia'] + custos_detalhados['Outros']
}

fig_custos_agrupados = px.pie(
    values=list(custos_agrupados.values()), 
    names=list(custos_agrupados.keys()),
    title="Distribuição de Custos por Categoria",
    hole=0.4,
    color_discrete_sequence=px.colors.qualitative.Set3
)
fig_custos_agrupados.update_traces(textposition='inside', textinfo='percent+label+value')
st.plotly_chart(fig_custos_agrupados, use_container_width=True)

# GRÁFICO 2: CUSTOS DETALHADOS INDIVIDUAIS
st.subheader("🔍 Detalhamento Individual dos Custos")

fig_custos_detalhados = px.bar(
    x=list(custos_detalhados.keys()), 
    y=list(custos_detalhados.values()),
    title="Custos Individuais por Item",
    color=list(custos_detalhados.values()),
    color_continuous_scale='viridis'
)
fig_custos_detalhados.update_layout(xaxis_title="Itens de Custo", yaxis_title="Valor (R$)")
st.plotly_chart(fig_custos_detalhados, use_container_width=True)

# GRÁFICO 3: ANÁLISE DE RENTABILIDADE
st.subheader("💰 Análise de Rentabilidade")

col1, col2, col3 = st.columns(3)

with col1:
    # ROI
    fig_roi = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
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
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': roi
            }
        }
    ))
    st.plotly_chart(fig_roi, use_container_width=True)

with col2:
    # Margem de Lucro
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
    # Custo por Caixa
    custo_por_caixa = custo_total / producao_total
    fig_custo_caixa = go.Figure(go.Indicator(
        mode = "number+delta",
        value = custo_por_caixa,
        number = {'prefix': "R$ "},
        title = {'text': "Custo por Caixa"},
        delta = {'reference': 20, 'relative': False}
    ))
    st.plotly_chart(fig_custo_caixa, use_container_width=True)

# RESUMO EXECUTIVO ATUALIZADO
st.markdown("---")
st.subheader("🎯 Resumo Executivo com Custos Completos")

st.success(f"""
**RESULTADOS FINANCEIROS INCLUINDO TODOS OS INSUMOS:**

- ✅ **Produção Total**: 902 caixas
- ✅ **Receita Bruta**: R$ {receita_total:,.0f}
- ✅ **Custo Total**: R$ {custo_total:,.0f}
- ✅ **Lucro Líquido**: R$ {lucro:,.0f}
- ✅ **ROI**: {roi:.1f}% (Excelente!)
- ✅ **Margem de Lucro**: {margem_lucro:.1f}%
- ✅ **Custo por Caixa**: R$ {custo_por_caixa:.1f}

**INVESTIMENTOS INICIAIS:**
- Sementes (5000 pés): R$ 4.000
- Viveiro: R$ 500
- Sistema gotejo: R$ 800
- Plástico (1750m): R$ 2.450

**CONCLUSÃO:** Mesmo com todos os custos iniciais, o projeto apresenta **rentabilidade excelente** 
com ROI de 300% e margem de lucro de 75%.
""")

# TABELA DE CUSTOS DETALHADA
st.subheader("📋 Tabela de Custos Detalhada")

df_custos = pd.DataFrame({
    'Item': list(custos_detalhados.keys()),
    'Custo (R$)': list(custos_detalhados.values()),
    'Percentual (%)': [round((custo/custo_total)*100, 1) for custo in custos_detalhados.values()]
})

st.dataframe(df_custos, use_container_width=True)

# RECOMENDAÇÕES FINAIS
st.subheader("💡 Recomendações Estratégicas")

recomendacoes = """
1. **Manter fornecedor de sementes** - custo competitivo (R$ 0,80/semente)
2. **Otimizar uso de plástico** - maior custo inicial após sementes
3. **Expandir área com mesmo sistema** - ROI comprovado de 300%
4. **Negociar desconto por volume** na compra de sementes e plástico
5. **Manter sistema de gotejo** - eficiência comprovada
"""

st.info(recomendacoes)

st.markdown("---")
st.caption(f"Dashboard atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')} | Incluindo todos os insumos informados")
