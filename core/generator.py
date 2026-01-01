# core/generator.py
import json
import os
import streamlit as st
# Importa do novo arquivo de config
from core.config import DATASET_DIR 

class SunoMaestroCore:
    def __init__(self, base_path=None):
        # Se base_path não for passado, usa o do config
        self.dataset_dir = base_path if base_path else DATASET_DIR
        self.arquivos = {
            "hierarquia": "01_genero_ritmo.json", 
            "tipo_de_gravacao": "02_tipo_de_gravacao.json",
            "influencia_estetica": "03_influencia_estetica.json", 
            "vibe_emocional": "04_vibe_emocional.json",
            "publico": "05_publico_alvo.json", 
            "tom": "06_tom_lirico.json",
            "narrador": "07_narrador.json",
            "metatags": "08_metatags_musicais.json"
        }
        self.dados = self.load_all_data()

    @st.cache_data
    def load_all_data(_self):
        dados_carregados = {}
        for key, filename in _self.arquivos.items():
            filepath = os.path.join(_self.dataset_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    dados_carregados[key] = json.load(f)
            except FileNotFoundError:
                dados_carregados[key] = {}
        return dados_carregados
    
    # ... MANTENHA O RESTO DO SEU MÉTODO gerar_prompt AQUI ...
    # (Copie o resto da classe original que você já tem)
    def gerar_prompt(self, inputs):
        # ... seu código original ...
        pass
