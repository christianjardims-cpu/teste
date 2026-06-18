import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import os
import pytz
import sqlite3
import requests
import re
import html
from datetime import datetime, date, timedelta

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÕES INICIAIS E DESIGN CORE (GEMINI X GITHUB PRESTIGE)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Gestão de Manutenção | CMPC",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Correção 2.2: Evitar o destrutivo session_state.clear() que apaga dados úteis de navegação
if "versao_layout" not in st.session_state or st.session_state.versao_layout != "16.1_github_instant_color":
    # Em vez de .clear(), reinicializamos apenas o necessário para preservar a sessão do Streamlit
    st.session_state["versao_layout"] = "16.1_github_instant_color"
    st.session_state["uploaded_file_cache"] = None

COLOR_MAP = {
    "Realizada": "#2ea44f",
    "Pendente": "#f85149",
    "Necessita Reprogramação": "#db6d28",
    "Outros": "#8b949e"
}

HEX_BG_MAP = {
    "Realizada": "rgba(46, 164, 79, 0.08)",
    "Pendente": "rgba(248, 81, 73, 0.08)",
    "Necessita Reprogramação": "rgba(219, 109, 40, 0.08)",
    "Outros": "rgba(139, 148, 158, 0.08)"
}

# Mapeamento estático e limpo dos dias da semana
DIAS_MAPEAMENTO = {
    "Monday": "Segunda-feira",
    "Tuesday": "Terça-feira",
    "Wednesday": "Quarta-feira",
    "Thursday": "Quinta-feira",
    "Friday": "Sexta-feira",
    "Saturday": "Sábado",
    "Sunday": "Domingo"
}

# -----------------------------------------------------------------------------
# 2. FUNÇÕES DE BANCO DE DADOS E CONEXÕES EXTERNAS (CORREÇÕES DE SEGURANÇA)
# -----------------------------------------------------------------------------

# Correção 1.2: Gerenciamento seguro de conexões SQLite usando 'with'
def executar_query_segura(db_path, query, params=()):
    """Executa queries de forma segura fechando a conexão automaticamente."""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Erro no banco de dados: {e}")
        return []

# Correção 1.1: Adicionado Timeout seguro para requisições HTTP externos
def buscar_dados_api_segura(url):
    """Busca dados de API externa garantindo que a aplicação não trave se cair."""
    try:
        response = requests.get(url, timeout=10) # Timeout de 10s para segurança absoluta
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.Timeout:
        st.warning("O servidor de integração externa demorou muito para responder. Usando dados locais.")
        return None
    except requests.exceptions.RequestException as e:
        # Silencioso ou log amigável
        return None

# -----------------------------------------------------------------------------
# 3. PROCESSAMENTO DE DADOS (CORREÇÕES DE PERFORMANCE E MÉTODOS DE PARSING)
# -----------------------------------------------------------------------------

# Correção 2.3: Inferência de disciplina robusta (Case-insensitive)
def inferir_disciplina(centro_trabalho):
    """Verifica e infere a disciplina de manutenção de forma segura e padronizada."""
    if pd.isna(centro_trabalho):
        return "Mecânica"
    
    texto_limpo = str(centro_trabalho).strip().upper()
    
    # Prioriza Elétrica se conter 'E' e Instrumentação se conter 'I' de forma isolada e inteligente
    if "E" in texto_limpo and "I" not in texto_limpo:
        return "Elétrica"
    elif "I" in texto_limpo:
        return "Instrumentação"
    elif "E" in texto_limpo:
        return "Elétrica"
    
    return "Mecânica"

# Correção 3.1: Utilização de cache do Streamlit para otimização de performance
@st.cache_data(show_spinner="Processando base de dados de manutenção...")
def carregar_e_processar_dados(file_bytes, is_csv=False):
    """Carrega o arquivo e faz todo o tratamento inicial pesado em cache."""
    if is_csv:
        df = pd.read_csv(file_bytes, encoding="utf-8")
    else:
        df = pd.read_excel(file_bytes)
    
    df_temp = df.copy()
    
    # Padronização de colunas obrigatórias
    colunas_obrigatorias = {
        "Ordem": "ordem",
        "Texto breve": "descricao",
        "Status do usuário": "status_usuario",
        "Início programado": "data_inicio",
        "Fim programado": "data_fim",
        "Centro de trabalho de operação": "Centro de Trabalho Op."
    }
    
    # Renomeação dinâmica baseada na existência
    for col_orig, col_dest in colunas_obrigatorias.items():
        # Busca aproximada caso existam pequenas variações no nome da coluna
        col_encontrada = [c for c in df_temp.columns if str(c).strip().lower() == col_orig.lower()]
        if col_encontrada:
            df_temp.rename(columns={col_encontrada[0]: col_dest}, inplace=True)
            
    # Criar colunas padrão caso faltem
    if "ordem" not in df_temp.columns:
        df_temp["ordem"] = range(1, len(df_temp) + 1)
    if "descricao" not in df_temp.columns:
        df_temp["descricao"] = "Sem Descrição"
    if "status_usuario" not in df_temp.columns:
        df_temp["status_usuario"] = "Pendente"
        
    # Inferência da Disciplina
    if "Centro de Trabalho Op." in df_temp.columns:
        df_temp["disciplina"] = df_temp["Centro de Trabalho Op."].apply(inferir_disciplina)
    else:
        df_temp["disciplina"] = "Mecânica"
        
    # Correção 2.1: Parsing de datas robusto definindo explicitamente dayfirst=True
    if "data_inicio" in df_temp.columns:
        df_temp["data_parsed"] = pd.to_datetime(df_temp["data_inicio"], dayfirst=True, errors="coerce")
    else:
        df_temp["data_parsed"] = pd.NaT
        df_temp["data_inicio"] = None
        
    # Mapeamento do dia da semana em português direto
    df_temp["dia_semana_num"] = df_temp["data_parsed"].dt.weekday # Segunda=0, Domingo=6
    df_temp["dia_nome"] = df_temp["data_parsed"].dt.day_name()
    
    # Classificação simplificada do status
    def classificar_status(status_str):
        status_str = str(status_str).upper()
        if "EXEC" in status_str or "CONC" in status_str or "REAL" in status_str:
            return "Realizada"
        elif "REPR" in status_str or "ADIA" in status_str:
            return "Necessita Reprogramação"
        return "Pendente"
        
    df_temp["status_simplificado"] = df_temp["status_usuario"].apply(classificar_status)
    
    return df_temp

# -----------------------------------------------------------------------------
# 4. COMPONENTES VISUAIS E INTERFACE COM SEGURANÇA DE DESIGN
# -----------------------------------------------------------------------------

# Correção 3.2: Renderizador de cartões HTML com sanitização de campos de texto
def render_cards_operacionais(df_cards, key_prefix):
    """Renderiza a lista de atividades em formato de cards elegantes e seguros."""
    if df_cards.empty:
        st.info("Nenhuma atividade encontrada para esta seleção.")
        return

    for idx, row in df_cards.iterrows():
        status = row.get("status_simplificado", "Pendente")
        cor_borda = COLOR_MAP.get(status, "#8b949e")
        cor_fundo = HEX_BG_MAP.get(status, "rgba(139, 148, 158, 0.08)")
        
        # Correção 3.2: Escapamento de caracteres especiais usando html.escape
        ordem_segura = html.escape(str(row.get("ordem", "S/N")))
        desc_segura = html.escape(str(row.get("descricao", "Sem descrição")))
        ct_seguro = html.escape(str(row.get("Centro de Trabalho Op.", "Não definido")))
        status_original = html.escape(str(row.get("status_usuario", "Pendente")))
        
        card_html = f"""
        <div style='
            border-left: 5px solid {cor_borda}; 
            background-color: {cor_fundo}; 
            padding: 12px 16px; 
            border-radius: 6px; 
            margin-bottom: 12px; 
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        '>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <strong style='font-size: 1.1em; color: #f0f6fc;'>Ordem: {ordem_segura}</strong>
                <span style='
                    background-color: {cor_borda}; 
                    color: white; 
                    padding: 2px 8px; 
                    border-radius: 12px; 
                    font-size: 0.8em; 
                    font-weight: bold;
                '>{status}</span>
            </div>
            <p style='margin: 8px 0 4px 0; color: #c9d1d9; font-size: 0.95em;'>{desc_segura}</p>
            <div style='display: flex; gap: 15px; font-size: 0.8em; color: #8b949e; margin-top: 6px;'>
                <span><b>C. Trabalho:</b> {ct_seguro}</span>
                <span><b>Status Real:</b> {status_original}</span>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. EXECUÇÃO DO APLICATIVO PRINCIPAL
# -----------------------------------------------------------------------------
def main():
    # Header Premium CMPC
    st.markdown("""
        <div style='background-color: #0d1117; padding: 20px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 25px;'>
            <h1 style='color: #58a6ff; margin: 0; font-size: 2.2em;'>Painel de Manutenção CMPC</h1>
            <p style='color: #8b949e; margin: 5px 0 0 0;'>Indicadores operacionais, programação por disciplina e acompanhamento diário.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Upload do arquivo na sidebar
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/b/b0/Logo_CMPC.svg", width=120)
    st.sidebar.markdown("### Base de Dados")
    uploaded_file = st.sidebar.file_uploader("Selecione o arquivo de manutenção (Excel ou CSV)", type=["xlsx", "xls", "csv"])
    
    if uploaded_file is not None:
        file_name = uploaded_file.name
        is_csv = file_name.endswith('.csv')
        
        # Processa utilizando o cache inteligente
        df_dados = carregar_e_processar_dados(uploaded_file.getvalue(), is_csv=is_csv)
        
        # Filtros Globais na Sidebar
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Filtros Rápidos")
        
        lista_disciplinas = sorted(df_dados["disciplina"].unique().tolist())
        disc_selecionadas = st.sidebar.multiselect("Disciplinas", lista_disciplinas, default=lista_disciplinas)
        
        lista_status = sorted(df_dados["status_simplificado"].unique().tolist())
        status_selecionados = st.sidebar.multiselect("Status", lista_status, default=lista_status)
        
        # Filtragem reativa rápida (em memória)
        df_filtrado = df_dados[
            (df_dados["disciplina"].isin(disc_selecionadas)) & 
            (df_dados["status_simplificado"].isin(status_selecionados))
        ].copy()
        
        # KPIs Principais
        col1, col2, col3, col4 = st.columns(4)
        total_ordens = len(df_filtrado)
        concluidas = len(df_filtrado[df_filtrado["status_simplificado"] == "Realizada"])
        pendentes = len(df_filtrado[df_filtrado["status_simplificado"] == "Pendente"])
        reprogramar = len(df_filtrado[df_filtrado["status_simplificado"] == "Necessita Reprogramação"])
        
        taxa_adesao = (concluidas / total_ordens * 100) if total_ordens > 0 else 0
        
        with col1:
            st.metric("Total de Ordens", f"{total_ordens}")
        with col2:
            st.metric("Taxa de Conclusão", f"{taxa_adesao:.1f}%")
        with col3:
            st.metric("Pendentes", f"{pendentes}")
        with col4:
            st.metric("Necessitam Ajuste", f"{reprogramar}")
            
        # Abas de Navegação
        tab1, tab2 = st.tabs(["📊 Visão Geral e Indicadores", "📅 Programação Diária"])
        
        with tab1:
            st.markdown("### Distribuição de Atividades")
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                # Gráfico de Rosca de Status
                fig_status = px.pie(
                    df_filtrado, 
                    names="status_simplificado", 
                    title="Status Geral das Ordens",
                    hole=0.4,
                    color="status_simplificado",
                    color_discrete_map=COLOR_MAP
                )
                fig_status.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e6edf3")
                st.plotly_chart(fig_status, use_container_width=True)
                
            with col_chart2:
                # Distribuição por Disciplina
                fig_disc = px.histogram(
                    df_filtrado,
                    x="disciplina",
                    color="status_simplificado",
                    barmode="group",
                    title="Atividades por Disciplina",
                    color_discrete_map=COLOR_MAP
                )
                fig_disc.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e6edf3")
                st.plotly_chart(fig_disc, use_container_width=True)
                
        with tab2:
            st.markdown("### Programação Semanal por Disciplina")
            
            # Filtro exclusivo de disciplina para a programação diária
            disc_sel = st.selectbox("Escolha uma Disciplina para Visualizar Cronograma:", lista_disciplinas)
            
            if disc_sel:
                df_disc = df_filtrado[df_filtrado["disciplina"] == disc_sel].copy()
                
                # Definir dia de hoje para expansão automática inteligente
                hoje_num = datetime.now().weekday()
                dias_semana_lista = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
                hoje_nome_pt = dias_semana_lista[hoje_num]
                
                if df_disc.empty or df_disc["data_parsed"].isna().all():
                    st.warning(f"Sem datas programadas para a disciplina {disc_sel} ou dados filtrados vazios.")
                    render_cards_operacionais(df_disc, "vazio")
                else:
                    # Renderiza os expanders de dias úteis dinamicamente baseados nas atividades
                    for eng_day, pt_day in DIAS_MAPEAMENTO.items():
                        df_dia_disc = df_disc[df_disc["dia_nome"] == eng_day].copy()
                        if not df_dia_disc.empty:
                            qtd_unicas_disc = df_dia_disc["ordem"].nunique()
                            # Se o dia iterado for igual a hoje, expande automaticamente
                            expandir_se_hoje = (pt_day == hoje_nome_pt)
                            
                            with st.expander(f"📅 {pt_day} — {disc_sel} ({qtd_unicas_disc} Atividades)", expanded=expandir_se_hoje):
                                render_cards_operacionais(df_dia_disc, f"disc_crd_{disc_sel}_{eng_day}")
                                
    else:
        # Tela de Boas-vindas caso não haja arquivo
        st.markdown("""
        <div style='border: 1px dashed #30363d; border-radius: 6px; padding: 40px; text-align: center; background-color: #161b22;'>
            <h3 style='color: #c9d1d9; margin-top: 0;'>Aguardando carregamento de dados</h3>
            <p style='color: #8b949e; max-width: 500px; margin: 10px auto;'>
                Por favor, faça o upload de um arquivo CSV ou Excel exportado do SAP ou do seu sistema de gestão de manutenção na barra lateral esquerda para iniciar a análise.
            </p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()