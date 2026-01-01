# app/utils.py
import streamlit as st
import streamlit.components.v1 as components
import os
import io
import zipfile

@st.cache_data
def load_css(file_name="style.css") -> str:
    # Procura o CSS na mesma pasta que este arquivo (app/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, file_name)
    try:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def custom_copy_button(text_to_copy: str):
    if not text_to_copy: return
    # ... (MANTENHA O CÓDIGO DO BOTÃO JS QUE ENVIEI ANTES) ...
    # Para economizar espaço aqui, use a mesma função custom_copy_button da resposta anterior

def criar_zip_historico(historico):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for i, item in enumerate(historico):
            safe_title = item['titulo'].replace(' ', '_').replace('|', '').replace('/', '-')
            zip_file.writestr(f"{len(historico)-i:02d}_{safe_title}.txt", item['conteudo'])
    return buffer.getvalue()
