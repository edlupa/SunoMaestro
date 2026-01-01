# app/main.py
import sys
import os
import streamlit as st

# 1. Configurar o Python Path para encontrar a pasta 'core'
# Isso permite importar 'from core.generator' mesmo rodando o arquivo da pasta 'app'
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

# 2. Imports após ajuste do Path
from core.generator import SunoMaestroCore
from app import utils, callbacks as cb
from core import logic
from app.components import hierarchical_field
from app.sections import render_structure_section, render_vibe_section, render_history_sidebar

# Configuração da Página
st.set_page_config(page_title="Suno Maestro", page_icon="🎛️", layout="wide")

# Inicialização
@st.cache_resource
def get_core_instance():
    return SunoMaestroCore() # Não precisa passar path, o config resolve

def main():
    st.markdown(f"<style>{utils.load_css()}</style>", unsafe_allow_html=True)
    cb.init_session_state()
    core = get_core_instance()
    
    placeholder_aviso = st.empty()

    # --- Header e Botões Globais ---
    st.title("🎛️ Suno Maestro")
    
    t1, t2, t3 = st.columns([1, 1, 2])
    with t1: st.button("🧹 Limpar", on_click=cb.clear_all, use_container_width=True)
    with t2: st.button("🎲 Aleatório", on_click=cb.random_all, args=(core.dados,), use_container_width=True)
    with t3:
        if st.button("🚀 Gerar Prompt", type="primary", use_container_width=True):
            # Validação simples
            if not st.session_state.genero:
                placeholder_aviso.error("Selecione pelo menos um Gênero!")
            else:
                campos = {k: st.session_state[k] for k in list(cb.STATE_DEFAULTS.keys())}
                texto = core.gerar_prompt(campos)
                st.session_state.prompt_final = texto
                st.session_state.show_prompt = True
                
                # Salvar no histórico
                st.session_state.history.insert(0, {
                    "titulo": f"{st.session_state.genero} - {st.session_state.tema}"[:30],
                    "conteudo": texto, "data": ""
                })

    # --- Exibir Prompt ---
    if st.session_state.show_prompt:
        st.divider()
        c1, c2 = st.columns([1, 0.1])
        with c1: utils.custom_copy_button(st.session_state.prompt_final)
        with c2: 
            if st.button("❌"): st.session_state.show_prompt = False; st.rerun()
        st.code(st.session_state.prompt_final, language="yaml")

    # --- Formulários ---
    col_l, col_r = st.columns(2, gap="large")
    
    with col_l:
        st.subheader("📝 Composição")
        l1, l2 = st.columns(2)
        with l1: st.text_input("💡 Tema", key="tema"); st.text_input("📩 Mensagem", key="mensagem")
        with l2: st.text_input("🔑 Tags", key="palavras_chave"); st.text_input("🌐 Idioma", key="idioma")
        
        st.subheader("🎵 Identidade")
        m1, m2 = st.columns(2)
        with m1: 
            opts = [""] + list(core.dados["hierarquia"].keys())
            st.selectbox("Gênero*", opts, key="genero", on_change=cb.on_genero_change)
        with m2:
            opts_r = [""] + logic.get_ritmos_list(st.session_state.genero, core.dados)
            st.selectbox("Ritmo", opts_r, key="ritmo", on_change=cb.on_ritmo_change, args=(core.dados,))
        
        st.text_input("Referência", key="referencia")
        render_structure_section(core.dados)
        render_vibe_section(core.dados)

    with col_r:
        hierarchical_field("🎧 Público", "publico", core.dados["publico"])
        hierarchical_field("🎤 Narrador", "narrador", core.dados["narrador"])
        hierarchical_field("📜 Tom", "tom", core.dados["tom"])
        hierarchical_field("🎨 Estética", "influencia_estetica", core.dados["influencia_estetica"])
        hierarchical_field("🎚️ Gravação", "tipo_de_gravacao", core.dados["tipo_de_gravacao"])

    render_history_sidebar()

if __name__ == "__main__":
    main()
