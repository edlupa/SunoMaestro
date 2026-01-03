import streamlit as st
import random
import re

# --- CONSTANTES ---
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

def init_session_state():
    """Garante que todas as chaves necessárias existam no session_state."""
    for k, v in STATE_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v

    for k in HIER_KEYS:
        if f"{k}_cat" not in st.session_state: st.session_state[f"{k}_cat"] = ""
        if f"{k}_sel" not in st.session_state: st.session_state[f"{k}_sel"] = ""
        if k not in st.session_state: st.session_state[k] = ""

# --- HELPERS DE DADOS ---
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

# --- CALLBACKS ---
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
    # 1. Limpa os campos definidos no STATE_DEFAULTS
    for k in STATE_DEFAULTS.keys():
        if k == "history": 
            continue
        if k == "vibe_emocional":
            st.session_state[k] = []  # Garante lista vazia
        else:
            st.session_state[k] = ""  # Garante string vazia

    # 2. Limpa especificamente os campos hierárquicos (Público, Narrador, etc.)
    for k in HIER_KEYS: 
        st.session_state[f"{k}_cat"] = ""
        st.session_state[f"{k}_sel"] = ""
        st.session_state[k] = ""
    
    # 3. Reseta o controle de exibição
    st.session_state.show_prompt = False
    
    # 4. Limpa campos auxiliares de input de vibe se existirem
    if "new_vibe_input" in st.session_state:
        st.session_state.new_vibe_input = ""

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

def randomize_struct_callback(core):
    structs = get_all_unique_structures(core)
    if structs:
        s = random.choice(structs)
        st.session_state.estrutura_sel = s
        st.session_state.estrutura = s

def callback_restaurar(texto_prompt):
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

    for k in HIER_KEYS:
        st.session_state[f"{k}_cat"] = ""
        st.session_state[f"{k}_sel"] = ""
    
    st.session_state.show_prompt = False

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

def handle_tag_selection(key: str, data: dict):
    """
    Garante que apenas 1 item por categoria seja selecionado.
    Se o usuário selecionar um novo item da mesma categoria, o antigo é removido.
    """
    selected_items = st.session_state[key]
    
    # 1. Mapeia cada item para sua categoria {"Item": "Categoria"}
    item_to_cat = {}
    for cat, items_list in data.items():
        for item_pair in items_list:
            item_name = item_pair[0] # O nome está no índice 0
            item_to_cat[item_name] = cat
            
    # 2. Verifica duplicidade de categorias (de trás para frente para manter o último selecionado)
    seen_cats = set()
    final_list = []
    
    # Invertemos para dar prioridade à seleção mais recente (última da lista)
    for item in reversed(selected_items):
        cat = item_to_cat.get(item)
        
        # Se o item pertence a uma categoria conhecida do JSON
        if cat:
            if cat not in seen_cats:
                seen_cats.add(cat)
                final_list.insert(0, item) # Adiciona no início para manter ordem original
            # Se a categoria já foi vista, ignoramos este item (foi substituído pelo novo)
        else:
            # Se for um item que não está no JSON (segurança), mantém
            final_list.insert(0, item)
            
    st.session_state[key] = final_list

def randomize_tags_callback(key: str, data: dict):
    """Seleciona aleatoriamente até 3 itens de categorias diferentes."""
    import random
    all_cats = list(data.keys())
    # Escolhe até 3 categorias aleatórias (sem repetir)
    chosen_cats = random.sample(all_cats, k=min(3, len(all_cats)))
    
    selection = []
    for cat in chosen_cats:
        items = data[cat]
        if items:
            # Pega um item aleatório dessa categoria
            item_name = random.choice(items)[0]
            selection.append(item_name)
            
    st.session_state[key] = selection

def clear_tags_callback(key: str):
    """Limpa as tags e o campo manual."""
    st.session_state[key] = []
    # Limpa também o input manual associado
    manual_key = f"{key}_manual_input"
    if manual_key in st.session_state:
        st.session_state[manual_key] = ""

        st.session_state.new_vibe_input = ""

