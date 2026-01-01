# core/logic.py
import re
from typing import List, Dict

def get_ritmos_list(genero: str, core_data: dict) -> List[str]:
    if not genero or genero not in core_data.get("hierarquia", {}): 
        return []
    return [item[0] for item in core_data["hierarquia"][genero]]

def get_structure_map(genero: str, core_data: dict) -> Dict[str, str]:
    if not genero or genero not in core_data.get("hierarquia", {}): 
        return {}
    return {item[0]: item[1] for item in core_data["hierarquia"][genero]}

def get_all_unique_structures(core_data: dict) -> List[str]:
    structures = set()
    hierarquia = core_data.get("hierarquia", {})
    for gen_list in hierarquia.values():
        for item in gen_list:
            if len(item) > 1: 
                structures.add(item[1])
    return sorted(list(structures))

def parse_prompt_for_restore(texto_prompt: str) -> Dict[str, any]:
    partes = texto_prompt.split("AUTOMATIC_INPUTS:")
    texto_usuario = partes[0] if len(partes) > 0 else texto_prompt
    
    mapeamento_reverso = {}
    mapeamento_chaves = {
        "primary_genre": "genero", "specific_style": "ritmo",
        "recording_aesthetic": "tipo_de_gravacao", "artistic_influence": "influencia_estetica",
        "emotional_vibe": "vibe_emocional", "external_refs": "referencia",
        "language": "idioma", "topic": "tema", "core_message": "mensagem",
        "keywords": "palavras_chave", "target_audience": "publico",
        "narrator_perspective": "narrador", "structure_format": "estrutura",
        "lyrical_tone": "tom"
    }

    for chave_prompt, chave_state in mapeamento_chaves.items():
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
            mapeamento_reverso[chave_state] = novo_valor
            
    return mapeamento_reverso
