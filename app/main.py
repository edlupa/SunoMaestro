import streamlit as st
import streamlit.components.v1 as components
import random
import sys
import os
import io
import zipfile
import re
from datetime import datetime
from typing import Dict, List, Any

# Configuração de Paths
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from core.generator import SunoMaestroCore

# Configuração da Página
st.set_page_config(page_title="Suno Maestro", page_icon="🎛️", layout="wide")

# --- CONSTANTES E CONFIGURAÇÕES ---
HIER_KEYS = ["publico", "tom", "tipo_de_gravacao", "influencia_estetica", "narrador"]
STATE_DEFAULTS = {
    "genero": "", "ritmo": "", "idioma": "", "tema": "",
    "mensagem": "", "palavras_chave": "", "referencia": "",
    "vibe_emocional": [], "vibe_cat": "", "vibe_item": "", "vibe_manual": "",
    "prompt_final": "", "show_prompt": False,
    "estrutura": "", "estrutura_sel": "",
    "history": [],
    "new_vibe_input": ""
}

# --- SINGLETONS E CACHE ---
@st.cache_data
def load_css() -> str:
    """Carrega o CSS uma única vez."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(base_dir, "style.css")
    with open(css_path, encoding="utf-8") as f:
        return f.read()

@st.cache_resource
def get_core_instance(root_path: str) -> SunoMaestroCore:
    """Instancia o motor do projeto uma única vez."""
    return SunoMaestroCore(base_path=root_path)

# --- INICIALIZAÇÃO DO ESTADO ---
def init_session_state():
    """Garante que todas as chaves necessárias existam no session_state."""
    for k, v in STATE_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v

    for k in HIER_KEYS:
        if f"{k}_cat" not in st.session_state: st.session_state[f"{k}_cat"] = ""
        if f"{k}_sel" not in st.session_state: st.session_state[f"{k}_sel"] = ""
        if k not in st.session_state: st.session_state[k] = ""

# --- COMPONENTES UI AUXILIARES ---
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

def hierarchical_field(title: str, key: str, data: Dict[str, List[str]]):
    """Componente reutilizável para campos hierárquicos (Categoria -> Seleção)."""
    st.markdown(f"**{title}**")
    cat_key, sel_key = f"{key}_cat", f"{key}_sel"
    
    # Colunas: Categoria | Seleção | Aleatório | Limpar
    c1, c2, c3, c4 = st.columns([0.3, 0.3, 0.10, 0.10], gap="small", vertical_alignment="bottom")
    
    with c1:
        opts_cat = [""] + sorted(data.keys())
        # Safe get index
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
                  on_click=randomize_hier_callback, args=(key, data))
    with c4:
        st.button("🧹", key=f"btn_clr_{key}", use_container_width=True, 
                  on_click=clear_hier_callback, args=(key,))
    
    st.text_input(f"In_{key}", key=key, label_visibility="collapsed", placeholder=f"Valor final...")
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

# --- LOGICA E CALLBACKS ---
def get_ritmos_list(genero, core):
    if not genero or genero not in core.dados["hierarquia"]: return []
    return [item[0] for item in core.dados["hierarquia"][genero]]

def get_structure_map(genero, core):
    if not genero or genero not in core.dados["hierarquia"]: return {}
    return {item[0]: item[1] for item in core.dados["hierarquia"][genero]}

def get_all_unique_structures(core):
    structures = set()
    for gen_list in core.dados["hierarquia"].values():
        for item in gen_list:
            if len(item) > 1: structures.add(item[1])
    return sorted(list(structures))

# Callbacks de UI
def on_genero_change():
    st.session_state.ritmo = ""

def on_ritmo_change(core):
    g, r = st.session_state.genero, st.session_state.ritmo
    if g and r:
        mapa = get_structure_map(g, core)
        sugestao = mapa.get(r, "")
        if sugestao:
            st.session_state.estrutura_sel = sugestao
            st.session_state.estrutura = sugestao

def on_estrutura_sel_change():
    if st.session_state.estrutura_sel:
        st.session_state.estrutura = st.session_state.estrutura_sel

def clear_all():
    for k in STATE_DEFAULTS.keys():
        if k == "history": continue
        st.session_state[k] = [] if k == "vibe_emocional" else ""
    for k in HIER_KEYS: 
        st.session_state[f"{k}_cat"] = ""; st.session_state[f"{k}_sel"] = ""; st.session_state[k] = ""
    st.session_state.show_prompt = False

def randomize_hier_callback(key, data):
    cats = [c for c in data.keys() if data[c]]
    if cats:
        c = random.choice(cats)
        v = random.choice(data[c])
        st.session_state[f"{key}_cat"] = c
        st.session_state[f"{key}_sel"] = v
        st.session_state[key] = v

def clear_hier_callback(key):
    st.session_state[f"{key}_cat"] = ""
    st.session_state[f"{key}_sel"] = ""
    st.session_state[key] = ""

def random_vibe_generator(core):
    vibe_data = core.dados["vibe_emocional"]
    st.session_state.vibe_emocional = []
    valid_cats = [c for c, itens in vibe_data.items() if any(i for i in itens)]
    if valid_cats:
        for _ in range(random.randint(3, 5)):
            c = random.choice(valid_cats)
            itens = [i for i in vibe_data[c] if i]
            if itens:
                v = random.choice(itens)
                if v not in st.session_state.vibe_emocional: 
                    st.session_state.vibe_emocional.append(v)

def random_all(core):
    # Gênero e Ritmo
    generos = list(core.dados["hierarquia"].keys())
    if generos:
        g = random.choice(generos)
        st.session_state.genero = g
        itens_ritmo = core.dados["hierarquia"].get(g, [])
        if itens_ritmo:
            escolhido = random.choice(itens_ritmo)
            st.session_state.ritmo = escolhido[0]
            st.session_state.estrutura = escolhido[1]
            st.session_state.estrutura_sel = escolhido[1]

    # Campos Hierárquicos
    for k in HIER_KEYS:
        data = core.dados[k]
        randomize_hier_callback(k, data)
        
    random_vibe_generator(core)

def add_tag_to_structure(tag):
    cur = st.session_state.estrutura
    st.session_state.estrutura = f"{cur} {tag}" if cur else tag

def add_vibe_click(vibe_nome):
    if "vibe_emocional" not in st.session_state: st.session_state.vibe_emocional = []
    if vibe_nome not in st.session_state.vibe_emocional:
        st.session_state.vibe_emocional.append(vibe_nome)
    else:
        st.toast(f"A vibe '{vibe_nome}' já foi adicionada!", icon="⚠️")

def delete_vibe(index):
    if len(st.session_state.vibe_emocional) > index:
        st.session_state.vibe_emocional.pop(index)

def submit_manual_vibe():
    val = st.session_state.get("new_vibe_input", "").strip()
    if val:
        if val not in st.session_state.vibe_emocional:
            st.session_state.vibe_emocional.append(val)
        st.session_state.new_vibe_input = ""

def randomize_struct_callback(core):
    structs = get_all_unique_structures(core)
    if structs:
        s = random.choice(structs)
        st.session_state.estrutura_sel = s
        st.session_state.estrutura = s

def callback_restaurar(texto_prompt):
    """Restaura o estado baseado no texto do prompt (parse reverso)."""
    partes = texto_prompt.split("AUTOMATIC_INPUTS:")
    texto_usuario = partes[0] if len(partes) > 0 else texto_prompt
    
    mapeamento = {
        "primary_genre": "genero", "specific_style": "ritmo",
        "recording_aesthetic": "tipo_de_gravacao", "artistic_influence": "influencia_estetica",
        "emotional_vibe": "vibe_emocional", "external_refs": "referencia",
        "language": "idioma", "topic": "tema", "core_message": "mensagem",
        "keywords": "palavras_chave", "target_audience": "publico",
        "narrator_perspective": "narrador", "structure_format": "estrutura",
        "lyrical_tone": "tom"
    }

    for chave_prompt, chave_state in mapeamento.items():
        padrao = rf'{chave_prompt}: "(.*?)"'
        match = re.search(padrao, texto_usuario)
        if match:
            valor = match.group(1).strip()
            if "AUTOMATIC_INPUT" in valor or valor.lower() == "none" or valor == "":
                novo_valor = [] if chave_state == "vibe_emocional" else ""
            elif chave_state == "vibe_emocional":
                limpo = valor.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
                novo_valor = [v.strip() for v in limpo.split(",") if v.strip()]
            else:
                novo_valor = valor
            st.session_state[chave_state] = novo_valor

    # Limpar categorias UI
    for k in HIER_KEYS:
        st.session_state[f"{k}_cat"] = ""
        st.session_state[f"{k}_sel"] = ""
    
    st.session_state.show_prompt = False

def criar_zip_historico(historico):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for i, item in enumerate(historico):
            nome_arquivo = f"{len(historico)-i:02d}_{item['titulo'].replace(' ', '_').replace('|', '')}.txt"
            zip_file.writestr(nome_arquivo, item['conteudo'])
    return buffer.getvalue()

# --- FUNÇÕES DE RENDERIZAÇÃO DE SEÇÃO ---
def render_structure_section(core):
    st.markdown("**🎶 Estrutura**")
    sc1, sc3, sc4 = st.columns([0.70, 0.10, .010], gap="small", vertical_alignment="bottom")
    with sc1: 
        opts_est = [""] + get_all_unique_structures(core)
        curr = st.session_state.estrutura_sel
        idx_est = opts_est.index(curr) if curr in opts_est else 0
        st.selectbox("Sug. Est.", opts_est, index=idx_est, key="estrutura_sel", 
                     on_change=on_estrutura_sel_change, label_visibility="collapsed")
    with sc3:
        st.button("🎲", key="btn_rnd_est", use_container_width=True, on_click=randomize_struct_callback, args=(core,))
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
                                      on_click=add_tag_to_structure, args=(tag_nome,), use_container_width=True)
            st.caption("💡 Clique nas tags para adicionar ao final da estrutura.")

def render_vibe_section(core):
    st.subheader("✨ Vibe Emocional")
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
                                          on_click=add_vibe_click, args=(v_nome,), use_container_width=True)
            else:
                # Fallback se for lista simples
                itens_ordenados = sorted(dados_vibes, key=lambda x: x[0] if isinstance(x, list) else x)
                cols_v = st.columns(4)
                for idx, item in enumerate(itens_ordenados):
                    v_nome = item[0] if isinstance(item, list) else item
                    with cols_v[idx % 4]:
                        st.button(v_nome, key=f"tag_v_list_{idx}", on_click=add_vibe_click, args=(v_nome,), use_container_width=True)
            st.caption("💡 Clique para adicionar à lista de vibes.")

    cv1, cv2, cv3 = st.columns([0.80, 0.10, 0.10], gap="small", vertical_alignment="bottom")
    with cv1:
        st.text_input("Adicionar manualmente", key="new_vibe_input", placeholder="Ex: Melancólico, Eufórico...", 
                      on_change=submit_manual_vibe, label_visibility="collapsed")
    with cv2:
        st.button("🎲", key="btn_rnd_vibe_local", use_container_width=True, on_click=random_vibe_generator, args=(core,))
    with cv3:
        st.button("🧹", key="btn_clr_vibe_local", use_container_width=True, on_click=lambda: st.session_state.update({"vibe_emocional": []}))
    
    if st.session_state.vibe_emocional:
        for i, v in enumerate(st.session_state.vibe_emocional):
            c1, c2 = st.columns([1.3, 0.10], gap="small")
            with c1: st.markdown(f"**{v}**") 
            with c2:
                if st.button("❌", key=f"del_vibe_{i}"):
                    delete_vibe(i)
                    st.rerun()
    else:
        st.caption("Nenhuma vibe selecionada.")

def render_history_sidebar():
    with st.sidebar:
        st.header("📜 Histórico")
        st.info("Os prompts gerados nesta sessão ficam salvos abaixo.")
        
        if not st.session_state.history:
            st.write("Nenhum prompt gerado ainda.")
        
        for idx, item in enumerate(st.session_state.history):
            with st.expander(item["titulo"]):
                st.caption(f"Gerado em: {item['data']}")
                sb1, sb2 = st.columns([0.2, 0.2], gap="small", vertical_alignment="bottom")
                with sb1: st.button("🔄 Restaurar", key=f"rest_{idx}", use_container_width=True, on_click=callback_restaurar, args=(item["conteudo"],))
                with sb2: custom_copy_button(item["conteudo"])
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

# --- MAIN APP ---
def main():
    # Inicializações
    st.markdown(f"<style>{load_css()}</style>", unsafe_allow_html=True)
    init_session_state()
    core = get_core_instance(ROOT)
    placeholder_aviso = st.empty()

    # Cabeçalho
    st.title("🎛️ Suno Maestro")
    st.markdown("Generate professional prompts for Suno AI v5.")
    st.markdown("---")

    # Controles Superiores
    t_c1, t_c2, t_c3 = st.columns([1, 1, 2], vertical_alignment="center")
    with t_c1: st.button("🧹 Limpar Tudo", on_click=clear_all, use_container_width=True)
    with t_c2: st.button("🎲 Aleatório", on_click=random_all, args=(core,), use_container_width=True)
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
        with ac1: custom_copy_button(st.session_state.prompt_final)
        with ac2: st.download_button("⬇️ Baixar", st.session_state.prompt_final, "prompt.txt", use_container_width=True)
        with ac3: 
            if st.button("❌ Fechar", use_container_width=True): 
                st.session_state.show_prompt = False
                st.rerun()
        st.code(st.session_state.prompt_final, language="yaml")

    # Layout Principal (Formulários)
    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        st.subheader("📝 Composição")
        lc1, lc2 = st.columns(2)
        with lc1: st.text_input("💡 Tema*", key="tema"); st.text_input("📩 Mensagem", key="mensagem")
        with lc2: st.text_input("🔑 Tags", key="palavras_chave"); st.text_input("🌐 Idioma*", key="idioma", placeholder="Português (Brasil), Inglês (EUA), Espanhol")
        st.divider()

        st.subheader("🎵 Identidade Musical")
        mc1, mc2 = st.columns(2)
        with mc1: 
            opts_gen = [""] + list(core.dados["hierarquia"].keys())
            idx_gen = opts_gen.index(st.session_state.genero) if st.session_state.genero in opts_gen else 0
            st.selectbox("Gênero*", opts_gen, index=idx_gen, key="genero", on_change=on_genero_change)
        with mc2: 
            opts_rit = [""] + get_ritmos_list(st.session_state.genero, core)
            curr_rit = st.session_state.ritmo
            idx_rit = opts_rit.index(curr_rit) if curr_rit in opts_rit else 0
            st.selectbox("Ritmo", opts_rit, index=idx_rit, key="ritmo", on_change=on_ritmo_change, args=(core,))
        st.text_input("🎼 Referências Artísticas", key="referencia", placeholder="Aquarela - Toquinho, Garota de Ipanema - Tom Jobim")
        st.divider()

        render_structure_section(core)
        st.divider()
        render_vibe_section(core)

    with col_right:
        hierarchical_field("🎧 Público Alvo", "publico", core.dados["publico"])
        st.divider()
        hierarchical_field("🎤 Narrador", "narrador", core.dados["narrador"])
        st.divider()
        hierarchical_field("📜 Tom Lírico", "tom", core.dados["tom"])
        st.divider()
        hierarchical_field("🎨 Influência Estética", "influencia_estetica", core.dados["influencia_estetica"])
        st.divider()
        hierarchical_field("🎚️ Tipo de Gravação", "tipo_de_gravacao", core.dados["tipo_de_gravacao"])

    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #666; font-size: 0.8rem;'>Suno Maestro • Powered by Eduardo Palombo</div>", unsafe_allow_html=True)

    render_history_sidebar()

if __name__ == "__main__":
    main()
