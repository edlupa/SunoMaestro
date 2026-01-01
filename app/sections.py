import streamlit as st
from datetime import datetime
from core.logic import get_all_unique_structures
import app.callbacks as cb
from app.utils import custom_copy_button, criar_zip_historico

def render_structure_section(core_data):
    st.markdown("**🎶 Estrutura**")
    sc1, sc3, sc4 = st.columns([0.70, 0.10, .10], gap="small", vertical_alignment="bottom")
    with sc1: 
        opts_est = [""] + get_all_unique_structures(core_data)
        curr = st.session_state.estrutura_sel
        idx = opts_est.index(curr) if curr in opts_est else 0
        st.selectbox("Sug. Est.", opts_est, index=idx, key="estrutura_sel", 
                     on_change=cb.on_estrutura_sel_change, label_visibility="collapsed")
    with sc3:
        st.button("🎲", key="btn_rnd_est", use_container_width=True, on_click=cb.randomize_struct_callback, args=(core_data,))
    with sc4:
        st.button("🧹", key="btn_clr_est", use_container_width=True, on_click=lambda: st.session_state.update({"estrutura_sel":"", "estrutura":""}))
    
    st.text_input("Editável", key="estrutura", label_visibility="collapsed", placeholder="Selecione ou monte sua estrutura...")

    # Tags e Metatags
    metatags = core_data.get("metatags", {})
    if metatags:
        with st.expander("🏷️ Adicionar Seções e Tags", expanded=False):
            abas = st.tabs(list(metatags.keys()))
            for i, (cat, itens) in enumerate(metatags.items()):
                with abas[i]:
                    cols = st.columns(4) 
                    for idx, item in enumerate(itens):
                        with cols[idx % 4]:
                            st.button(item[0], key=f"tag_{cat}_{idx}", help=item[1], 
                                      on_click=cb.add_tag_to_structure, args=(item[0],), use_container_width=True)

def render_vibe_section(core_data):
    st.subheader("✨ Vibe Emocional")
    
    # --- ÁREA DO CATÁLOGO DE VIBES (Corrigida) ---
    dados_vibes = core_data.get("vibe_emocional", {})
    if dados_vibes:
        with st.expander("🎭 Catálogo de Emoções e Vibes", expanded=False):
            if isinstance(dados_vibes, dict):
                categorias_ordenadas = sorted(dados_vibes.keys())
                abas_v = st.tabs(categorias_ordenadas)
                for i, categoria in enumerate(categorias_ordenadas):
                    with abas_v[i]:
                        # Ordena itens
                        itens_ordenados = sorted(dados_vibes[categoria], key=lambda x: x[0] if isinstance(x, list) else x)
                        cols_v = st.columns(4)
                        for idx, item in enumerate(itens_ordenados):
                            v_nome = item[0] if isinstance(item, list) else item
                            v_desc = item[1] if isinstance(item, list) and len(item) > 1 else ""
                            with cols_v[idx % 4]:
                                # Chama o callback add_vibe_click
                                st.button(v_nome, key=f"tag_v_cat_{categoria}_{idx}", help=v_desc, 
                                          on_click=cb.add_vibe_click, args=(v_nome,), use_container_width=True)
            else:
                # Fallback para lista simples
                itens_ordenados = sorted(dados_vibes, key=lambda x: x[0] if isinstance(x, list) else x)
                cols_v = st.columns(4)
                for idx, item in enumerate(itens_ordenados):
                    v_nome = item[0] if isinstance(item, list) else item
                    with cols_v[idx % 4]:
                        st.button(v_nome, key=f"tag_v_list_{idx}", 
                                  on_click=cb.add_vibe_click, args=(v_nome,), use_container_width=True)
            st.caption("💡 Clique para adicionar à lista de vibes.")
    # -----------------------------------------------

    cv1, cv2, cv3 = st.columns([0.70, 0.10, 0.10], gap="small", vertical_alignment="bottom")
    with cv1:
        st.text_input("Adicionar manualmente", key="new_vibe_input", on_change=cb.submit_manual_vibe, label_visibility="collapsed", placeholder="Ex: Melancólico...")
    with cv2:
        st.button("🎲", key="btn_rnd_vibe", use_container_width=True, on_click=cb.random_vibe_generator, args=(core_data,))
    with cv3:
        st.button("🧹", key="btn_clr_vibe", use_container_width=True, on_click=lambda: st.session_state.update({"vibe_emocional": []}))
    
    if st.session_state.vibe_emocional:
        for i, v in enumerate(st.session_state.vibe_emocional):
            c1, c2 = st.columns([0.8, 0.10])
            with c1: st.markdown(f"**{v}**") 
            with c2: 
                if st.button("❌", key=f"del_{i}"): cb.delete_vibe(i); st.rerun()

def render_history_sidebar():
    """Renderiza a barra lateral com o histórico completo e funcional."""
    with st.sidebar:
        st.header("📜 Histórico")
        st.info("Prompts gerados nesta sessão.")
        
        if not st.session_state.history:
            st.write("Nenhum prompt gerado ainda.")
        
        for idx, item in enumerate(st.session_state.history):
            # O título agora inclui o índice para facilitar a identificação
            with st.expander(f"{item['titulo']}"):
                st.caption(f"🕒 {item.get('data', 'N/A')}")
                
                # Botões de Ação
                h_col1, h_col2 = st.columns(2)
                with h_col1:
                    # O botão de restaurar usa o callback que reverte o session_state
                    st.button("🔄 Restaurar", key=f"hist_rest_{idx}", 
                              on_click=cb.callback_restaurar, args=(item["conteudo"],),
                              use_container_width=True)
                with h_col2:
                    # O botão de cópia via JS/HTML
                    custom_copy_button(item["conteudo"])
                
                st.code(item["conteudo"], language="yaml")
        
        st.markdown("---")
        
        if st.session_state.history:
            # Opção de baixar tudo em ZIP
            zip_data = criar_zip_historico(st.session_state.history)
            st.download_button(
                label="📦 Baixar Tudo (ZIP)",
                data=zip_data,
                file_name=f"prompts_suno_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                mime="application/zip",
                use_container_width=True
            )
            
            # Botão para limpar a lista do estado
            if st.button("🗑️ Limpar Histórico", use_container_width=True):
                st.session_state.history = []
                st.rerun()
