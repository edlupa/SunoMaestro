import streamlit as st
import sys
import os
import io
import zipfile
from datetime import datetime
from state import clear_all

# Configuração de Paths para Importação
# Adiciona o diretório pai (raiz) ao path para importar core
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from core.generator import SunoMaestroCore
from app import state, components as ui

# Configuração da Página
st.set_page_config(page_title="Suno Maestro", page_icon="🎛️", layout="wide")

# --- SINGLETONS E CACHE ---
@st.cache_data
def load_css() -> str:
    """Carrega o CSS uma única vez."""
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    with open(css_path, encoding="utf-8") as f:
        return f.read()

@st.cache_resource
def get_core_instance(root_path: str) -> SunoMaestroCore:
    """Instancia o motor do projeto uma única vez."""
    return SunoMaestroCore(base_path=root_path)

# --- FUNÇÕES UI ESPECÍFICAS DE SEÇÃO ---
def render_structure_section(core, help_text):
    st.markdown("**🎶 Estrutura**", help=help_text.get("estrutura"))
    sc1, sc3, sc4 = st.columns([0.70, 0.10, .10], gap="small", vertical_alignment="bottom")
    with sc1: 
        opts_est = [""] + state.get_all_unique_structures(core)
        curr = st.session_state.estrutura_sel
        idx_est = opts_est.index(curr) if curr in opts_est else 0
        st.selectbox("Sug. Est.", opts_est, index=idx_est, key="estrutura_sel", 
                     on_change=state.on_estrutura_sel_change, label_visibility="collapsed")
    with sc3:
        st.button("🎲", key="btn_rnd_est", use_container_width=True, on_click=state.randomize_struct_callback, args=(core,))
    with sc4:
        st.button("🧹", key="btn_clr_est", use_container_width=True, on_click=lambda: st.session_state.update({"estrutura_sel":"", "estrutura":""}))
    
    st.text_input("Editável", key="estrutura", label_visibility="collapsed", placeholder="Selecione ou monte sua estrutura...")

    # Tags de Estrutura
    metatags = core.dados.get("metatags", {})
    if metatags:
        with st.expander("🏷️ Adicionar Seções e Tags", expanded=False):
            mapa_nomes = {
                "Estrutura_Principal": "Principal",
                "Secoes_Instrumentais_e_Dinamicas": "Instrumental/Dinâmica",
                "Finalizacao_e_Transicao_Sonora": "Transições/Final"
            }
            abas = st.tabs([mapa_nomes.get(k, k) for k in metatags.keys()])
            for i, (categoria, itens) in enumerate(metatags.items()):
                with abas[i]:
                    cols = st.columns(4) 
                    for idx, item in enumerate(itens):
                        tag_nome, tag_desc = item[0], item[1]
                        with cols[idx % 4]:
                            st.button(tag_nome, key=f"tag_{categoria}_{idx}", help=tag_desc, 
                                      on_click=state.add_tag_to_structure, args=(tag_nome,), use_container_width=True)
            st.caption("💡 Clique nas tags para adicionar ao final da estrutura.")

def render_vibe_section(core, help_text):
    st.subheader("✨ Vibe Emocional", help=help_text.get("vibe_emocional"))
    dados_vibes = core.dados.get("vibe_emocional", {})
    
    if dados_vibes:
        with st.expander("🎭 Catálogo de Emoções e Vibes", expanded=False):
            if isinstance(dados_vibes, dict):
                categorias_ordenadas = sorted(dados_vibes.keys())
                abas_v = st.tabs(categorias_ordenadas)
                for i, categoria in enumerate(categorias_ordenadas):
                    with abas_v[i]:
                        itens_ordenados = sorted(dados_vibes[categoria], key=lambda x: x[0] if isinstance(x, list) else x)
                        cols_v = st.columns(4)
                        for idx, item in enumerate(itens_ordenados):
                            v_nome = item[0] if isinstance(item, list) else item
                            v_desc = item[1] if isinstance(item, list) and len(item) > 1 else ""
                            with cols_v[idx % 4]:
                                st.button(v_nome, key=f"tag_v_cat_{categoria}_{idx}", help=v_desc, 
                                          on_click=state.add_vibe_click, args=(v_nome,), use_container_width=True)
            else:
                itens_ordenados = sorted(dados_vibes, key=lambda x: x[0] if isinstance(x, list) else x)
                cols_v = st.columns(4)
                for idx, item in enumerate(itens_ordenados):
                    v_nome = item[0] if isinstance(item, list) else item
                    with cols_v[idx % 4]:
                        st.button(v_nome, key=f"tag_v_list_{idx}", on_click=state.add_vibe_click, args=(v_nome,), use_container_width=True)
            st.caption("💡 Clique para adicionar à lista de vibes.")

    cv1, cv2, cv3 = st.columns([0.70, 0.10, 0.10], gap="small", vertical_alignment="bottom")
    with cv1:
        st.text_input("Adicionar manualmente", key="new_vibe_input", placeholder="Ex: Melancólico, Eufórico...", 
                      on_change=state.submit_manual_vibe, label_visibility="collapsed")
    with cv2:
        st.button("🎲", key="btn_rnd_vibe_local", use_container_width=True, on_click=state.random_vibe_generator, args=(core,))
    with cv3:
        st.button("🧹", key="btn_clr_vibe_local", use_container_width=True, on_click=lambda: st.session_state.update({"vibe_emocional": []}))
    
    if st.session_state.vibe_emocional:
        for i, v in enumerate(st.session_state.vibe_emocional):
            c1, c2 = st.columns([0.85, 0.10], gap="small")
            with c1: st.markdown(f"**{v}**") 
            with c2:
                if st.button("❌", use_container_width=True, key=f"del_vibe_{i}"):
                    state.delete_vibe(i)
                    st.rerun()
    else:
        st.caption("Nenhuma vibe selecionada.")

def criar_zip_historico(historico):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for i, item in enumerate(historico):
            nome_arquivo = f"{len(historico)-i:02d}_{item['titulo'].replace(' ', '_').replace('|', '')}.txt"
            zip_file.writestr(nome_arquivo, item['conteudo'])
    return buffer.getvalue()

def render_history_sidebar(core):
    with st.sidebar:
        st.header("Suno Maestro")
        
        render_help_sidebar(core)
        
        st.markdown("---")
        st.header("📜 Histórico")
        st.info("Os prompts gerados nesta sessão ficam salvos abaixo.")
        
        if not st.session_state.history:
            st.write("Nenhum prompt gerado ainda.")
        
        for idx, item in enumerate(st.session_state.history):
            with st.expander(item["titulo"]):
                st.caption(f"Gerado em: {item['data']}")
                sb1, sb2 = st.columns([0.2, 0.2], gap="small", vertical_alignment="bottom")
                with sb1: st.button("🔄 Restaurar", key=f"rest_{idx}", use_container_width=True, on_click=state.callback_restaurar, args=(item["conteudo"],))
                with sb2: ui.custom_copy_button(item["conteudo"])
                st.code(item["conteudo"], language="yaml")
        
        st.markdown("---")
        
        if st.session_state.history:
            zip_data = criar_zip_historico(st.session_state.history)
            st.download_button(
                label="📦 Baixar Tudo (ZIP)", data=zip_data,
                file_name=f"prompts_suno_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                mime="application/zip", use_container_width=True
            )
            
            if st.button("🗑️ Limpar Histórico", use_container_width=True):
                st.session_state.history = []
                st.rerun()

def render_help_sidebar(core):
    """Renderiza a seção de ajuda na barra lateral lendo do JSON de listas."""
    help_data = core.dados.get("help", {})
    
    # Converte para dict apenas para facilitar o acesso às chaves do 'geral'
    geral_dict = dict(help_data.get("geral", []))
    campos_lista = help_data.get("campos", [])

    with st.sidebar.expander("❓ Guia e Dúvidas", expanded=False):
        if geral_dict:
            st.markdown(f"**{geral_dict.get('titulo', 'Ajuda')}**")
            st.caption(geral_dict.get('descricao', ''))
            
            st.markdown("---")
            st.markdown("🔴 **Campos em Branco**")
            st.info(geral_dict.get('campos_em_branco', ''))

        if campos_lista:
            st.markdown("---")
            st.markdown("📚 **Dicionário de Campos**")
            for item in campos_lista:
                # Como é uma lista de listas: item[0] é a chave, item[1] é a descrição
                nome_campo = item[0].replace('_', ' ').title()
                descricao = item[1]
                st.markdown(f"**{nome_campo}:** {descricao}")

# --- MAIN APP ---
def main():
    # Inicializações
    st.markdown(f"<style>{load_css()}</style>", unsafe_allow_html=True)
    state.init_session_state()
    core = get_core_instance(ROOT)
    placeholder_aviso = st.empty()

    raw_help = core.dados.get("help", {})
    help_geral = dict(raw_help.get("geral", []))
    help_text = dict(raw_help.get("campos", []))

    # Cabeçalho
    st.title("🎛️ Suno Maestro")
    st.markdown("Generate professional prompts for Suno AI v5.")
    st.markdown("---")

    # Controles Superiores
    t_c1, t_c2, t_c3 = st.columns([1, 1, 2], vertical_alignment="center")
    with t_c1: st.button("🧹 Limpar Tudo", on_click=state.clear_all, use_container_width=True)
    with t_c2: st.button("🎲 Aleatório", on_click=state.random_all, args=(core,), use_container_width=True)
    with t_c3:
        if st.button("🚀 Gerar Prompt", type="primary", use_container_width=True):
            # Validação
            obrigatorios = {"genero": "Gênero Musical", "idioma": "Idioma", "tema": "Tema da Música"}
            erros = [nome for campo, nome in obrigatorios.items() 
                     if not st.session_state.get(campo) or st.session_state.get(campo) == "Selecione..."]

            if erros:
                with placeholder_aviso:
                    st.toast(f"Os seguintes campos são obrigatórios: {', '.join(erros)}", icon="🚫")
            else:
                # Geração
                with st.spinner("Maestro está compondo seu prompt..."):
                    campos = {k: st.session_state[k] for k in ["genero","ritmo","estrutura","tipo_de_gravacao",
                                                               "influencia_estetica","vibe_emocional","referencia",
                                                               "idioma","tema","mensagem","palavras_chave",
                                                               "publico","narrador","tom"]}
                    texto_gerado = core.gerar_prompt(campos)
                    st.session_state.prompt_final = texto_gerado
                    st.session_state.show_prompt = True

                    # Salvar Histórico
                    agora = datetime.now()
                    gen = st.session_state.genero or "Estilo"
                    tem = st.session_state.tema or "Geral"
                    novo_item = {
                        "titulo": f"{agora.strftime('%H:%M')} | {gen} - {tem}"[:40], 
                        "conteudo": texto_gerado,
                        "data": agora.strftime("%d/%m/%Y %H:%M")
                    }
                    st.session_state.history.insert(0, novo_item)                    
                    
                    # Feedback Visual
                    with placeholder_aviso:
                        st.balloons()
                        st.toast("Pronto para uso!", icon="🎵")
                        st.markdown("""
                        <div style="background-color: #d4edda; color: #155724; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745; margin-bottom: 20px;">
                            <h3 style="margin-top: 0;">🎉 Tudo pronto!</h3>
                            <p>💡 Agora, basta enviá-lo para uma IA (como o ChatGPT) para obter a composição completa da sua música.</p>
                        </div>
                        """, unsafe_allow_html=True)

    # Exibição do Prompt Gerado
    if st.session_state.show_prompt:
        st.divider()
        ac1, ac2, ac3 = st.columns([1, 1, 1], vertical_alignment="bottom")
        with ac1: ui.custom_copy_button(st.session_state.prompt_final)
        with ac2: st.download_button("⬇️ Baixar", st.session_state.prompt_final, "prompt.txt", use_container_width=True)
        with ac3: 
            if st.button("❌ Fechar", use_container_width=True):
                state.clear_all()
                st.session_state.show_prompt = False
                st.rerun()
        st.code(st.session_state.prompt_final, language="yaml")

    # Layout Principal (Formulários)
    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        st.subheader("📝 Composição")
        lc1, lc2 = st.columns(2)
        with lc1: st.text_input("💡 Tema*", key="tema", help=help_text.get("tema")); st.text_input("📩 Mensagem", key="mensagem", help=help_text.get("mensagem"))
        with lc2: st.text_input("🔑 Tags", key="palavras_chave", help=help_text.get("palavras_chave")); st.text_input("🌐 Idioma*", key="idioma", help=help_text.get("idioma"), placeholder="Português (Brasil), Inglês (EUA), Espanhol")
        st.divider()

        st.subheader("🎵 Identidade Musical")
        mc1, mc2 = st.columns(2)
        with mc1: 
            opts_gen = [""] + list(core.dados["hierarquia"].keys())
            idx_gen = opts_gen.index(st.session_state.genero) if st.session_state.genero in opts_gen else 0
            st.selectbox("Gênero*", opts_gen, index=idx_gen, key="genero", help=help_text.get("genero"), on_change=state.on_genero_change)
        with mc2: 
            opts_rit = [""] + state.get_ritmos_list(st.session_state.genero, core)
            curr_rit = st.session_state.ritmo
            idx_rit = opts_rit.index(curr_rit) if curr_rit in opts_rit else 0
            st.selectbox("Ritmo", opts_rit, index=idx_rit, key="ritmo", help=help_text.get("ritmo"), on_change=state.on_ritmo_change, args=(core,))
        st.text_input("🎼 Referências Artísticas", key="referencia", help=help_text.get("referencia"), placeholder="Aquarela - Toquinho, Garota de Ipanema - Tom Jobim")
        st.divider()

        render_structure_section(core, help_text)
        st.divider()
        render_vibe_section(core, help_text)

    with col_right:
        ui.hierarchical_field("🎧 Público Alvo", "publico", core.dados["publico"], help_msg=help_text.get("publico"))
        st.divider()
        ui.hierarchical_field("🎤 Narrador", "narrador", core.dados["narrador"], help_msg=help_text.get("narrador"))
        st.divider()
        
       # --- NOVO SISTEMA CATEGORIZADO (TOM) ---
        ui.render_categorized_system(
            "📜 Tom Lírico", 
            "tom", 
            core.dados["tom"], 
            help_msg=help_text.get("tom")
        )
        st.divider()
        
        # --- NOVO SISTEMA CATEGORIZADO (INFLUÊNCIA) ---
        ui.render_categorized_system(
            "🎨 Influência Estética", 
            "influencia_estetica", 
            core.dados["influencia_estetica"], 
            help_msg=help_text.get("influencia_estetica")
        )
        st.divider()
        
        ui.hierarchical_field("🎚️ Tipo de Gravação", "tipo_de_gravacao", core.dados["tipo_de_gravacao"], help_msg=help_text.get("tipo_de_gravacao"))

    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #666; font-size: 0.8rem;'>Suno Maestro • Powered by Eduardo Palombo</div>", unsafe_allow_html=True)

    render_history_sidebar(core)

if __name__ == "__main__":

    main()















