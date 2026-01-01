import json
import os
import streamlit as st

class SunoMaestroCore:
    def __init__(self, base_path):
        self.base_path = base_path
        self.dataset_dir = os.path.join(self.base_path, "dataset")
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
        # Agora chamamos a função que tem o cache
        self.dados = self.load_all_data()

    @st.cache_data
    def load_all_data(_self): # O _ no _self diz ao Streamlit para não tentar "cahear" a classe inteira, apenas o retorno
        dados_carregados = {}
        for key, filename in _self.arquivos.items():
            filepath = os.path.join(_self.dataset_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f: 
                    dados_carregados[key] = json.load(f)
            except Exception:
                dados_carregados[key] = {}
                print(f"Erro ao carregar {filename}: {e}")
        return dados_carregados

    def gerar_prompt(self, campos):
        # Lógica: Se vazio ou None -> "AUTOMATIC_INPUT"
        d = {}
        for k, v in campos.items():
            if isinstance(v, list):
                val = ", ".join(filter(None, v))
                d[k] = val if val.strip() else "AUTOMATIC_INPUT"
            else:
                val = str(v).strip() if v else ""
                d[k] = val if val else "AUTOMATIC_INPUT"

        return f"""suno_music_generator_prompt:
  ROLE: "Composer, arranger, lyricist, music producer, and prompt engineer specialized in Suno 5.0"

  USER_INPUTS:
    musical_identity:
      primary_genre: "{d.get('genero')}"
      specific_style: "{d.get('ritmo')}"
      recording_aesthetic: "{d.get('tipo_de_gravacao')}"
      artistic_influence: "{d.get('influencia_estetica')}"
      emotional_vibe: "{d.get('vibe_emocional')}"
      external_refs: "{d.get('referencia')}"

    lyrics_specs:
      language: "{d.get('idioma')}"
      topic: "{d.get('tema')}"
      core_message: "{d.get('mensagem')}"
      keywords: "{d.get('palavras_chave')}"
      target_audience: "{d.get('publico')}"
      narrator_perspective: "{d.get('narrador')}"
      structure_format: "{d.get('estrutura')}"
      lyrical_tone: "{d.get('tom')}"

  AUTOMATIC_INPUTS:
    arrangement_and_production_inference:
      derived FIRST from external_refs or musical_identity:
        - main_instrumentation
        - texture_and_layers
        - atmosphere_and_mix
        - tempo_and_dynamic_progression
        - relationship_between_sections
        - vocal_style_and_range
        - bass_percussion_and_groove_functions
        - characteristic_harmonies_and_voicings
        - climax_and_transitions

  OUTPUTS:
    commercial_title:
      description: "Generate a short, memorable, and impactful title, aligned with the theme and consistent with the musical aesthetic. It must sound like an official song name with emotional and commercial strength."
      requirements:
        - "1 line"
        - "High memorability"
        - "Consistency with MUSICAL IDENTITY and message"
        - "Able to function as a commercial title"

    full_lyrics:
      requirements:
        - "Structure with instrumental markings"
          reference_structure_examples:
          - "[Intro: Deep sub-bass pulse, metallic hi-hat flickers, distant vocal whispers]"
          - "[Verse 1: Strummed clean guitar, melodic bass, light drums]"
          - "[Drop: aggressive kick, industrial synth grind, side-chained pads pulsing]"
          - "[Pre-Chorus: bass and drums build, open guitar chords]"
          - "[Chorus: full band, driving rhythm guitar, atmospheric synth]"
          - "[Bridge: atmospheric piano, soft choir, rising drums]"
          - "[Outro: smooth fade-out, percussion and cavaquinho]"

        - "Progressive coherence between verses"
        - "Memorable and singable chorus"
        - "Natural alternating rhymes, avoiding weak rhymes"
        - "Possibility of simple repetition in chorus for pop usability"
        - "Balanced syllables per line"

    prompt_for_suno_5:
      description: "The prompt must be written as continuous text in 3 to 6 long sentences, highly descriptive and musically technical, following the style of the provided examples. Avoid mentioning song or artist names."
      requirements:
        - "Language: EN-US."
        - "AVOID mentioning song and artist names."
        - "WARNING! MAXIMUM of 1000 characters"
        - "Cinematic, detailed, and functional description"
        - "Mention tempo (~BPM), time signature and key if inferable"
        - "Optional harmonic progressions when characteristic of the style"
        - "Explicit and functional instrumentation, including vocals and mix"
        - "Use high-fidelity audio terminology"
        - "Describe timbres, dynamics, and emotional feeling"
        - "Climax, expansion, and layered development"
        - "Vocals described in range, timbre, and interpretation"
        - "Clear stylistic references incorporated naturally"
        - "Continuous text — no bullet points, no markers"

      formatting_example:
        style: >
          "Begin like: Brazilian romantic pop / soft rock inspired by 80s Brazilian pop."
        voice: >
          "Mention timbre, range, technique, emotion, and position in the mix."
        instrumentation: >
          "List piano, pads, guitars, strings, drums, bass, etc., with function."
        feel_and_mix: >
          "Indicate ambience, reverb, compression, stereo image, and emotional atmosphere."
        text_structure: >
          "Start with style and tempo; move to instrumentation, groove, bass, harmony;
          then vocals and mix; finish with emotional feel, climax, and impact."

  understanding:
    rule: "If something in the MUSICAL IDENTITY is vague, make coherent artistic decisions without asking for confirmation."

  output_order:
    - "# Title"
    ─────────────────────────────────────────────
    - "# Lyrics"
    ─────────────────────────────────────────────
    - "# Prompt for Suno"

"""

