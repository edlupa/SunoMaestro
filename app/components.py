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

def render_tag_system(title: str, key: str, data: dict, help_msg: str = None):
    """
    Renderiza um sistema de tags limpo (Multiselect) com catálogo expansível.
    Sem restrições de categoria.
    """
    # 1. Cabeçalho e Botões de Ação
    c_head, c_btn = st.columns([0.80, 0.20], vertical_alignment="bottom")
    with c_head:
        if help_msg:
            st.markdown(f"**{title}**", help=help_msg)
        else:
            st.markdown(f"**{title}**")
            
    with c_btn:
        b1, b2 = st.columns(2, gap="small")
        with b1:
             st.button("🎲", key=f"rnd_{key}", help="Sugerir combinação", 
                      on_click=state.randomize_tags_callback, args=(key, data), use_container_width=True)
        with b2:
             st.button("🧹", key=f"clr_{key}", help="Limpar tudo",
                      on_click=state.clear_tags_callback, args=(key,), use_container_width=True)

    # 2. Preparar dados para o Multiselect (Achatar o JSON)
    # Criamos um dicionário reverso para buscar descrição e categoria pelo nome
    item_details = {}
    all_options = []
    
    for category, items_list in data.items():
        for item_pair in items_list:
            name = item_pair[0]
            desc = item_pair[1]
            all_options.append(name)
            item_details[name] = {"cat": category, "desc": desc}
    
    all_options = sorted(all_options)

    # Função de formatação para deixar o dropdown bonito
    def format_func(option):
        details = item_details.get(option)
        if details:
            # Ex: [Modo Emocional] Melancólico | Estado de tristeza...
            return f"[{details['cat']}] {option} | {details['desc']}"
        return option

    # 3. Multiselect Principal
    if key not in st.session_state:
        st.session_state[key] = []

    st.multiselect(
        label=f"Selecione {title}",
        options=all_options,
        default=st.session_state[key],
        key=key,
        format_func=format_func,
        label_visibility="collapsed",
        placeholder="Selecione ou digite..."
    )

    # 4. Input Manual para "Outros"
    manual_key = f"{key}_manual_input"
    def add_manual():
        val = st.session_state.get(manual_key, "").strip()
        if val and val not in st.session_state[key]:
            st.session_state[key].append(val)
            st.session_state[manual_key] = "" # Limpa input

    st.text_input(
        "Adicionar manual",
        key=manual_key,
        placeholder="Adicionar tag personalizada...",
        label_visibility="collapsed",
        on_change=add_manual
    )

    # 5. Catálogo Expansível (Igual Estrutura/Vibe)
    with st.expander(f"📚 Ver Catálogo de {title}", expanded=False):
        for category, items_list in data.items():
            st.markdown(f"**{category}**")
            # Cria chips ou texto pequeno para visualização rápida
            tags_display = [f"`{item[0]}`" for item in items_list]
            st.markdown(" ".join(tags_display))
            st.divider()

    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

