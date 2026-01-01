# app/callbacks.py
import streamlit as st
import random
# Imports cruzados: app pegando coisas do core
from core.config import STATE_DEFAULTS, HIER_KEYS
from core.logic import get_structure_map, get_all_unique_structures, parse_prompt_for_restore

def init_session_state():
    for k, v in STATE_DEFAULTS.items():
        if k not in st.session_state: st.session_state[k] = v
    for k in HIER_KEYS:
        if f"{k}_cat" not in st.session_state: st.session_state[f"{k}_cat"] = ""
        if f"{k}_sel" not in st.session_state: st.session_state[f"{k}_sel"] = ""
        if k not in st.session_state: st.session_state[k] = ""

def on_genero_change():
    st.session_state.ritmo = ""

def on_ritmo_change(core_data):
    g, r = st.session_state.genero, st.session_state.ritmo
    if g and r:
        mapa = get_structure_map(g, core_data)
        if sugestao := mapa.get(r, ""):
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
    st.session_state[f"{key}_cat"] = ""; st.session_state[f"{key}_sel"] = ""; st.session_state[key] = ""

def random_vibe_generator(core_data):
    vibe_data = core_data.get("vibe_emocional", {})
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

def randomize_struct_callback(core_data):
    if structs := get_all_unique_structures(core_data):
        s = random.choice(structs)
        st.session_state.estrutura_sel = s; st.session_state.estrutura = s

def random_all(core_data):
    hierarquia = core_data.get("hierarquia", {})
    if generos := list(hierarquia.keys()):
        g = random.choice(generos)
        st.session_state.genero = g
        if itens_ritmo := hierarquia.get(g, []):
            escolhido = random.choice(itens_ritmo)
            st.session_state.ritmo = escolhido[0]
            st.session_state.estrutura = escolhido[1]
            st.session_state.estrutura_sel = escolhido[1]
    for k in HIER_KEYS:
        randomize_hier_callback(k, core_data.get(k, {}))
    random_vibe_generator(core_data)

def add_tag_to_structure(tag):
    cur = st.session_state.estrutura
    st.session_state.estrutura = f"{cur} {tag}" if cur else tag

def add_vibe_click(vibe_nome):
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
        if val not in st.session_state.vibe_emocional: st.session_state.vibe_emocional.append(val)
        st.session_state.new_vibe_input = ""

def callback_restaurar(texto_prompt):
    dados = parse_prompt_for_restore(texto_prompt)
    for k, v in dados.items(): st.session_state[k] = v
    for k in HIER_KEYS: st.session_state[f"{k}_cat"] = ""; st.session_state[f"{k}_sel"] = ""
    st.session_state.show_prompt = False
