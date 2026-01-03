import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, List
from . import state  # Importa callbacks

def custom_copy_button(text_to_copy: str):
    """Botão de cópia customizado usando HTML/JS."""
    button_style = """
    <style>
        body { margin: 0 !important; padding: 0 !important; overflow: hidden; }
        .custom-btn {
            border: 1px solid #3a3f4b; background-color: #F0F2F6; color: #3a3f4b;
            border-radius: 6px; cursor: pointer; width: 100%; height: 38px;
            font-family: "Source Sans Pro", sans-serif; font-weight: 500; font-size: 1rem;
            display: flex; align-items: center; justify-content: center; box-sizing: border-box; transition: 0.2s;
        }
        .custom-btn:hover { border-color: #46c45e; color: #46c45e; background-color: #ffffff; }
    </style>
    """
    
    clean_text = text_to_copy.replace('`', '\\`').replace('$', '\\$')
    copy_script = f"""
    <script>
        function copyToClipboard() {{
            const text = `{clean_text}`;
            const textArea = document.createElement("textarea");
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {{
                document.execCommand('copy');
                const btn = document.getElementById("copyBtn");
                btn.innerText = "✅ Copiado!";
                btn.style.borderColor = "#46c45e"; btn.style.color = "#46c45e";
                setTimeout(() => {{ 
                    btn.innerText = "📋 Copiar"; 
                    btn.style.borderColor = "#3a3f4b"; btn.style.color = "#3a3f4b";
                }}, 2000);
            }} catch (err) {{ console.error('Falha ao copiar', err); }}
            document.body.removeChild(textArea);
        }}
    </script>
    """
    html_content = f"{button_style}{copy_script}<button id='copyBtn' class='custom-btn' onclick='copyToClipboard()'>📋 Copiar</button>"
    components.html(html_content, height=40)

def hierarchical_field(title: str, key: str, data: Dict[str, List[str]], help_msg: str = None):
    """Componente reutilizável para campos hierárquicos (Categoria -> Seleção)."""
    
    if help_msg:
        st.markdown(f"**{title}**", help=help_msg)
    else:
        st.markdown(f"**{title}**")
    
    cat_key, sel_key = f"{key}_cat", f"{key}_sel"
    
    # Colunas: Categoria | Seleção | Aleatório | Limpar
    c1, c2, c3, c4 = st.columns([0.3, 0.3, 0.10, 0.10], gap="small", vertical_alignment="bottom")
    
    with c1:
        opts_cat = [""] + sorted(data.keys())
        curr_cat = st.session_state.get(cat_key, "")
        idx_cat = opts_cat.index(curr_cat) if curr_cat in opts_cat else 0
        st.selectbox(f"C_{key}", opts_cat, index=idx_cat, key=cat_key, label_visibility="collapsed")
    
    with c2:
        current_cat_val = st.session_state.get(cat_key, "")
        opts_sel = [""] + data.get(current_cat_val, [])
        curr_sel = st.session_state.get(sel_key, "")
        idx_sel = opts_sel.index(curr_sel) if curr_sel in opts_sel else 0
        
        st.selectbox(
            f"S_{key}", opts_sel, index=idx_sel, key=sel_key, label_visibility="collapsed",
            on_change=lambda: st.session_state.update({key: st.session_state[sel_key]}) if st.session_state[sel_key] else None
        )
         
    with c3:
        st.button("🎲", key=f"btn_rnd_{key}", use_container_width=True, 
                  on_click=state.randomize_hier_callback, args=(key, data))
    with c4:
        st.button("🧹", key=f"btn_clr_{key}", use_container_width=True, 
                  on_click=state.clear_hier_callback, args=(key,))
    
    st.text_input(f"In_{key}", key=key, label_visibility="collapsed", placeholder=f"Valor final...")

    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

import streamlit as st
import app.state as state

def render_tag_system(title: str, key: str, data: dict, help_msg: str = None):
    """
    Sistema de Tags com Seletor de Categoria (Solução para muitas abas).
    Mantém o padrão da Estrutura, mas usa um selectbox para navegar nas categorias.
    """
    
    st.markdown(f"**{title}**", help=help_msg)
    
    # 1. Linha de Controles
    sc1, sc3, sc4 = st.columns([0.76, 0.12, 0.12], gap="small", vertical_alignment="bottom")
    
    with sc1:
        if not isinstance(st.session_state.get(key), str):
            st.session_state[key] = ""
        st.text_input("Editável", key=key, label_visibility="collapsed", placeholder="Selecione abaixo ou digite...")
        
    with sc3:
        st.button("🎲", key=f"btn_rnd_{key}", use_container_width=True, 
                  on_click=state.randomize_tags_callback, args=(key, data))
        
    with sc4:
        st.button("🧹", key=f"btn_clr_{key}", use_container_width=True, 
                  on_click=lambda: st.session_state.update({key: ""}))

    # 2. Catálogo com Seletor de Categoria Interno
    if data:
        with st.expander("🏷️ Catálogo", expanded=False):
            categorias = list(data.keys())
            
            # Em vez de abas, um seletor simples que não quebra o layout
            col_cat, col_info = st.columns([0.4, 0.6], vertical_alignment="center")
            with col_cat:
                cat_selecionada = st.selectbox(
                    "Filtrar por Categoria:", 
                    categorias, 
                    key=f"sel_cat_{key}",
                    label_visibility="collapsed"
                )
            with col_info:
                st.caption(f"Exibindo itens de: *{cat_selecionada}*")

            st.divider()

            # Grid de Tags da categoria selecionada
            itens = data[cat_selecionada]
            cols = st.columns(3) # 3 colunas para nomes mais longos (como no seu JSON)
            
            for idx, item_pair in enumerate(itens):
                tag_nome, tag_desc = item_pair[0], item_pair[1]
                
                def make_add_tag(val=tag_nome):
                    current = st.session_state.get(key, "").strip()
                    if val not in current:
                        if current and not current.endswith(','):
                            st.session_state[key] = f"{current}, {val}"
                        elif current:
                            st.session_state[key] = f"{current} {val}"
                        else:
                            st.session_state[key] = val

                with cols[idx % 3]:
                    st.button(
                        tag_nome, 
                        key=f"btn_{key}_{cat_selecionada}_{idx}", 
                        help=tag_desc, 
                        on_click=make_add_tag, 
                        use_container_width=True
                    )
            
            # Legenda de ajuda
            st.markdown(
                f"<div style='font-size: 0.8rem; color: gray; margin-top: 10px;'>"
                f"💡 Clique nas tags para adicionar. Passe o mouse para ver a descrição. "
                f"Utilize apenas uma por categoria!</div>", 
                unsafe_allow_html=True
            )


