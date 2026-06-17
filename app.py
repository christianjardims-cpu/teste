import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import os
import pytz
import sqlite3
import requests
import re
from datetime import datetime, date, timedelta

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÕES INICIAIS E DESIGN CORE (GEMINI X GITHUB)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Gestão de Manutenção | CMPC",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Reset de estado para garantir aplicação limpa do design fluido
if "versao_layout" not in st.session_state or st.session_state.versao_layout != "14.0_github_dark_animated":
    st.session_state.clear()  
    st.session_state.versao_layout = "14.0_github_dark_animated"

COLOR_MAP = {
    "Realizada": "#2ea44f",
    "Pendente": "#f85149",
    "Necessita Reprogramação": "#db6d28",
    "Outros": "#8b949e"
}

HEX_BG_MAP = {
    "Realizada": "rgba(46, 164, 79, 0.1)",
    "Pendente": "rgba(248, 81, 73, 0.1)",
    "Necessita Reprogramação": "rgba(219, 109, 40, 0.1)",
    "Outros": "rgba(139, 148, 158, 0.1)"
}

DISCIPLINA_CORES = {
    "Mecânica": "#1f6feb",
    "Elétrica": "#bc8cff",
    "Instrumentação": "#347d39"
}

# -----------------------------------------------------------------------------
# ARCHITECTURE VISUAL & ANIMATIONS FRAMEWORK (CSS HIGH-FIDELITY GITHUB ANIMATED)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Configuração Global - GitHub Dark Ecosystem */
    html, body, [class*="st-emotion-cache"] { 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
        background-color: #0d1117 !important; 
        color: #c9d1d9 !important;
    }
    h1, h2, h3, h4 { 
        font-weight: 600;
        color: #f0f6fc;
        letter-spacing: -0.02em;
    }
    
    /* Linha Superior Fluida */
    .stApp::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #1f6feb, #8957e5, #2ea44f, #d29922);
        z-index: 9999;
    }

    /* Sidebar Customizada */
    [data-testid="stSidebar"] { 
        background-color: #161b22 !important;
        border-right: 1px solid #30363d !important; 
        padding: 24px 16px !important;
    }

    /* KEYFRAMES PARA ANIMAÇÕES */
    @keyframes fadeInSlide {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulseProgressBar {
        0% { opacity: 0.9; }
        50% { opacity: 1; box-shadow: 0 0 8px rgba(31, 111, 235, 0.6); }
        100% { opacity: 0.9; }
    }

    /* CARD DE CLIMA DA SEMANA - GitHub Moderno com Animações */
    .gemini-weather-container {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 16px;
        animation: fadeInSlide 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .gemini-weather-container:hover {
        border-color: #58a6ff;
        box-shadow: 0 4px 20px rgba(56, 139, 253, 0.12);
        transform: translateY(-2px);
    }
    .gemini-weather-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 4px;
        border-bottom: 1px solid #21262d;
        transition: background-color 0.2s ease;
    }
    .gemini-weather-row:hover {
        background-color: rgba(240, 246, 252, 0.03);
        border-radius: 4px;
    }
    .gemini-weather-row:last-child { border-bottom: none; }
    .gemini-day-text { color: #8b949e; font-size: 0.88rem; }
    .gemini-day-active { color: #58a6ff; font-weight: 600; font-size: 0.88rem; }
    .gemini-badge-today { 
        font-size: 0.7rem; background: rgba(88, 166, 255, 0.15); color: #58a6ff;
        padding: 2px 8px; border-radius: 2em; font-weight: 600; margin-left: 8px;
        border: 1px solid rgba(56, 139, 253, 0.4);
    }
    .gemini-temp-text { font-weight: 600; color: #f0f6fc; font-size: 0.88rem; font-family: 'JetBrains Mono', monospace; }

    /* WIDGET DE HORÁRIO E JORNADA - Mantendo estrutura com Visual Modernizado e Animado */
    .ios-clock-widget { 
        background: #161b22;
        border: 1px solid #30363d; 
        border-radius: 8px; 
        padding: 16px; 
        display: flex; 
        flex-direction: column; 
        gap: 10px;
        animation: fadeInSlide 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .ios-clock-widget:hover { 
        border-color: #58a6ff; 
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
        transform: translateY(-2px);
    }
    .ios-clock-top { display: flex; justify-content: space-between; align-items: center; }
    .ios-time { font-size: 1.75rem; font-weight: 700; color: #58a6ff; font-family: 'JetBrains Mono', monospace; }
    .ios-date-badge { background: #21262d; color: #c9d1d9; font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 6px; border: 1px solid #30363d; }
    .ios-progress-label { font-size: 0.7rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
    .ios-progress-container { background: #21262d; border-radius: 10px; height: 6px; width: 100%; overflow: hidden; border: 1px solid #30363d; }
    .ios-progress-bar { 
        background: linear-gradient(90deg, #1f6feb, #2ea44f); 
        height: 100%; 
        border-radius: 10px;
        animation: pulseProgressBar 3s infinite ease-in-out;
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1); 
    }
    
    /* CARDS OPERACIONAIS */
    .os-card { 
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px; 
        padding: 18px; 
        margin-bottom: 12px;
        transition: all 0.2s ease;
    }
    .os-card:hover { 
        border-color: #8b949e;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
    }
    .badge-disciplina { 
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem; font-weight: 600; padding: 3px 8px; border-radius: 2em; text-transform: uppercase; margin-left: 8px; color: #FFF; 
    }
    code { font-family: 'JetBrains Mono', monospace; color: #ff7b72; background: #21262d; padding: 2px 6px; border-radius: 4px; font-size: 0.85rem; border: 1px solid #30363d; }

    /* Framework de KPIs */
    .kpi-container { display: flex; gap: 1rem; margin-bottom: 1.5rem; margin-top: 1rem; flex-wrap: wrap; }
    .kpi-card { 
        background: #161b22; 
        border: 1px solid #30363d; 
        border-radius: 6px;
        padding: 1.2rem; 
        flex: 1; 
        min-width: 220px;
        text-align: left;
        transition: all 0.2s ease;
    }
    .kpi-card:hover { border-color: #58a6ff; }
    .kpi-value { font-size: 2.2rem; font-weight: 700; color: #f0f6fc; font-family: 'JetBrains Mono', monospace; margin-bottom: 4px; }
    .kpi-label { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }

    /* Inputs Estilo GitHub */
    .stTextInput input, .stSelectbox select {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        border-radius: 6px !important;
        color: #c9d1d9 !important;
        transition: all 0.2s ease !important;
    }
    
    /* Abas de Navegação */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; background-color: transparent; border-bottom: 1px solid #30363d; }
    .stTabs [data-baseweb="tab"] { 
        background-color: transparent !important; 
        color: #8b949e !important; 
        border: 1px solid transparent !important;
        border-radius: 6px 6px 0 0 !important;
        padding: 10px 18px !important;
        font-size: 0.9rem !important;
    }
    .stTabs [aria-selected="true"] { 
        color: #f0f6fc !important; 
        background-color: #0d1117 !important; 
        border-color: #30363d #30363d #0d1117 !important; 
        font-weight: 600 !important;
    }

    .corporate-signature { text-align: right; }
    .corp-title { font-size: 1.2rem; font-weight: 700; color: #f0f6fc; letter-spacing: 1px; margin: 0; }
    .corp-author { font-size: 0.72rem; color: #8b949e; margin-top: 2px; font-family: 'JetBrains Mono', monospace; }
</style>
""", unsafe_allow_html=True)

DB_NOME = "data_cmpc.db"

# -----------------------------------------------------------------------------
# 2. SISTEMA DE BANCO DE DADOS (SQLITE)
# -----------------------------------------------------------------------------
def inicializar_banco():
    with sqlite3.connect(DB_NOME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS programacao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ordem TEXT, area TEXT, descricao TEXT, operacao TEXT, 
                executante TEXT, data_inicio TEXT, tempo_execucao TEXT, 
                disciplina TEXT, status_execucao TEXT, comentario TEXT
            )
        """)
        conn.commit()

inicializar_banco()

def carregar_dados_db():
    with sqlite3.connect(DB_NOME) as conn:
        return pd.read_sql_query("SELECT * FROM programacao", conn)

def salvar_ou_atualizar_registro_db(id_registro, novo_status, novo_comentario, ordem_nome=""):
    with sqlite3.connect(DB_NOME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE programacao SET status_execucao = ?, comentario = ? WHERE id = ?",
            (novo_status, str(novo_comentario), id_registro)
        )
        conn.commit()
    st.session_state.recriar_cache = True
    st.toast(f"OMS {ordem_nome} sincronizada localmente.", icon="🔄")

def atualizar_banco_completo(df_novo):
    with sqlite3.connect(DB_NOME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM programacao")
        for _, row in df_novo.iterrows():
            cursor.execute("""
                INSERT INTO programacao (ordem, area, descricao, operacao, executante, data_inicio, tempo_execucao, disciplina, status_execucao, comentario)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row.get("Ordem", "")), str(row.get("Área", "")), str(row.get("Descrição da Ordem", "")),
                str(row.get("Texto Breve da Operação", "")), str(row.get("Executante", "")), str(row.get("Data de Início", "")),
                str(row.get("Tempo de Execução", "4h")), str(row.get("Disciplina", "Mecânica")),
                str(row.get("Status_Execucao", "Pendente")), str(row.get("Comentario", ""))
            ))
        conn.commit()

# -----------------------------------------------------------------------------
# 3. TELEMETRIA METEOROLÓGICA REAL-TIME (OPEN-METEO)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def obter_dados_meteorologicos_puros_v11():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=-30.1139&longitude=-51.3250&daily=weathercode,temperature_2m_max,temperature_2m_min&current_weather=true&timezone=America/Sao_Paulo"
        res = requests.get(url, timeout=5).json()
        wmo_codes = {0: "☀️ Limpo", 1: "⛅ Parcial", 2: "⛅ Parcial", 3: "☁️ Encoberto", 61: "🌧️ Chuva", 63: "🌧️ Chuva", 71: "❄️ Neve", 95: "⚡ Tempestade"}
        current = res.get("current_weather", {})
        daily = res.get("daily", {})
        temp_atual = f"{int(current.get('temperature', 14))}°C"
        status_atual = wmo_codes.get(current.get("weathercode"), "☁️ Encoberto")
        
        cronograma = []
        dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        for i in range(min(7, len(daily.get("time", [])))):
            data_dt = datetime.strptime(daily["time"][i], "%Y-%m-%d")
            cronograma.append({
                "nome": dias_semana[data_dt.weekday()],
                "status": wmo_codes.get(daily["weathercode"][i], "☁️ Encoberto"),
                "temp": f"{int(daily['temperature_2m_max'][i])}°C"
            })
        return temp_atual, status_atual, cronograma
    except Exception:
        cronograma_fallback = [
            {"nome": "Segunda", "status": "☁️ Encoberto", "temp": "14°C"},
            {"nome": "Terça", "status": "⛅ Parcial", "temp": "15°C"},
            {"nome": "Quarta", "status": "☁️ Encoberto", "temp": "16°C"},
            {"nome": "Quinta", "status": "☁️ Encoberto", "temp": "18°C"},
            {"nome": "Sexta", "status": "⛅ Parcial", "temp": "14°C"},
            {"nome": "Sábado", "status": "☀️ Limpo", "temp": "17°C"},
            {"nome": "Domingo", "status": "☁️ Encoberto", "temp": "13°C"}
        ]
        return "14°C", "☁️ Encoberto", cronograma_fallback

temp_real, status_real, dados_clima = obter_dados_meteorologicos_puros_v11()

# -----------------------------------------------------------------------------
# 4. CONFIGURAÇÕES INTERNAS DE DATA E JORNADA
# -----------------------------------------------------------------------------
if "db_data" not in st.session_state or st.session_state.get("recriar_cache", False):
    st.session_state.db_data = carregar_dados_db()
    st.session_state.recriar_cache = False

tz_br = pytz.timezone("America/Sao_Paulo")
now_br = datetime.now(tz_br)
hoje_nome_pt = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][now_br.weekday()]

# Sincronização padrão ISO 8601 %V
semana_ano = now_br.strftime("%V")

hora_inicio_trabalho = 8
hora_fim_trabalho = 17
minutos_totais_trabalho = (hora_fim_trabalho - hora_inicio_trabalho) * 60
minutos_atuais_jornada = (now_br.hour * 60 + now_br.minute) - (hora_inicio_trabalho * 60)
pct_jornada = min(100.0, max(0.0, (minutos_atuais_jornada / minutos_totais_trabalho) * 100))

dias_mapeamento = {
    "Monday": "Segunda-feira", "Tuesday": "Terça-feira", "Wednesday": "Quarta-feira",
    "Thursday": "Quinta-feira", "Friday": "Sexta-feira", "Saturday": "Sábado", "Sunday": "Domingo"
}

def extrair_horas(string_tempo):
    try:
        match = re.search(r"[-+]?\d*\.\d+|\d+", str(string_tempo))
        return float(match.group()) if match else 4.0
    except Exception:
        return 4.0

# -----------------------------------------------------------------------------
# 5. SIDEBAR: FLUID DESIGN (CLIMA SEMANAL MODERNIZADO E ANIMADO)
# -----------------------------------------------------------------------------
with st.sidebar:
    opcoes_extensao = ["logo_cmpc.png", "logo_cmpc.jpeg", "logo_cmpc.jpg", "logo_cmpc.svg.png", "Logo-cmpc.svg.png"]
    imagem_encontrada = None
    for opt in opcoes_extensao:
        caminho_teste = os.path.join(os.path.dirname(__file__), opt) if "__file__" in locals() else opt
        if os.path.exists(caminho_teste):
            imagem_encontrada = caminho_teste
            break

    if imagem_encontrada:
        st.image(imagem_encontrada, use_container_width=True)
    else:
        st.markdown("<h2 style='font-size:1.4rem; font-weight:600; margin-bottom:2px;'>🏭 CMPC Guaíba</h2>", unsafe_allow_html=True)
        
    st.markdown("<div style='margin: 14px 0; border-bottom: 1px solid #30363d;'></div>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.7rem; color:#8b949e; font-weight:600; letter-spacing:0.8px; text-transform:uppercase; margin-bottom:12px;'>Telemetria Climática Semanal</p>", unsafe_allow_html=True)
    
    # Renderização da lista climática com animações via CSS injetado
    st.markdown("<div class='gemini-weather-container'>", unsafe_allow_html=True)
    for index, info in enumerate(dados_clima):
        is_hoje = info["nome"] == hoje_nome_pt
        label_dia = f"<span class='gemini-day-active'>{info['nome']}</span><span class='gemini-badge-today'>Hoje</span>" if is_hoje else f"<span class='gemini-day-text'>{info['nome']}</span>"
        icon = info["status"].split(" ")[0]
        
        # Inserção de um pequeno delay incremental para efeito cascata elegante
        st.markdown(f"""
            <div class='gemini-weather-row' style='animation: fadeInSlide 0.4s ease both {index * 0.05}s;'>
                <div style='display:flex; align-items:center;'>{label_dia}</div>
                <div style='display:flex; align-items:center; gap:10px;'>
                    <span style='font-size:1rem;'>{icon}</span>
                    <span class='gemini-temp-text'>{info['temp']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
                
    st.write("")

    with st.expander("🔐 Chave Operacional", expanded=False):
        senha_inserida = st.text_input("Chave:", type="password", placeholder="Insira o token...", label_visibility="collapsed", key="v12_pass_key")
    
    if senha_inserida == "Programacao@2026":
        if "uploader_key" not in st.session_state: st.session_state.uploader_key = 9000
        uploaded_file = st.file_uploader("Atualizar Base:", type=["csv", "xlsx"], key=f"uploader_v12_{st.session_state.uploader_key}")
        
        if uploaded_file is not None:
            nome_arq = uploaded_file.name.lower()
            try:
                with st.spinner("Sincronizando Banco de Dados..."):
                    df_temp = pd.read_csv(uploaded_file, skiprows=1) if nome_arq.endswith(".csv") else pd.read_excel(uploaded_file, skiprows=1)
                    df_temp.columns = df_temp.columns.str.strip()
                    if "Centro de Trabalho Op." in df_temp.columns:
                        df_temp["Disciplina"] = df_temp["Centro de Trabalho Op."].astype(str).apply(
                            lambda x: "Elétrica" if "E" in x else ("Instrumentação" if "I" in x else "Mecânica")
                        )
                    else: df_temp["Disciplina"] = "Mecânica"
                    if "Status_Execucao" not in df_temp.columns: df_temp["Status_Execucao"] = "Pendente"
                    if "Comentario" not in df_temp.columns: df_temp["Comentario"] = ""
                    atualizar_banco_completo(df_temp)
                    st.session_state.db_data = carregar_dados_db()
                    st.session_state.recriar_cache = False
                st.success("Banco de dados updated com sucesso!")
                st.session_state.uploader_key += 1
                st.rerun()
            except Exception as e: st.error(f"Falha de integridade: {e}")
                
    st.markdown("<div style='margin-top:20px; font-size:0.7rem; color:#8b949e;'><center>📊 Unidade Guaíba • Utilidades</center></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. HEADER DESIGN CONTEMPORÂNEO (SISTEMA DE HORÁRIO REFINADO COM ANIMAÇÃO)
# -----------------------------------------------------------------------------
col_tit1, col_tit2, col_signature = st.columns([2.0, 1.4, 0.6])
with col_tit1:
    st.markdown("<h1 style='font-weight: 600; font-size: 2.2rem; margin-bottom: 4px; font-family: \"SF Pro Display\",sans-serif;'>⚙️ Painel de Acompanhamento</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8b949e; margin: 0; font-size: 1rem;'>Manutenção Integrada • Setor de Caldeira de Recuperação e Energia</p>", unsafe_allow_html=True)
with col_tit2:
    # Widget original mantido na íntegra, otimizado estruturalmente com animações de hover e pulsação na barra
    st.markdown(f"""
        <div class='ios-clock-widget'>
            <div class='ios-clock-top'>
                <span class='ios-time'>{now_br.strftime('%H:%M')}</span>
                <span class='ios-date-badge'>{hoje_nome_pt} • Semana {semana_ano}</span>
            </div>
            <div class='ios-progress-label'>⏱️ Progresso da Jornada Ativa</div>
            <div class='ios-progress-container'>
                <div class='ios-progress-bar' style='width: {pct_jornada}%;'></div>
            </div>
            <div class='ios-weather-row' style='display:flex; justify-content:space-between; font-size:0.78rem; margin-top:2px;'>
                <span style='color:#8b949e;'>📍 Guaíba - RS</span>
                <span style='color:#58a6ff; font-weight:600;'>{status_real.split(' ')[0]} {temp_real}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
with col_signature:
    st.markdown("""
        <div class='corporate-signature'>
            <p class='corp-title'>CMPC</p>
            <p class='corp-author'>Design Dev<br>Christian Jardim</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin: 18px 0; border-bottom: 1px solid #30363d;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 7. FILTROS E RENDERIZAÇÃO FLUIDA DOS CARDS OPERACIONAIS
# -----------------------------------------------------------------------------
def tratar_mudanca_status(id_reg, prefixo, ordem_nome):
    status_escolhido = st.session_state.get(f"st_{prefixo}_{id_reg}")
    if status_escolhido in ["Pendente", "Necessita Reprogramação"]:
        motivo = st.session_state.get(f"mot_{prefixo}_{id_reg}", "Selecione motivo...")
        detalhe = st.session_state.get(f"det_{prefixo}_{id_reg}", "")
        comentario_final = f"{motivo}: {detalhe}" if motivo != "Selecione motivo..." else ""
    else:
        comentario_final = ""
    salvar_ou_atualizar_registro_db(id_reg, status_escolhido, comentario_final, ordem_nome)

def render_cards_operacionais(sub_df, unique_prefix):
    sub_df = sub_df.drop_duplicates(subset=["ordem"], keep="first")

    col_search, col_format = st.columns([3, 1])
    with col_search:
        busca = st.text_input("Filtrar ordens ou descrições:", "", placeholder="🔍 Digite o número da OMS ou termos chaves...", key=f"src_v12_{unique_prefix}", label_visibility="collapsed")
    with col_format:
        modo_exibicao = st.segmented_control("Visualização", options=["Cards", "Lista"], default="Cards", key=f"v_v12_{unique_prefix}", label_visibility="collapsed")
    
    if busca:
        sub_df = sub_df[sub_df["ordem"].astype(str).str.contains(busca, case=False) |
                        sub_df["descricao"].astype(str).str.contains(busca, case=False)]
    if sub_df.empty:
        st.markdown("<p style='font-size:0.9rem; color:#8b949e; padding:10px;'>Nenhuma ordem de trabalho encontrada para os filtros antigos.</p>", unsafe_allow_html=True)
        return

    st.markdown("<br>", unsafe_allow_html=True)

    for _, row in sub_df.iterrows():
        id_reg, ordem, desc, operacao, status_atual, cor_disc = row["id"], row["ordem"], row["descricao"], row["operacao"], row["status_execucao"], DISCIPLINA_CORES.get(row["disciplina"], "#8b949e")
        comentario_atual = "" if str(row["comentario"]) in ["nan", "None", ""] else str(row["comentario"])
        
        bg_card = HEX_BG_MAP.get(status_atual, "rgba(22, 27, 34, 0.5)")
        border_left_color = COLOR_MAP.get(status_atual, "#30363d")
        
        if modo_exibicao == "Cards":
            st.markdown(f"""
                <div class='os-card' style='background: {bg_card}; border-left: 4px solid {border_left_color};'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <span><strong>OMS:</strong> <code>{ordem}</code> <span class='badge-disciplina' style='background:{cor_disc};'>{row['disciplina']}</span></span>
                        <span style='font-size:0.8rem; color:#8b949e; font-family: "JetBrains Mono", monospace;'>⏱️ Carga: {row['tempo_execucao']}</span>
                    </div>
                    <p style='margin:12px 0 8px 0; font-size:0.95rem; font-weight:600; color:#f0f6fc;'>{desc}</p>
                    <div style='font-size:0.78rem; color:#8b949e; display:flex; gap:12px;'>
                        <span><b>🛠️ Op:</b> {operacao[:60]}...</span>
                        <span><b>👤 Executante:</b> <span style='color: #c9d1d9;'>{row['executante']}</span></span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"📌 <b>OMS {ordem}</b> - <span style='color:{cor_disc}; font-weight:600;'>{row['disciplina']}</span> | <span style='color:#f0f6fc;'>{desc[:90]}...</span>", unsafe_allow_html=True)

        col_rad, col_input = st.columns([1.6, 2.4])
        with col_rad:
            st.segmented_control(
                "Status", options=["Pendente", "Realizada", "Necessita Reprogramação"], default=status_atual, 
                key=f"st_{unique_prefix}_{id_reg}", label_visibility="collapsed",
                on_change=tratar_mudanca_status, args=(id_reg, unique_prefix, ordem)
            )
        with col_input:
            status_em_tempo_real = st.session_state.get(f"st_{unique_prefix}_{id_reg}", status_atual)
            if status_em_tempo_real in ["Pendente", "Necessita Reprogramação"]:
                motivos = ["Falta de Material", "Falta de Acesso", "Mão de Obra", "Não liberado pela operação", "Condição climática não favorável", "Outros"]
                col_sel, col_det = st.columns([1.3, 2.7])
                motivo_inicial, detalhe_inicial = "Selecione motivo...", ""
                
                if ":" in comentario_atual:
                    partes = comentario_atual.split(":", 1)
                    if partes[0] in motifs:
                        motivo_inicial, detalhe_inicial = partes[0], partes[1].strip()
                elif comentario_atual in motivos: 
                    motivo_inicial = comentario_atual

                with col_sel:
                    st.selectbox(
                        "Justificativa", ["Selecione motivo..."] + motivos, index=(["Selecione motivo..."] + motivos).index(motivo_inicial),
                        key=f"mot_{unique_prefix}_{id_reg}", label_visibility="collapsed", on_change=tratar_mudanca_status, args=(id_reg, unique_prefix, ordem)
                    )
                with col_det:
                    st.text_input(
                        "Detalhes", value=detalhe_inicial, placeholder="Observações complementares...", 
                        key=f"det_{unique_prefix}_{id_reg}", label_visibility="collapsed", on_change=tratar_mudanca_status, args=(id_reg, unique_prefix, ordem)
                    )
        st.markdown("<div style='margin: 12px 0; border-bottom: 1px solid #21262d;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 8. SISTEMA DE ABAS EM ALTA DENSIDADE (ESTILO GITHUB INSIGHTS)
# -----------------------------------------------------------------------------
if st.session_state.db_data is not None and not st.session_state.db_data.empty:
    df_geral = st.session_state.db_data
    
    lista_areas_disponiveis = sorted(list(df_geral["area"].str.strip().dropna().unique()))
    
    aba_geral, aba_exec, aba_disc = st.tabs(["📊 Métricas Macro", "🛠️ Visão por Executante", "⚙️ Linha por Disciplina"])
    
    with aba_geral:
        area_sel_geral = st.selectbox("Selecione a Área de Foco:", lista_areas_disponiveis, key="area_macro_v12")
        df_foco = df_geral[df_geral["area"].str.strip() == area_sel_geral].copy()
        
        df_foco_unicas = df_foco.drop_duplicates(subset=["ordem"])
        total_os = len(df_foco_unicas)
        realizadas = len(df_foco_unicas[df_foco_unicas["status_execucao"] == "Realizada"])
        aderencia = (realizadas / total_os * 100) if total_os > 0 else 0.0
        
        st.markdown(f"""
            <div class='kpi-container'>
                <div class='kpi-card'><div class='kpi-value'>{total_os}</div><div class='kpi-label'>Ordens Totais Alvo</div></div>
                <div class='kpi-card'><div class='kpi-value' style='color:#2ea44f'>{aderencia:.1f}%</div><div class='kpi-label'>Aderência Programada</div></div>
                <div class='kpi-card'><div class='kpi-value' style='color:#f85149'>{total_os - realizadas}</div><div class='kpi-label'>Ordens Backlog / Abertas</div></div>
            </div>
        """, unsafe_allow_html=True)
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("<p style='font-size:0.85rem; color:#8b949e; text-transform:uppercase; font-weight:600; letter-spacing:0.5px;'>Distribuição por Status de Operação</p>", unsafe_allow_html=True)
            if not df_foco_unicas.empty:
                st_counts = df_foco_unicas["status_execucao"].value_counts().reset_index()
                fig1 = px.pie(st_counts, values="count", names="status_execucao", hole=0.6, color="status_execucao", color_discrete_map=COLOR_MAP)
                fig1.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10,b=10,l=10,r=10), showlegend=True)
                st.plotly_chart(fig1, use_container_width=True)
        with col_g2:
            st.markdown("<p style='font-size:0.85rem; color:#8b949e; text-transform:uppercase; font-weight:600; letter-spacing:0.5px;'>Atividades por Disciplina Ativa</p>", unsafe_allow_html=True)
            if not df_foco_unicas.empty:
                disc_counts = df_foco_unicas["disciplina"].value_counts().reset_index()
                fig2 = px.pie(disc_counts, values="count", names="disciplina", hole=0.6, color="disciplina", color_discrete_map=DISCIPLINA_CORES)
                fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10,b=10,l=10,r=10), showlegend=True)
                st.plotly_chart(fig2, use_container_width=True)

        st.markdown("<div style='margin: 15px 0; border-bottom: 1px solid #30363d;'></div>", unsafe_allow_html=True)
        
        st.markdown("<p style='font-size:0.85rem; color:#8b949e; text-transform:uppercase; font-weight:600; letter-spacing:0.5px;'>Análise de Entrega Concluída (%)</p>", unsafe_allow_html=True)
        if not df_foco_unicas.empty:
            lista_discs_existentes = sorted(list(df_foco_unicas["disciplina"].dropna().unique()))
            disc_alvo = st.selectbox("Selecione a Especialidade Tática:", lista_discs_existentes, key="seletor_reativo_v12")
            
            df_selecionada = df_foco_unicas[df_foco_unicas["disciplina"] == disc_alvo]
            total_atividades = len(df_selecionada)
            concluidas_atividades = len(df_selecionada[df_selecionada["status_execucao"] == "Realizada"])
            
            pct_concluida = (concluidas_atividades / total_atividades * 100) if total_atividades > 0 else 0.0
            pct_restante = 100.0 - pct_concluida
            
            fig_barras_horizontal = go.Figure()
            fig_barras_horizontal.add_trace(go.Bar(
                y=[disc_alvo], x=[pct_concluida], name="Realizada", orientation='h',
                marker=dict(color=DISCIPLINA_CORES.get(disc_alvo, "#2ea44f")),
                text=[f"Concluída: {pct_concluida:.1f}% ({concluidas_atividades} OMS)"], textposition='inside'
            ))
            fig_barras_horizontal.add_trace(go.Bar(
                y=[disc_alvo], x=[pct_restante], name="Backlog", orientation='h',
                marker=dict(color="#21262d"),
                text=[f"Pendente: {pct_restante:.1f}%"], textposition='inside'
            ))
            
            fig_barras_horizontal.update_layout(
                barmode='stack', template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(range=[0, 100], gridcolor='#21262d', title="Percentual Concluído"),
                margin=dict(t=5, b=5, l=5, r=5), height=100, showlegend=False
            )
            st.plotly_chart(fig_barras_horizontal, use_container_width=True, key="graph_v12_bar")

    with aba_exec:
        st.markdown("<h3 style='font-size:1.2rem; font-weight:500; margin-bottom:12px;'>Alocação Técnica por Executante</h3>", unsafe_allow_html=True)
        
        area_sel_exec = st.selectbox("Filtrar Visão por Área:", lista_areas_disponiveis, key="area_exec_v12")
        df_foco = df_geral[df_geral["area"].str.strip() == area_sel_exec].copy()
        
        lista_executantes = ["Selecione o profissional..."] + sorted(list(df_foco["executante"].dropna().unique()))
        exec_sel = st.selectbox("Filtrar por técnico de campo:", lista_executantes, key="c_exec_v12", label_visibility="collapsed")
        
        if exec_sel != "Selecione o profissional...":
            df_exec = df_foco[df_foco["executante"] == exec_sel].copy()
            st.markdown("<br>", unsafe_allow_html=True)
            col_pie1, col_pie2 = st.columns(2)
            with col_pie1:
                st.markdown(f"<p style='font-size:0.8rem; color:#8b949e; text-transform:uppercase;'>Aderência Individual - {exec_sel}</p>", unsafe_allow_html=True)
                st_exec_counts = df_exec.drop_duplicates(subset=["ordem"])["status_execucao"].value_counts().reset_index()
                f_pie_exec = px.pie(st_exec_counts, values="count", names="status_execucao", hole=0.55, color="status_execucao", color_discrete_map=COLOR_MAP)
                f_pie_exec.update_layout(template="plotly_dark", height=200, paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10,b=10,l=10,r=10))
                st.plotly_chart(f_pie_exec, use_container_width=True)
            with col_pie2:
                st.markdown("<p style='font-size:0.8rem; color:#8b949e; text-transform:uppercase;'>Balanço de Carga Horária Alocada</p>", unsafe_allow_html=True)
                df_exec_unique = df_exec.drop_duplicates(subset=["ordem"]).copy()
                df_exec_unique["horas_num"] = df_exec_unique["tempo_execucao"].apply(extrair_horas)
                total_horas_alocadas = df_exec_unique["horas_num"].sum()
                horas_utilizadas = df_exec_unique[df_exec_unique["status_execucao"] == "Realizada"]["horas_num"].sum()
                horas_restantes = max(0.0, total_horas_alocadas - horas_utilizadas)
                
                df_horas_chart = pd.DataFrame([{"Métrica": "Horas Executadas", "Valor": horas_utilizadas}, {"Métrica": "Horas Pendentes", "Valor": horas_restantes}])
                f_pie_horas = px.pie(df_horas_chart, values="Valor", names="Métrica", hole=0.55, color="Métrica", color_discrete_map={"Horas Executadas": "#2ea44f", "Horas Pendentes": "#21262d"})
                f_pie_horas.update_layout(template="plotly_dark", height=200, paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10,b=10,l=10,r=10))
                st.plotly_chart(f_pie_horas, use_container_width=True)
            
            st.markdown("<div style='margin: 15px 0; border-bottom: 1px solid #30363d;'></div>", unsafe_allow_html=True)
            df_exec["data_parsed"] = pd.to_datetime(df_exec["data_inicio"], errors="coerce")
            df_exec["dia_nome"] = df_exec["data_parsed"].dt.day_name()
            
            if df_exec["data_parsed"].isna().all():
                render_cards_operacionais(df_exec, f"ex_lst_{exec_sel}")
            else:
                for eng_day, pt_day in dias_mapeamento.items():
                    df_dia_especifico = df_exec[df_exec["dia_nome"] == eng_day].copy()
                    if not df_dia_especifico.empty:
                        qtd_unicas = df_dia_especifico["ordem"].nunique()
                        with st.expander(f"➔ {pt_day} ({qtd_unicas} Ordens Vinculadas)", expanded=True):
                            render_cards_operacionais(df_dia_especifico, f"ex_crd_{exec_sel}_{eng_day}")

    with aba_disc:
        st.markdown("<h3 style='font-size:1.2rem; font-weight:500; margin-bottom:12px;'>Cronograma Técnico Semanal</h3>", unsafe_allow_html=True)
        
        area_sel_disc = st.selectbox("Filtrar Linha por Área:", lista_areas_disponiveis, key="area_disc_v12")
        df_foco = df_geral[df_geral["area"].str.strip() == area_sel_disc].copy()
        
        disc_sel = st.selectbox("Selecione a especialidade técnica:", sorted(list(df_foco["disciplina"].dropna().unique())), key="c_disc_page_v12")
        
        if disc_sel:
            df_disc = df_foco[df_foco["disciplina"] == disc_sel].copy()
            df_disc["data_parsed"] = pd.to_datetime(df_disc["data_inicio"], errors="coerce")
            df_disc["dia_nome"] = df_disc["data_parsed"].dt.day_name()
            st.markdown("<br>", unsafe_allow_html=True)
            
            if df_disc["data_parsed"].isna().all():
                st.warning("Ordens sem formatação de data estruturada.")
                render_cards_operacionais(df_disc, f"disc_full_list_{disc_sel}")
            else:
                for eng_day, pt_day in dias_mapeamento.items():
                    df_dia_disc = df_disc[df_disc["dia_nome"] == eng_day].copy()
                    if not df_dia_disc.empty:
                        qtd_unicas_disc = df_dia_disc["ordem"].nunique()
                        expandir_se_hoje = (pt_day.split("-")[0] == hoje_nome_pt)
                        with st.expander(f"📅 {pt_day} — {disc_sel} ({qtd_unicas_disc} Atividades)", expanded=expandir_se_hoje):
                            render_cards_operacionais(df_dia_disc, f"disc_crd_v12_{disc_sel}_{eng_day}")
else:
    st.markdown("""
    <div style='border: 1px dashed #30363d; border-radius: 6px; padding: 24px; text-align: center; margin-top: 20px;'>
        <p style='color: #8b949e; margin-bottom: 0;'>Nenhuma programação activa localizada no banco local.</p>
        <small style='color: #58a6ff;'>Insira a Chave Operacional no menu lateral para fazer o upload do cronograma.</small>
    </div>
    """, unsafe_allow_html=True)