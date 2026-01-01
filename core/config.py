# core/config.py
import os

# Caminho absoluto da raiz do projeto (sobe um nível a partir de 'core')
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(ROOT_DIR, "dataset")

# Definição dos campos que possuem hierarquia
HIER_KEYS = ["publico", "tom", "tipo_de_gravacao", "influencia_estetica", "narrador"]

# Valores padrão do Estado
STATE_DEFAULTS = {
    "genero": "", "ritmo": "", "idioma": "", "tema": "",
    "mensagem": "", "palavras_chave": "", "referencia": "",
    "vibe_emocional": [], "vibe_cat": "", "vibe_item": "", "vibe_manual": "",
    "prompt_final": "", "show_prompt": False,
    "estrutura": "", "estrutura_sel": "",
    "history": [],
    "new_vibe_input": ""
}
