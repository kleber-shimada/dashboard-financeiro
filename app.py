# ==========================================
# IMPORTAÇÃO DAS BIBLIOTECAS
# ==========================================
import streamlit as st 
import pandas as pd 

# ==========================================
# CONFIGURAÇÃO INICIAL DA PÁGINA
# ==========================================
st.set_page_config(page_title="Meu Dashboard Financeiro", layout="wide")
st.title("📊 Controle Financeiro 2026")

# ---------------------------------------------------------
# FUNÇÕES INTELIGENTES (MÁQUINAS REUTILIZÁVEIS)
# ---------------------------------------------------------
def limpar_valor(coluna):
    return (coluna.astype(str)
            .str.replace('R$', '', regex=False)
            .str.replace(' ', '', regex=False)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .astype(float))

meses_pt = {
    'Janeiro': 1, 'Jan': 1, 'Fevereiro': 2, 'Fev': 2, 'Março': 3, 'Mar': 3, 'Abril': 4, 'Abr': 4,
    'Maio': 5, 'Mai': 5, 'Junho': 6, 'Jun': 6, 'Julho': 7, 'Jul': 7, 'Agosto': 8, 'Ago': 8,
    'Setembro': 9, 'Set': 9, 'Outubro': 10, 'Out': 10, 'Novembro': 11, 'Nov': 11, 'Dezembro': 12, 'Dez': 12
}

def definir_competencia(linha):
    if 'Pagamento' in linha and linha['Pagamento'] == 'Crédito' and pd.notna(linha.get('Fatura Mês')):
        texto = str(linha['Fatura Mês']).strip()
        partes = texto.split() 
        if len(partes) >= 2:
            nome_mes = partes[0].capitalize()
            mes_num = meses_pt.get(nome_mes, 1)
            ano_str = partes[1]
            ano_num = 2000 + int(ano_str) if len(ano_str) == 2 else int(ano_str)
            return pd.to_datetime(f"{ano_num}-{mes_num:02d}-01")
    return linha.get('Data')

df_despesas = pd.DataFrame()
df_receita = pd.DataFrame()

# ==========================================
# LEITURA DOS DADOS (AGORA DIRETO DO GOOGLE SHEETS)
# ==========================================
try:
    # A MÁGICA: O Python busca os links diretamente do Cofre do Streamlit!
    # Se você for testar localmente no VS Code, precisaremos criar um arquivo ".streamlit/secrets.toml",
    # mas para a internet, ele já vai puxar direto da configuração que fizemos.
    url_base = st.secrets["URL_BASE"]
    url_receita = st.secrets["URL_RECEITA"]

    # ==========================================
    # PROCESSAMENTO DAS DESPESAS
    # ==========================================
    df_base = pd.read_csv(url_base)
    df_base.columns = df_base.columns.str.strip() 
    
    df_base['Valor Numérico'] = limpar_valor(df_base['Valor'])
    df_base['Data'] = pd.to_datetime(df_base['Data'], format='mixed', dayfirst=True, errors='coerce')
    
    df_base['Data Competência'] = df_base.apply(definir_competencia, axis=1)
    df_base['Ano'] = df_base['Data Competência'].dt.year
    df_base['Mês'] = df_base['Data Competência'].dt.month
    
    df_despesas = df_base[df_base['Tipo'] == 'Despesa'].dropna(subset=['Ano', 'Mês'])

    # ==========================================
    # PROCESSAMENTO DAS RECEITAS
    # ==========================================
    df_rec_raw = pd.read_csv(url_receita)
    df_rec_raw.columns = df_rec_raw.columns.str.strip() 
    
    df_rec_raw['Valor Numérico'] = limpar_valor(df_rec_raw['Valor'])
    df_rec_raw['Data'] = pd.to_datetime(df_rec_raw['Data'], format='mixed', dayfirst=False, errors='coerce')
    
    df_rec_raw['Ano'] = df_rec_raw['Data'].dt.year
    df_rec_raw['Mês'] = df_rec_raw['Data'].dt.month
    
    df_receita = df_rec_raw.dropna(subset=['Ano', 'Mês'])

except Exception as e:
    # Se houver erro de leitura ou o cofre não estiver configurado, ele avisa.
    st.error(f"Erro ao conectar com o Google Sheets: {e}")

# ==========================================
# MENU LATERAL PARA FILTROS
# ==========================================
st.sidebar.title("🔍 Filtros de Busca")

anos_desp = set(df_despesas['Ano'].unique()) if not df_despesas.empty else set()
anos_rec = set(df_receita['Ano'].unique()) if not df_receita.empty else set()
anos_disponiveis = sorted(list(anos_desp.union(anos_rec)))

lista_anos = ['Todos'] + [int(a) for a in anos_disponiveis]
ano_selecionado = st.sidebar.selectbox("Selecione o Ano", lista_anos)

if ano_selecionado != 'Todos':
    if not df_despesas.empty: df_despesas = df_despesas[df_despesas['Ano'] == ano_selecionado]
    if not df_receita.empty:  df_receita = df_receita[df_receita['Ano'] == ano_selecionado]
    
    meses_desp = set(df_despesas['Mês'].unique()) if not df_despesas.empty else set()
    meses_rec = set(df_receita['Mês'].unique()) if not df_receita.empty else set()
    meses_disponiveis = sorted(list(meses_desp.union(meses_rec)))
    
    lista_meses = ['Todos'] + [int(m) for m in meses_disponiveis]
    mes_selecionado = st.sidebar.selectbox("Selecione o Mês", lista_meses)
    
    if mes_selecionado != 'Todos':
        if not df_despesas.empty: df_despesas = df_despesas[df_despesas['Mês'] == mes_selecionado]
        if not df_receita.empty:  df_receita = df_receita[df_receita['Mês'] == mes_selecionado]

# ==========================================
# CRIAÇÃO DO DASHBOARD VISUAL (A VITRINE)
# ==========================================
st.subheader("💰 Resumo Financeiro do Período")

total_receitas = df_receita['Valor Numérico'].sum() if not df_receita.empty else 0.0
total_despesas = df_despesas['Valor Numérico'].sum() if not df_despesas.empty else 0.0
saldo_liquido = total_receitas - total_despesas

def fmt(val):
    return f"R$ {val:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')

col_rec, col_desp, col_saldo = st.columns(3)
col_rec.metric(label="Total de Receitas (Entradas)", value=fmt(total_receitas))
col_desp.metric(label="Total de Despesas (Saídas)", value=fmt(total_despesas))
col_saldo.metric(label="Saldo Líquido", value=fmt(saldo_liquido), delta=fmt(saldo_liquido))

st.divider() 

if not df_despesas.empty:
    st.write("### 💳 Gastos por Forma de Pagamento")
    gastos_por_pagamento = df_despesas.groupby('Pagamento')['Valor Numérico'].sum().reset_index()
    
    colunas_cartoes = st.columns(len(gastos_por_pagamento))
    for indice, linha in gastos_por_pagamento.iterrows():
        colunas_cartoes[indice].metric(label=str(linha['Pagamento']), value=fmt(linha['Valor Numérico']))
        
    st.divider()

    st.write("### 🛒 Gastos por Categoria")
    gastos_categoria = df_despesas.groupby('Categoria')['Valor Numérico'].sum().sort_values(ascending=False)
    
    col_grafico, col_tabela = st.columns([2, 1])
    with col_grafico:
        st.bar_chart(gastos_categoria)
    with col_tabela:
        tabela_bonita = gastos_categoria.reset_index().rename(columns={'Valor Numérico': 'Total (R$)'})
        st.dataframe(tabela_bonita, hide_index=True)
else:
    st.info("Nenhuma despesa para mostrar neste período.")

st.divider()

st.write("### 📋 Detalhamento dos Dados Filtrados")
aba_desp, aba_rec = st.tabs(["Despesas", "Receitas"])

with aba_desp:
    if not df_despesas.empty: st.dataframe(df_despesas)
    else: st.info("Sem dados de despesas.")

with aba_rec:
    if not df_receita.empty: st.dataframe(df_receita)
    else: st.info("Sem dados de receitas.")