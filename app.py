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
# 1. CONFIGURAÇÕES INICIAIS E DESIGN CORE (GEMINI X GITHUB PRESTIGE)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Gestão de Manutenção | CMPC",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "versao_layout" not in st.session_state or st.session_state.versao_layout != "16.2_github_optimized":
    st.session_state.clear()  
    st.session_state.versao_layout = "16.2_github_optimized"

COLOR_MAP = {
    "Realizada": "#2ea44f",
    "Pendente": "#f85149",
    "Necessita Reprogramação": "#db6d28",
    "Outros": "#8b949e"
}

HEX_BG_MAP = {
    "Realizada": "rgba(46, 164, 79, 0.05)",
    "Pendente": "rgba(248, 81, 73, 0.05)",
    "Necessita Reprogramação": "rgba(219, 109, 40, 0.05)",
    "Outros": "rgba(139, 148, 158, 0.05)"
}

DISCIPLINA_CORES = {
    "Mecânica": "#1f6feb",
    "Elétrica": "#bc8cff",
    "Instrumentação": "#347d39",
    "Outros": "#8b949e"
}

# -----------------------------------------------------------------------------
# ARCHITECTURE VISUAL & ANIMATIONS FRAMEWORK (CSS ULTRA-COMPACT GITHUB)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
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
    
    .stApp::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #1f6feb, #8957e5, #2ea44f, #d29922);
        z-index: 9999;
    }

    [data-testid="stSidebar"] { 
        background-color: #161b22 !important;
        border-right: 1px solid #30363d !important; 
        padding: 16px 12px !important;
    }

    @keyframes fadeInSlide {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .gemini-weather-container {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 10px;
        margin-bottom: 12px;
        animation: fadeInSlide 0.4s ease both;
    }
    .gemini-weather-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 4px;
        border-bottom: 1px solid #21262d;
    }
    .gemini-weather-row-today {
        border-left: 3px solid #58a6ff !important;
        background-color: rgba(56, 139, 253, 0.05);
        padding-left: 6px;
    }
    .gemini-weather-row:last-child { border-bottom: none; }
    .gemini-day-text { color: #8b949e; font-size: 0.82rem; }
    .gemini-day-active { color: #58a6ff; font-weight: 600; font-size: 0.82rem; }
    .gemini-badge-today { 
        font-size: 0.65rem;
        background: rgba(88, 166, 255, 0.15); color: #58a6ff;
        padding: 1px 6px; border-radius: 2em; font-weight: 600; margin-left: 6px;
        border: 1px solid rgba(56, 139, 253, 0.4);
    }
    .gemini-temp-text { font-weight: 600; color: #f0f6fc; font-size: 0.82rem; font-family: 'JetBrains Mono', monospace; }

    .ios-clock-widget { 
        background: #161b22;
        border: 1px solid #30363d; 
        border-radius: 6px; 
        padding: 12px; 
        display: flex; 
        flex-direction: column; 
        gap: 6px;
    }
    .ios-time { font-size: 1.5rem; font-weight: 700; color: #58a6ff; font-family: 'JetBrains Mono', monospace; }
    .ios-date-badge { background: #21262d; color: #c9d1d9; font-size: 0.72rem; font-weight: 600; padding: 2px 8px; border-radius: 4px; border: 1px solid #30363d; }
    .ios-progress-label { font-size: 0.65rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
    .ios-progress-container { background: #21262d; border-radius: 4px; height: 5px; width: 100%; overflow: hidden; border: 1px solid #30363d; }
    .ios-progress-bar { background: linear-gradient(90deg, #1f6feb, #2ea44f); height: 100%; border-radius: 4px; }
    
    /* CARDS ULTRA OTIMIZADOS - ESPAÇO COMPACTO */
    .os-card { 
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px; 
        padding: 10px 14px; 
        margin-bottom: 6px;
        transition: all 0.15s ease-in-out;
    }
    .os-card:hover { 
        border-color: #8b949e;
        background-color: #1f242c !important;
    }
    .badge-disciplina { 
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        font-weight: 600; padding: 1px 6px; border-radius: 4px; text-transform: uppercase; margin-left: 6px; color: #FFF;
    }
    code { font-family: 'JetBrains Mono', monospace; color: #ff7b72; background: #21262d; padding: 1px 4px; border-radius: 4px; font-size: 0.8rem; border: 1px solid #30363d; }

    /* GRID DE METADADOS COMPACTOS DENTRO DO CARD */
    .card-meta-inline {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 6px;
        font-size: 0.75rem;
        color: #8b949e;
        border-top: 1px solid rgba(48, 54, 61, 0.5);
        padding-top: 6px;
    }
    .meta-inline-item {
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .kpi-container { display: flex; gap: 0.75rem; margin-bottom: 1rem; margin-top: 0.5rem; flex-wrap: wrap; }
    .kpi-card { 
        background: #161b22;
        border: 1px solid #30363d; 
        border-radius: 6px;
        padding: 0.8rem 1rem; 
        flex: 1; 
        min-width: 200px;
        transition: all 0.2s ease;
    }
    .kpi-value { font-size: 1.8rem; font-weight: 700; color: #f0f6fc; font-family: 'JetBrains Mono', monospace; margin-bottom: 2px; }
    .kpi-label { font-size: 0.7rem; color: #8b949e; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }

    .stTextInput input, .stSelectbox select, .stSelectbox div[data-baseweb="select"] {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        border-radius: 4px !important;
        color: #c9d1d9 !important;
        height: 28px !important;
    }
</style>
""", unsafe_allow_html=True)

DB_NOME = "data_cmpc.db"

# -----------------------------------------------------------------------------
# 2. BANCO DE DADOS E NORMALIZAÇÃO DE TEXTO/DISCIPLINA
# -----------------------------------------------------------------------------
def normalizar_disciplina(texto):
    txt = str(texto).upper().strip()
    if "ELÉTRICA" in txt or "ELET" in txt or "-E" in txt:
        return "Elétrica"
    elif "INSTRUMENTAÇÃO" in txt or "INST" in txt or "-I" in txt:
        return "Instrumentação"
    elif "MECÂNICA" in txt or "MEC" in txt or "-M" in txt:
        return "Mecânica"
    return "Mecânica" # Fallback padrão unificado para evitar o erro de sumiço

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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_filtros_operacionais ON programacao (area, disciplina, executante)")
        conn.commit()

inicializar_banco()

def carregar_dados_db():
    with sqlite3.connect(DB_NOME) as conn:
        df = pd.read_sql_query("SELECT * FROM programacao", conn)
        if not df.empty:
            df["area"] = df["area"].astype(str).str.strip()
            df["disciplina"] = df["disciplina"].astype(str).str.strip().apply(normalizar_disciplina)
        return df

def salvar_ou_atualizar_registro_db(id_registro, novo_status, novo_comentario, ordem_nome=""):
    with sqlite3.connect(DB_NOME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE programacao SET status_execucao = ?, comentario = ? WHERE id = ?",
            (novo_status, str(novo_comentario), id_registro)
        )
        conn.commit()
    st.session_state.recriar_cache = True

def atualizar_banco_completo(df_novo):
    with sqlite3.connect(DB_NOME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM programacao")
        for _, row in df_novo.iterrows():
            # Extração limpa eliminando tags HTML residuais das planilhas
            def limpar_html(val):
                return re.sub(r'<[^>]*>', '', str(val)).strip()

            area_limpa = limpar_html(row.get("Área", row.get("area", "Instalação Geral")))
            ct_trabalho = str(row.get("Centro de Trabalho Op.", row.get("disciplina", "")))
            disciplina_final = normalizar_disciplina(ct_trabalho)

            cursor.execute("""
                INSERT INTO programacao (ordem, area, descricao, operacao, executante, data_inicio, tempo_execucao, disciplina, status_execucao, comentario)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                limpar_html(row.get("Ordem", "")),
                area_limpa,
                limpar_html(row.get("Descrição da Ordem", row.get("descricao", ""))),
                limpar_html(row.get("Texto Breve da Operação", row.get("operacao", ""))),
                limpar_html(row.get("Executante", "Não Atribuído")),
                limpar_html(row.get("Data de Início", "")),
                limpar_html(row.get("Tempo de Execução", "4h")),
                disciplina_final,
                limpar_html(row.get("Status_Execucao", "Pendente")),
                limpar_html(row.get("Comentario", ""))
            ))
        conn.commit()

# -----------------------------------------------------------------------------
# 3. TELEMETRIA E CONFIGURAÇÕES DE JORNADA
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def obter_dados_meteorologicos_puros_v11():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=-30.1139&longitude=-51.3250&daily=weathercode,temperature_2m_max,temperature_2m_min&current_weather=true&timezone=America/Sao_Paulo"
        res = requests.get(url, timeout=5).json()
        wmo_codes = {0: "☀️ Limpo", 1: "⛅ Parcial", 2: "⛅ Parcial", 3: "☁️ Encoberto", 61: "🌧️ Chuva", 63: "🌧️ Chuva", 71: "❄️ Neve", 95: "⚡ Tempestade"}
        current = res.get("current_weather", {})
        daily = res.get("daily", {})
        return f"{int(current.get('temperature', 14))}°C", wmo_codes.get(current.get("weathercode"), "☁️ Encoberto"), [
            {"nome": ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][datetime.strptime(d, "%Y-%m-%d").weekday()],
             "status": wmo_codes.get(daily["weathercode"][i], "☁️ Encoberto"), "temp": f"{int(daily['temperature_2m_max'][i])}°C"}
            for i, d in enumerate(daily.get("time", []))
        ]
    except Exception:
        return "14°C", "☁️ Encoberto", [{"nome": d, "status": "⛅ Parcial", "temp": "16°C"} for d in ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]]

temp_real, status_real, dados_clima = obter_dados_meteorologicos_puros_v11()

if "db_data" not in st.session_state or st.session_state.get("recriar_cache", False):
    st.session_state.db_data = carregar_dados_db()
    st.session_state.recriar_cache = False

tz_br = pytz.timezone("America/Sao_Paulo")
now_br = datetime.now(tz_br)
hoje_nome_pt = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][now_br.weekday()]
semana_ano = now_br.strftime("%V")

minutos_totais = (17 - 8) * 60
minutos_atuais = (now_br.hour * 60 + now_br.minute) - (8 * 60)
pct_jornada = min(100.0, max(0.0, (minutos_atuais / minutos_totais) * 100))
dias_mapeamento = {"Monday": "Segunda-feira", "Tuesday": "Terça-feira", "Wednesday": "Quarta-feira", "Thursday": "Quinta-feira", "Friday": "Sexta-feira", "Saturday": "Sábado", "Sunday": "Domingo"}

def extrair_horas(string_tempo):
    match = re.search(r"[-+]?\d*\.\d+|\d+", str(string_tempo))
    return float(match.group()) if match else 4.0

# -----------------------------------------------------------------------------
# 4. SIDEBAR DESIGN
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='font-size:1.3rem; font-weight:600; margin-bottom:2px;'>🏭 CMPC Guaíba</h2>", unsafe_allow_html=True)
    st.markdown("<div style='margin: 8px 0; border-bottom: 1px solid #30363d;'></div>", unsafe_allow_html=True)
    
    st.markdown("<div class='gemini-weather-container'>", unsafe_allow_html=True)
    for index, info in enumerate(dados_clima[:5]):
        is_hoje = info["nome"] == hoje_nome_pt
        row_class = "gemini-weather-row gemini-weather-row-today" if is_hoje else "gemini-weather-row"
        label_dia = f"<span class='gemini-day-active'>{info['nome']}</span><span class='gemini-badge-today'>Hoje</span>" if is_hoje else f"<span class='gemini-day-text'>{info['nome']}</span>"
        st.markdown(f"<div class='{row_class}'><div>{label_dia}</div><div style='display:flex; gap:6px;'><span style='font-size:0.9rem;'>{info['status'].split(' ')[0]}</span><span class='gemini-temp-text'>{info['temp']}</span></div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    with st.expander("🔐 Chave Operacional", expanded=False):
        senha_inserida = st.text_input("Chave:", type="password", placeholder="Insira o token...", label_visibility="collapsed")
    if senha_inserida == "Programacao@2026":
        uploaded_file = st.file_uploader("Atualizar Base:", type=["csv", "xlsx"])
        if uploaded_file is not None:
            try:
                df_temp = pd.read_csv(uploaded_file, skiprows=1) if uploaded_file.name.lower().endswith(".csv") else pd.read_excel(uploaded_file, skiprows=1)
                df_temp.columns = df_temp.columns.str.strip()
                atualizar_banco_completo(df_temp)
                st.session_state.db_data = carregar_dados_db()
                st.success("Banco de dados atualizado!")
                st.rerun()
            except Exception as e: st.error(f"Erro: {e}")

# -----------------------------------------------------------------------------
# 5. HEADER DESIGN CONTEMPORÂNEO
# -----------------------------------------------------------------------------
col_tit1, col_tit2, col_signature = st.columns([2.0, 1.4, 0.6])
with col_tit1:
    st.markdown("<h1 style='font-size: 2rem; margin-bottom: 2px;'>⚙️ Painel de Acompanhamento</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8b949e; margin: 0; font-size: 0.9rem;'>Manutenção Integrada • Setor de Caldeira de Recuperação e Energia</p>", unsafe_allow_html=True)
with col_tit2:
    st.markdown(f"""
        <div class='ios-clock-widget'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <span class='ios-time'>{now_br.strftime('%H:%M')}</span>
                <span class='ios-date-badge'>{hoje_nome_pt} • Sem {semana_ano}</span>
            </div>
            <div class='ios-progress-container'><div class='ios-progress-bar' style='width: {pct_jornada}%;'></div></div>
        </div>
    """, unsafe_allow_html=True)
with col_signature:
    st.markdown("<div style='text-align: right;'><p style='font-size: 1rem; font-weight:700; color:#f0f6fc; margin:0;'>CMPC</p><p style='font-size: 0.65rem; color: #8b949e; margin:0;'>Christian Jardim</p></div>", unsafe_allow_html=True)

st.markdown("<div style='margin: 12px 0; border-bottom: 1px solid #30363d;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. RENDERIZADOR DE CARDS OPERACIONAIS COMPACTOS (SEM ERROS DE TAGS HTML EXPOSTAS)
# -----------------------------------------------------------------------------
def tratar_mudanca_status(id_reg, prefixo, ordem_nome):
    status_escolhido = st.session_state.get(f"st_{prefixo}_{id_reg}")
    comentario_final = f"{st.session_state.get(f'mot_{prefixo}_{id_reg}', '')}: {st.session_state.get(f'det_{prefixo}_{id_reg}', '')}" if status_escolhido in ["Pendente", "Necessita Reprogramação"] else ""
    salvar_ou_atualizar_registro_db(id_reg, status_escolhido, comentario_final, ordem_nome)

@st.fragment
def render_cards_operacionais(sub_df, unique_prefix):
    sub_df = sub_df.drop_duplicates(subset=["ordem"], keep="first")
    busca = st.text_input("Filtrar ordens ou descrições:", "", placeholder="🔍 Digite termos chaves...", key=f"src_{unique_prefix}", label_visibility="collapsed")
    
    if busca:
        sub_df = sub_df[sub_df["ordem"].astype(str).str.contains(busca, case=False) | sub_df["descricao"].astype(str).str.contains(busca, case=False)]
    if sub_df.empty:
        st.markdown("<p style='font-size:0.85rem; color:#8b949e;'>Nenhuma ordem localizada.</p>", unsafe_allow_html=True)
        return

    for _, row in sub_df.iterrows():
        id_reg, ordem, desc, operacao, status_base = row["id"], row["ordem"], row["descricao"], row["operacao"], row["status_execucao"]
        cor_disc = DISCIPLINA_CORES.get(row["disciplina"], "#8b949e")
        chave_widget = f"st_{unique_prefix}_{id_reg}"
        status_atual = st.session_state.get(chave_widget, status_base)
        
        # Limpeza absoluta de qualquer tag HTML residual vinda dos dados brutos
        desc_clean = re.sub(r'<[^>]*>', '', str(desc))
        op_clean = re.sub(r'<[^>]*>', '', str(operacao))
        area_clean = re.sub(r'<[^>]*>', '', str(row['area']))
        exec_clean = re.sub(r'<[^>]*>', '', str(row['executante']))

        bg_card = HEX_BG_MAP.get(status_atual, "rgba(22, 27, 34, 0.5)")
        border_left_color = COLOR_MAP.get(status_atual, "#30363d")
        
        # CARD ULTRA-COMPACTADO EM LINHA (OTIMIZAÇÃO DE ESPAÇO MÁXIMO)
        st.markdown(f"""
            <div class='os-card' style='background: {bg_card}; border-left: 4px solid {border_left_color};'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <span><strong>OMS:</strong> <code>{ordem}</code> <span class='badge-disciplina' style='background:{cor_disc};'>{row['disciplina']}</span></span>
                    <span style='font-size:0.75rem; color:#8b949e; font-family:monospace;'>⏱️ {row['tempo_execucao']}</span>
                </div>
                <p style='margin: 4px 0; font-size: 0.88rem; font-weight:600; color:#f0f6fc;'>{desc_clean}</p>
                <div style='font-size:0.78rem; color:#8b949e; margin-bottom: 2px;'><b>🛠️ Op:</b> {op_clean[:80]}...</div>
                <div class='card-meta-inline'>
                    <div class='meta-inline-item'>🏭 <b>Área:</b> {area_clean}</div>
                    <div class='meta-inline-item'>👤 <b>Executor:</b> {exec_clean}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        col_rad, col_input = st.columns([1.5, 2.5])
        with col_rad:
            st.segmented_control("Status", options=["Pendente", "Realizada", "Necessita Reprogramação"], default=status_atual, key=chave_widget, label_visibility="collapsed", on_change=tratar_mudanca_status, args=(id_reg, unique_prefix, ordem))
        with col_input:
            if status_atual in ["Pendente", "Necessita Reprogramação"]:
                motivos = ["Falta de Material", "Falta de Acesso", "Mão de Obra", "Não liberado pela operação", "Condição climática", "Outros"]
                col_sel, col_det = st.columns([1.3, 2.7])
                with col_sel: st.selectbox("Motivo", motivos, key=f"mot_{unique_prefix}_{id_reg}", label_visibility="collapsed", on_change=tratar_mudanca_status, args=(id_reg, unique_prefix, ordem))
                with col_det: st.text_input("Obs", placeholder="Detalhes...", key=f"det_{unique_prefix}_{id_reg}", label_visibility="collapsed", on_change=tratar_mudanca_status, args=(id_reg, unique_prefix, ordem))
        st.markdown("<div style='margin: 6px 0; border-bottom: 1px solid #21262d;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 7. HIGH-DENSITY TABS (ABAS REORGANIZADAS)
# -----------------------------------------------------------------------------
if st.session_state.db_data is not None and not st.session_state.db_data.empty:
    df_geral = st.session_state.db_data
    lista_areas_disponiveis = sorted(list(df_geral["area"].dropna().unique()))
    
    aba_fabrica, aba_geral, aba_exec, aba_disc = st.tabs([
        "🏭 Visão Geral da Fábrica", "📊 Métricas Macro por Área", "🛠️ Visão por Executante", "⚙️ Linha por Disciplina"
    ])
    
    # -------------------------------------------------------------------------
    # CORREÇÃO 1: VISÃO GERAL DA FÁBRICA (SEM CARDS - APENAS GRÁFICOS E DADOS ESTATÍSTICOS EXTRA)
    # -------------------------------------------------------------------------
    with aba_fabrica:
        st.markdown("<h3 style='font-size:1.1rem; font-weight:500;'>Métricas Consolidadas de Toda a Fábrica</h3>", unsafe_allow_html=True)
        df_fabrica_unicas = df_geral.drop_duplicates(subset=["ordem"])
        total_os_fabrica = len(df_fabrica_unicas)
        realizadas_fabrica = len(df_fabrica_unicas[df_fabrica_unicas["status_execucao"] == "Realizada"])
        aderencia_fabrica = (realizadas_fabrica / total_os_fabrica * 100) if total_os_fabrica > 0 else 0.0
        
        st.markdown(f"""
            <div class='kpi-container'>
                <div class='kpi-card'><div class='kpi-value'>{total_os_fabrica}</div><div class='kpi-label'>Total de Ordens Fábrica</div></div>
                <div class='kpi-card'><div class='kpi-value' style='color:#2ea44f'>{aderencia_fabrica:.1f}%</div><div class='kpi-label'>Aderência Global</div></div>
                <div class='kpi-card'><div class='kpi-value' style='color:#f85149'>{total_os_fabrica - realizadas_fabrica}</div><div class='kpi-label'>Backlog Total Unidade</div></div>
            </div>
        """, unsafe_allow_html=True)
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.markdown("<p style='font-size:0.8rem; color:#8b949e; text-transform:uppercase; font-weight:600;'>Distribuição Macroscópica de Status</p>", unsafe_allow_html=True)
            fig_f1 = px.pie(df_fabrica_unicas["status_execucao"].value_counts().reset_index(), values="count", names="status_execucao", hole=0.55, color="status_execucao", color_discrete_map=COLOR_MAP)
            fig_f1.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10,b=10,l=10,r=10), height=240)
            st.plotly_chart(fig_f1, use_container_width=True)
            
        with col_f2:
            st.markdown("<p style='font-size:0.8rem; color:#8b949e; text-transform:uppercase; font-weight:600;'>Volume Quantitativo de Ordens por Área Industrial</p>", unsafe_allow_html=True)
            area_counts = df_fabrica_unicas["area"].value_counts().reset_index()
            fig_f2 = px.bar(area_counts, x="area", y="count", text_auto=True, color="area", color_discrete_sequence=px.colors.qualitative.G10)
            fig_f2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10,b=10,l=10,r=10), height=240, showlegend=False, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_f2, use_container_width=True)

        # Adicionando Mais Dados Estatísticos Consolidados em Tabela Minimalista (Substituindo os antigos cards da Aba Fábrica)
        st.markdown("<p style='font-size:0.8rem; color:#8b949e; text-transform:uppercase; font-weight:600; margin-top:10px;'>Detalhamento Estatístico Operacional</p>", unsafe_allow_html=True)
        resumo_estatistico = df_fabrica_unicas.groupby("area").agg(
            Total_Ordens=("ordem", "count"),
            Concluidas=("status_execucao", lambda x: (x == "Realizada").sum()),
            Pendentes=("status_execucao", lambda x: (x == "Pendente").sum())
        ).reset_index()
        resumo_estatistico["Aderência"] = (resumo_estatistico["Concluidas"] / resumo_estatistico["Total_Ordens"] * 100).map("{:.1f}%".format)
        st.dataframe(resumo_estatistico, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # CORREÇÃO 2: MÉTRICAS MACRO POR ÁREA (MAPEAMENTO INTEGRAL DE DISCIPLINAS)
    # -------------------------------------------------------------------------
    with aba_geral:
        area_sel_geral = st.selectbox("Selecione a Área de Foco:", lista_areas_disponiveis, key="area_macro_v12")
        df_foco = df_geral[df_geral["area"] == area_sel_geral].copy()
        df_foco_unicas = df_foco.drop_duplicates(subset=["ordem"])
        
        total_os = len(df_foco_unicas)
        realizadas = len(df_foco_unicas[df_foco_unicas["status_execucao"] == "Realizada"])
        aderencia = (realizadas / total_os * 100) if total_os > 0 else 0.0
        
        st.markdown(f"""
            <div class='kpi-container'>
                <div class='kpi-card'><div class='kpi-value'>{total_os}</div><div class='kpi-label'>Ordens da Área Alvo</div></div>
                <div class='kpi-card'><div class='kpi-value' style='color:#2ea44f'>{aderencia:.1f}%</div><div class='kpi-label'>Aderência Programada</div></div>
                <div class='kpi-card'><div class='kpi-value' style='color:#f85149'>{total_os - realizadas}</div><div class='kpi-label'>Ordens Abertas / Backlog</div></div>
            </div>
        """, unsafe_allow_html=True)
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("<p style='font-size:0.8rem; color:#8b949e; text-transform:uppercase; font-weight:600;'>Distribuição por Status da Área</p>", unsafe_allow_html=True)
            fig1 = px.pie(df_foco_unicas["status_execucao"].value_counts().reset_index(), values="count", names="status_execucao", hole=0.55, color="status_execucao", color_discrete_map=COLOR_MAP)
            fig1.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10,b=10,l=10,r=10), height=220)
            st.plotly_chart(fig1, use_container_width=True)
            
        with col_g2:
            st.markdown("<p style='font-size:0.8rem; color:#8b949e; text-transform:uppercase; font-weight:600;'>Atividades por Disciplina Cadastrada (Mapeamento Abrangente)</p>", unsafe_allow_html=True)
            # Garantindo a contagem correta com as disciplinas normalizadas
            disc_counts = df_foco_unicas["disciplina"].value_counts().reset_index()
            fig2 = px.pie(disc_counts, values="count", names="disciplina", hole=0.55, color="disciplina", color_discrete_map=DISCIPLINA_CORES)
            fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10,b=10,l=10,r=10), height=220)
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("<div style='margin: 10px 0; border-bottom: 1px solid #30363d;'></div>", unsafe_allow_html=True)
        
        # Correção da Seleção das Especialidades (Listando Corretamente as Disciplinas Reais Encontradas)
        lista_discs_existentes = sorted(list(df_foco_unicas["disciplina"].unique()))
        if not lista_discs_existentes: lista_discs_existentes = ["Mecânica", "Elétrica", "Instrumentação"]
        
        disc_alvo = st.selectbox("Selecione a Disciplina:", lista_discs_existentes, key="seletor_reativo_v12")
        df_selecionada = df_foco_unicas[df_foco_unicas["disciplina"] == disc_alvo]
        
        total_atividades = len(df_selecionada)
        concluidas_atividades = len(df_selecionada[df_selecionada["status_execucao"] == "Realizada"])
        pct_concluida = (concluidas_atividades / total_atividades * 100) if total_atividades > 0 else 0.0
        pct_restante = 100.0 - pct_concluida
        
        fig_barras_horizontal = go.Figure()
        fig_barras_horizontal.add_trace(go.Bar(y=[disc_alvo], x=[pct_concluida], name="Realizada", orientation='h', marker=dict(color=DISCIPLINA_CORES.get(disc_alvo, "#2ea44f")), text=[f"Concluída: {pct_concluida:.1f}% ({concluidas_atividades} OMS)"], textposition='inside'))
        fig_barras_horizontal.add_trace(go.Bar(y=[disc_alvo], x=[pct_restante], name="Backlog", orientation='h', marker=dict(color="#21262d"), text=[f"Pendente: {pct_restante:.1f}%"], textposition='inside'))
        fig_barras_horizontal.update_layout(barmode='stack', template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(range=[0, 100], gridcolor='#21262d'), margin=dict(t=5, b=5, l=5, r=5), height=80, showlegend=False)
        st.plotly_chart(fig_barras_horizontal, use_container_width=True)

        st.markdown("<br><p style='font-size:0.8rem; color:#8b949e; text-transform:uppercase; font-weight:600;'>Ordens de Trabalho da Área</p>", unsafe_allow_html=True)
        render_cards_operacionais(df_foco, "macro_area_cards")

    # -------------------------------------------------------------------------
    # ABA ORIGINAL: VISÃO POR EXECUTANTE
    # -------------------------------------------------------------------------
    with aba_exec:
        st.markdown("<h3 style='font-size:1.1rem; font-weight:500;'>Alocação Técnica por Executante</h3>", unsafe_allow_html=True)
        area_sel_exec = st.selectbox("Filtrar Visão por Área:", lista_areas_disponiveis, key="area_exec_v12")
        df_foco = df_geral[df_geral["area"] == area_sel_exec].copy()
        
        lista_executantes = ["Selecione o profissional..."] + sorted(list(df_foco["executante"].dropna().unique()))
        exec_sel = st.selectbox("Filtrar por técnico de campo:", lista_executantes, key="c_exec_v12", label_visibility="collapsed")
        
        if exec_sel != "Selecione o profissional...":
            df_exec = df_foco[df_foco["executante"] == exec_sel].copy()
            col_pie1, col_pie2 = st.columns(2)
            with col_pie1:
                st.markdown(f"<p style='font-size:0.8rem; color:#8b949e; text-transform:uppercase;'>Aderência Individual - {exec_sel}</p>", unsafe_allow_html=True)
                f_pie_exec = px.pie(df_exec.drop_duplicates(subset=["ordem"])["status_execucao"].value_counts().reset_index(), values="count", names="status_execucao", hole=0.55, color="status_execucao", color_discrete_map=COLOR_MAP)
                f_pie_exec.update_layout(template="plotly_dark", height=180, paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=5,b=5,l=5,r=5))
                st.plotly_chart(f_pie_exec, use_container_width=True)
            with col_pie2:
                st.markdown("<p style='font-size:0.8rem; color:#8b949e; text-transform:uppercase;'>Balanço de Carga Horária Alocada</p>", unsafe_allow_html=True)
                df_exec_unique = df_exec.drop_duplicates(subset=["ordem"]).copy()
                df_exec_unique["horas_num"] = df_exec_unique["tempo_execucao"].apply(extrair_horas)
                total_horas_alocadas = df_exec_unique["horas_num"].sum()
                horas_utilizadas = df_exec_unique[df_exec_unique["status_execucao"] == "Realizada"]["horas_num"].sum()
                horas_restantes = max(0.0, total_horas_alocadas - horas_utilizadas)
                
                f_pie_horas = px.pie(pd.DataFrame([{"Métrica": "Horas Executadas", "Valor": horas_utilizadas}, {"Métrica": "Horas Pendentes", "Valor": horas_restantes}]), values="Valor", names="Métrica", hole=0.55, color="Métrica", color_discrete_map={"Horas Executadas": "#2ea44f", "Horas Pendentes": "#21262d"})
                f_pie_horas.update_layout(template="plotly_dark", height=180, paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=5,b=5,l=5,r=5))
                st.plotly_chart(f_pie_horas, use_container_width=True)
            
            st.markdown("<div style='margin: 10px 0; border-bottom: 1px solid #30363d;'></div>", unsafe_allow_html=True)
            df_exec["data_parsed"] = pd.to_datetime(df_exec["data_inicio"], errors="coerce")
            df_exec["dia_nome"] = df_exec["data_parsed"].dt.day_name()
            
            if df_exec["data_parsed"].isna().all():
                render_cards_operacionais(df_exec, f"ex_lst_{exec_sel}")
            else:
                for eng_day, pt_day in dias_mapeamento.items():
                    df_dia_specifico = df_exec[df_exec["dia_nome"] == eng_day].copy()
                    if not df_dia_specifico.empty:
                        with st.expander(f"➔ {pt_day} ({df_dia_specifico['ordem'].nunique()} Ordens)", expanded=True):
                            render_cards_operacionais(df_dia_specifico, f"ex_crd_{exec_sel}_{eng_day}")

    # -------------------------------------------------------------------------
    # CORREÇÃO 3: ABA LINHA POR DISCIPLINA (CORRIGIDO FILTRO PARA MOSTRAR MAIS QUE MECÂNICA/OUTROS)
    # -------------------------------------------------------------------------
    with aba_disc:
        st.markdown("<h3 style='font-size:1.1rem; font-weight:500;'>Cronograma Técnico Semanal por Disciplina</h3>", unsafe_allow_html=True)
        area_sel_disc = st.selectbox("Filtrar Linha por Área:", lista_areas_disponiveis, key="area_disc_v12")
        df_foco = df_geral[df_geral["area"] == area_sel_disc].copy()
        
        # Carrega dinamicamente todas as disciplinas filtradas e normalizadas daquela área
        lista_disciplinas_reais = sorted(list(df_foco["disciplina"].unique()))
        disc_sel = st.selectbox("Selecione a especialidade técnica:", lista_disciplinas_reais, key="c_disc_page_v12")
        
        if disc_sel:
            df_disc = df_foco[df_foco["disciplina"] == disc_sel].copy()
            df_disc["data_parsed"] = pd.to_datetime(df_disc["data_inicio"], errors="coerce")
            df_disc["dia_nome"] = df_disc["data_parsed"].dt.day_name()
            
            if df_disc["data_parsed"].isna().all():
                render_cards_operacionais(df_disc, f"disc_full_list_{disc_sel}")
            else:
                for eng_day, pt_day in dias_mapeamento.items():
                    df_dia_disc = df_disc[df_disc["dia_nome"] == eng_day].copy()
                    if not df_dia_disc.empty:
                        expandir_se_hoje = (pt_day.split("-")[0] == hoje_nome_pt)
                        with st.expander(f"📅 {pt_day} — {disc_sel} ({df_dia_disc['ordem'].nunique()} Atividades)", expanded=expandir_se_hoje):
                            render_cards_operacionais(df_dia_disc, f"disc_crd_v12_{disc_sel}_{eng_day}")
else:
    st.markdown("""
    <div style='border: 1px dashed #30363d; border-radius: 6px; padding: 24px; text-align: center; margin-top: 20px;'>
        <p style='color: #8b949e; margin-bottom: 0;'>Nenhuma programação ativa localizada no banco local.</p>
        <small style='color: #58a6ff;'>Insira a Chave Operacional no menu lateral para fazer o upload do cronograma.</small>
    </div>
    """, unsafe_allow_html=True)