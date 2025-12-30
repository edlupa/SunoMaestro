import streamlit as st
import streamlit.components.v1 as components
import random
import sys
import os
from datetime import datetime
import io
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from core.generator import SunoMaestroCore

st.set_page_config(page_title="Suno Maestro", page_icon="🎛️", layout="wide")

@st.cache_data
def load_css():
    """Carrega o CSS uma única vez e guarda na memória."""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(BASE_DIR, "style.css")
    with open(css_path, encoding="utf-8") as f:
        return f.read()

@st.cache_resource
def get_core_instance(root_path):
    """Instancia o motor do projeto uma única vez."""
    return SunoMaestroCore(base_path=root_path)

# --- APLICAÇÃO ---

# Aplica o CSS (o cache_data garante que não haverá leitura de disco constante)
st.markdown(f"<style>{load_css()}</style>", unsafe_allow_html=True)

# Instancia o Core com cache_resource (os JSONs serão lidos apenas no primeiro acesso)
core = get_core_instance(ROOT)

# --- FUNÇÃO DE CÓPIA CUSTOMIZADA ---
def custom_copy_button(text_to_copy):
    # CSS para garantir que o botão ocupe TODO o espaço do iframe sem sobras
    button_style = """
    <style>
        body { 
            margin: 0 !important; 
            padding: 0 !important; 
            overflow: hidden; 
        }
        .custom-btn {
            border: 1px solid #3a3f4b;
            background-color: #F0F2F6;
            color: #3a3f4b;
            border-radius: 6px;
            cursor: pointer;
            width: 100%;
            height: 38px; /* Altura idêntica ao botão do Streamlit */
            font-family: "Source Sans Pro", sans-serif;
            font-weight: 500;
            font-size: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            box-sizing: border-box;
            transition: 0.2s;
        }
        .custom-btn:hover {
            border-color: #46c45e;
            color: #46c45e;
            background-color: #ffffff;
        }
    </style>
    """
    
    # JavaScript robusto para copiar (fallback para textarea se clipboard API falhar)
    copy_script = f"""
    <script>
        function copyToClipboard() {{
            const text = `{text_to_copy.replace('`', '\\`').replace('$', '\\$')}`;
            
            // Método Fallback (mais compatível com iframes)
            const textArea = document.createElement("textarea");
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {{
                document.execCommand('copy');
                const btn = document.getElementById("copyBtn");
                btn.innerText = "✅ Copiado!";
                btn.style.borderColor = "#46c45e";
                btn.style.color = "#46c45e";
                setTimeout(() => {{ 
                    btn.innerText = "📋 Copiar Prompt"; 
                    btn.style.borderColor = "#3a3f4b";
                    btn.style.color = "#3a3f4b";
                }}, 2000);
            }} catch (err) {{
                console.error('Falha ao copiar', err);
            }}
            document.body.removeChild(textArea);
        }}
    </script>
    """
    
    html_content = f"{button_style}{copy_script}<button id='copyBtn' class='custom-btn' onclick='copyToClipboard()'>📋 Copiar Prompt</button>"
    components.html(html_content, height=40)

# --- ESTADO E CONFIGURAÇÃO ---
STATE_DEFAULTS = {
    "genero": "", "ritmo": "", "idioma": "", "tema": "",
    "mensagem": "", "palavras_chave": "", "referencia": "",
    "vibe_emocional": [], "vibe_cat": "", "vibe_item": "", "vibe_manual": "",
    "prompt_final": "", "show_prompt": False,
    "estrutura": "", "estrutura_sel": "",
    "history": []
}

HIER_KEYS = ["publico", "tom", "tipo_de_gravacao", "influencia_estetica", "narrador"]

# Inicialização Robusta: Garante que TODAS as chaves existam sempre
for k, v in STATE_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

for k in HIER_KEYS:
    if f"{k}_cat" not in st.session_state: st.session_state[f"{k}_cat"] = ""
    if f"{k}_sel" not in st.session_state: st.session_state[f"{k}_sel"] = ""
    if k not in st.session_state: st.session_state[k] = ""

# --- HELPERS DE DADOS ---
def get_ritmos_list(genero):
    if not genero or genero not in core.dados["hierarquia"]: return []
    return [item[0] for item in core.dados["hierarquia"][genero]]

def get_structure_map(genero):
    if not genero or genero not in core.dados["hierarquia"]: return {}
    return {item[0]: item[1] for item in core.dados["hierarquia"][genero]}

def get_all_unique_structures():
    structures = set()
    for gen_list in core.dados["hierarquia"].values():
        for item in gen_list:
            if len(item) > 1: structures.add(item[1])
    return sorted(list(structures))

# --- HANDLERS DE EVENTOS ---
def on_genero_change():
    st.session_state.ritmo = ""

def on_ritmo_change():
    g, r = st.session_state.genero, st.session_state.ritmo
    if g and r:
        mapa = get_structure_map(g)
        sugestao = mapa.get(r, "")
        if sugestao:
            st.session_state.estrutura_sel = sugestao
            st.session_state.estrutura = sugestao

def on_estrutura_sel_change():
    if st.session_state.estrutura_sel:
        st.session_state.estrutura = st.session_state.estrutura_sel

def clear_all():
    for k in STATE_DEFAULTS.keys():
        if k == "history":
                    continue
        st.session_state[k] = [] if k == "vibe_emocional" else ""
    for k in HIER_KEYS: 
        st.session_state[f"{k}_cat"] = ""; st.session_state[f"{k}_sel"] = ""; st.session_state[k] = ""
    st.session_state.show_prompt = False

def random_vibe_generator():
    vibe_data = core.dados["vibe_emocional"]
    st.session_state.vibe_emocional = []
    valid_cats = [c for c, itens in vibe_data.items() if any(i for i in itens)]
    if valid_cats:
        for _ in range(random.randint(3, 5)):
            c = random.choice(valid_cats)
            itens = [i for i in vibe_data[c] if i]
            if itens:
                v = random.choice(itens)
                if v not in st.session_state.vibe_emocional: st.session_state.vibe_emocional.append(v)

def random_all():
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

    for k in HIER_KEYS:
        data = core.dados[k]
        cats = [c for c in data.keys() if data[c]]
        if cats:
            c = random.choice(cats)
            v = random.choice(data[c])
            st.session_state[f"{k}_cat"], st.session_state[f"{k}_sel"], st.session_state[k] = c, v, v
    random_vibe_generator()

def randomize_hier_callback(key, data):
    """Callback para randomizar campos hierárquicos (Público, Tom, etc)"""
    cats = [c for c in data.keys() if data[c]]
    if cats:
        c = random.choice(cats)
        v = random.choice(data[c])
        # Atualiza o estado ANTES da renderização
        st.session_state[f"{key}_cat"] = c
        st.session_state[f"{key}_sel"] = v
        st.session_state[key] = v

def clear_hier_callback(key):
    """Callback para limpar campos hierárquicos"""
    st.session_state[f"{key}_cat"] = ""
    st.session_state[f"{key}_sel"] = ""
    st.session_state[key] = ""

def randomize_struct_callback():
    """Callback para randomizar estrutura"""
    structs = get_all_unique_structures()
    if structs:
        s = random.choice(structs)
        st.session_state.estrutura_sel = s
        st.session_state.estrutura = s

def clear_struct_callback():
    """Callback para limpar estrutura"""
    st.session_state.estrutura_sel = ""
    st.session_state.estrutura = ""

# --- FUNÇÃO DE CALLBACK PARA DELETAR VIBE ---
def delete_vibe(index):
    st.session_state.vibe_emocional.pop(index)

def preparar_exportacao_total(historico):
    """Transforma a lista de histórico em uma string formatada para TXT."""
    if not historico:
        return ""
    
    conteudo_final = "=== EXPORTAÇÃO COMPLETA - SUNO MAESTRO ===\n\n"
    for item in historico:
        conteudo_final += f"📅 DATA: {item['data']}\n"
        conteudo_final += f"🎵 TÍTULO: {item['titulo']}\n"
        conteudo_final += f"{'-'*40}\n"
        conteudo_final += f"{item['conteudo']}\n"
        conteudo_final += f"\n{'='*60}\n\n"
    
    return conteudo_final

def criar_zip_historico(historico):
    """Gera um ficheiro ZIP na memória contendo cada prompt em um TXT separado."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for i, item in enumerate(historico):
            # Nome do ficheiro: "01_Rock_Amor.txt"
            nome_arquivo = f"{len(historico)-i:02d}_{item['titulo'].replace(' ', '_').replace('|', '')}.txt"
            zip_file.writestr(nome_arquivo, item['conteudo'])
    
    return buffer.getvalue()

# --- COMPONENTES UI ---
def hierarchical_field(title, key, data):
    st.markdown(f"**{title}**")
    cat_key, sel_key = f"{key}_cat", f"{key}_sel"
    
    # GARANTIA EXTRA: Se a chave sumir, recria agora
    if cat_key not in st.session_state: st.session_state[cat_key] = ""
    if sel_key not in st.session_state: st.session_state[sel_key] = ""
    
    c1, c2, c3, c4 = st.columns([0.35, 0.35, 0.08, 0.08], gap="small", vertical_alignment="bottom")
    
    with c1:
        opts_cat = [""] + sorted(data.keys())
        val_cat = st.session_state.get(cat_key, "")
        idx_cat = opts_cat.index(val_cat) if val_cat in opts_cat else 0
        st.selectbox(f"C_{key}", opts_cat, index=idx_cat, key=cat_key, label_visibility="collapsed")
    
    with c2:
        current_cat = st.session_state.get(cat_key, "")
        opts_sel = [""] + data.get(current_cat, [])
        val_sel = st.session_state.get(sel_key, "")
        idx_sel = opts_sel.index(val_sel) if val_sel in opts_sel else 0
        st.selectbox(f"S_{key}", opts_sel, index=idx_sel, key=sel_key, label_visibility="collapsed")
         
    with c3:
        # CORREÇÃO: Usando on_click com args
        st.button(
            "🎲", 
            key=f"btn_rnd_{key}", 
            use_container_width=True,
            on_click=randomize_hier_callback,
            args=(key, data) # Passa os argumentos para a função
        )

    with c4:
        # CORREÇÃO: Usando on_click com args
        st.button(
            "🧹", 
            key=f"btn_clr_{key}", 
            use_container_width=True,
            on_click=clear_hier_callback,
            args=(key,)
        )
    
    st.text_input(f"In_{key}", key=key, label_visibility="collapsed", placeholder=f"Valor final...")
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

# --- LAYOUT PRINCIPAL ---
st.title("🎛️ Suno Maestro")
st.markdown("Generate professional prompts for Suno AI v5.")
st.markdown("---")

t_c1, t_c2, t_c3 = st.columns([1, 1, 2], vertical_alignment="center")
with t_c1: st.button("🧹 Limpar Tudo", on_click=clear_all, use_container_width=True)
with t_c2: st.button("🎲 Aleatório", on_click=random_all, use_container_width=True)
with t_c3:
    if st.button("🚀 Gerar Prompt", type="primary", use_container_width=True):
        
        # Coleta os campos
        campos = {k: st.session_state[k] for k in ["genero","ritmo","estrutura","tipo_de_gravacao","influencia_estetica","vibe_emocional","referencia","idioma","tema","mensagem","palavras_chave","publico","narrador","tom"]}
        
        texto_gerado = core.gerar_prompt(campos)
        
        st.session_state.prompt_final = texto_gerado
        st.session_state.show_prompt = True
        
        # --- SALVAMENTO ROBUSTO ---
        # 1. Garante que 'history' existe e é uma lista
        if "history" not in st.session_state or not isinstance(st.session_state.history, list):
            st.session_state.history = []
            
        # 2. Prepara os dados
        agora = datetime.now()
        hora = agora.strftime("%H:%M")
        gen = st.session_state.genero or "Estilo"
        tem = st.session_state.tema or "Geral"
        titulo = f"{hora} | {gen} - {tem}"
        
        # 3. Insere
        novo_item = {
            "titulo": titulo[:40], 
            "conteudo": texto_gerado,
            "data": agora.strftime("%d/%m/%Y %H:%M")
        }
        st.session_state.history.insert(0, novo_item)

if st.session_state.show_prompt:
    st.divider()
    ac1, ac2, ac3 = st.columns([1, 1, 1], vertical_alignment="bottom")
    
    with ac1: 
        custom_copy_button(st.session_state.prompt_final)
        
    with ac2: 
        st.download_button("⬇️ Baixar", st.session_state.prompt_final, "prompt.txt", use_container_width=True)
        
    with ac3: 
        if st.button("❌ Fechar", use_container_width=True): 
            st.session_state.show_prompt = False
            st.rerun()

    st.code(st.session_state.prompt_final, language="yaml")

col_left, col_right = st.columns(2, gap="large")

with col_left:
    st.subheader("📝 Conteúdo")
    lc1, lc2 = st.columns(2)
    with lc1: st.text_input("🌐 Idioma", key="idioma", placeholder="Português (Brasil), Inglês (EUA), Espanhol"); st.text_input("📩 Mensagem", key="mensagem")
    with lc2: st.text_input("💡 Tema", key="tema"); st.text_input("🔑 Tags", key="palavras_chave")
    st.text_input("🎼 Referências Artísticas", key="referencia", placeholder="Aquarela - Toquinho, Garota de Ipanema - Tom Jobim")
    st.divider()

    st.subheader("🎵 Identidade Musical")
    mc1, mc2 = st.columns(2)
    with mc1: 
        opts_gen = [""] + list(core.dados["hierarquia"].keys())
        idx_gen = opts_gen.index(st.session_state.genero) if st.session_state.genero in opts_gen else 0
        st.selectbox("Gênero", opts_gen, index=idx_gen, key="genero", on_change=on_genero_change)
    with mc2: 
        opts_rit = [""] + get_ritmos_list(st.session_state.genero)
        idx_rit = opts_rit.index(st.session_state.ritmo) if st.session_state.ritmo in opts_rit else 0
        st.selectbox("Ritmo", opts_rit, index=idx_rit, key="ritmo", on_change=on_ritmo_change)
    st.divider()

    st.markdown("**🎶 Estrutura**")
    sc1, sc2, sc3, sc4 = st.columns([0.35, 0.35, 0.08, 0.08], gap="small", vertical_alignment="bottom")
    with sc1: 
        opts_est = [""] + get_all_unique_structures()
        idx_est = opts_est.index(st.session_state.estrutura_sel) if st.session_state.estrutura_sel in opts_est else 0
        st.selectbox("Sug. Est.", opts_est, index=idx_est, key="estrutura_sel", on_change=on_estrutura_sel_change, label_visibility="collapsed")
    with sc2: st.text_input("Editável", key="estrutura", label_visibility="collapsed")
    with sc3:
        st.button(
            "🎲", 
            key="btn_rnd_est", 
            use_container_width=True,
            on_click=randomize_struct_callback
        )
    with sc4:
        st.button(
            "🧹", 
            key="btn_clr_est", 
            use_container_width=True,
            on_click=clear_struct_callback
        )
    st.divider()

    st.subheader("✨ Vibe Emocional")
    vc1, vc2, vc5, vc3, vc4 = st.columns([0.35, 0.35, 0.08, 0.08, 0.08], vertical_alignment="bottom")
    vd = core.dados["vibe_emocional"]
    with vc1: st.selectbox("Cat. Vibe", [""] + sorted(vd.keys()), key="vibe_cat", label_visibility="collapsed")
    with vc2: st.selectbox("Sug. Vibe", [""] + vd.get(st.session_state.vibe_cat, []), key="vibe_item", label_visibility="collapsed")
    with vc3: 
        if st.button("🎲", key="btn_v_rnd", use_container_width=True): random_vibe_generator(); st.rerun()
    with vc4:
        if st.button("🧹", key="btn_v_clr", use_container_width=True): st.session_state.vibe_emocional = []; st.rerun()
    with vc5:
        if st.button("✔️", key="btn_v_add", use_container_width=True):
            val = st.session_state.vibe_item or st.session_state.vibe_manual
            if val and val not in st.session_state.vibe_emocional: st.session_state.vibe_emocional.append(val)
    st.text_input("Vibe Manual", key="vibe_manual", placeholder="Adicionar manualmente...")
    for i, v in enumerate(st.session_state.vibe_emocional):
        rc1, rc2 = st.columns([0.9, 0.08], vertical_alignment="center")
        with rc1: 
            st.markdown(f"**🔹 {v}**")
        with rc2: 
            # Usar on_click em vez de if st.button evita o reset de outros campos
            st.button("❌", key=f"del_v_{i}_{v}", on_click=delete_vibe, args=(i,))

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

# --- BARRA LATERAL DE HISTÓRICO ---
with st.sidebar:
    st.header("📜 Histórico")
    st.info("Os prompts gerados nesta sessão ficam salvos abaixo.")
    
    if not st.session_state.history:
        st.write("Nenhum prompt gerado ainda.")
    
    for idx, item in enumerate(st.session_state.history):
        with st.expander(item["titulo"]):
            st.caption(f"Gerado em: {item['data']}")
            
            st.download_button(
                label="⬇️ Baixar txt",
                data=item["conteudo"],
                file_name=f"suno_prompt_{idx}.txt",
                mime="text/plain",
                key=f"dl_{idx}",
                use_container_width=True
            )

            st.code(item["conteudo"], language="yaml")
                       
    
    st.markdown("---") # Linha divisória

    if st.session_state.history:
        # Gerar os dados do ZIP
        zip_data = criar_zip_historico(st.session_state.history)
        
        st.download_button(
            label="📦 Baixar Tudo (ZIP)",
            data=zip_data,
            file_name=f"prompts_suno_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
            mime="application/zip",
            use_container_width=True,
            help="Descarrega todos os prompts do histórico em ficheiros individuais dentro de um ZIP."
        )

    if st.session_state.history:
        if st.button("🗑️ Limpar Histórico", use_container_width=True):
            st.session_state.history = []
            st.rerun()