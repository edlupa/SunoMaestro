import json
import os
import streamlit as st

class SunoMaestroCore:
    def __init__(self, base_path):
        self.base_path = base_path
        self.dataset_dir = os.path.join(self.base_path, "dataset")
        # Metadados dos arquivos
        self.arquivos_map = {
            "hierarquia": "01_genero_ritmo.json", 
            "tipo_de_gravacao": "02_tipo_de_gravacao.json",
            "influencia_estetica": "03_influencia_estetica.json", 
            "vibe_emocional": "04_vibe_emocional.json",
            "publico": "05_publico_alvo.json", 
            "tom": "06_tom_lirico.json",
            "narrador": "07_narrador.json",
            "metatags": "08_metatags_musicais.json"
        }
        self.dados = self._load_data()

    def _load_data(self):
        """Carrega os dados usando o cache do Streamlit."""
        return load_dataset_cached(self.dataset_dir, self.arquivos_map)

    def gerar_prompt(self, campos):
        # Normalização dos campos para evitar None
        d = {}
        for k, v in campos.items():
            if isinstance(v, list):
                val = ", ".join(filter(None, v))
                d[k] = val if val.strip() else "AUTOMATIC_INPUT"
            else:
                val = str(v).strip() if v else ""
                d[k] = val if val else "AUTOMATIC_INPUT"

        # Template do Prompt
        return f"""ROLE: Composer, arranger, lyricist, and music producer who creates commercially viable songs with realistic instrumentation and writes Suno 5.0–compatible prompts; prioritizes musical identity and functional audio description over poetic abstraction, infers missing details consistently, and structures outputs for real-world mixability and singability.

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
      purpose: "Translate MUSICAL_IDENTITY into practical production decisions."
      rule: "When conflicts occur, external_refs take precedence over style, which takes precedence over genre. Infer sonic characteristics, not names."
      derivation_priority: 
        - external_refs
        - specific_style
        - primary_genre
      derive_items:
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
      description: Generate a short, memorable, and impactful title, aligned with the theme and consistent with the musical aesthetic. It must sound like an official song name with emotional and commercial strength.
      requirements:
        - 1 line
        - High memorability
        - Consistency with MUSICAL IDENTITY and core_message
        - Avoid generic titles that could apply to any song
        - Should hint at the lyrical theme or emotional essence without becoming descriptive
        - Able to function as a commercial title

    full_lyrics:
      requirements:
        - Structure with instrumental markings placed before each section
        
          instrumental_markings_rules:
          - preferred 9–12 words, max 16 only when essential for audio clarity
          - max 3 instrument sources + 1 processing descriptor
          - must describe real, playable or mixable audio
          - Allowed: musical instruments, percussion and rhythmic textures, audio processing, ambient textures derived from real sources
          - Forbidden: abstract metaphors or images that do not correspond to real sonic sources; visual or cinematic elements that cannot exist as literal audio; conceptual artifacts
          - Priority: clarity and playability of musical elements is more important than poetic imagery in instrumental tags.
                  
          reference_structure_examples:
          - [Intro: Deep sub-bass pulse, metallic hi-hat flickers, distant vocal whispers]
          - [Verse 1: Strummed clean guitar, melodic bass, light drums]
          - [Drop: aggressive kick, industrial synth grind, side-chained pads pulsing]
          - [Pre-Chorus: bass and drums build, open guitar chords]
          - [Chorus: full band, driving rhythm guitar]
          - [Bridge: atmospheric piano, soft choir, rising drums]
          - [Outro: smooth fade-out, percussion and cavaquinho]
          
        - Memorable and singable chorus with possible repetition
        - Alternating rhyme patterns (ABAB or AABB); exceptions allowed only if rhyme weakens semantic clarity
        - Similar syllable count between corresponding lines (variation ideally ≤ 20%)
        - Progressive narrative coherence across verses

    prompt_for_suno_5:
      requirements:
        - Language: EN-US.
        - Continuous text only — no bullet points or markers.
        - The prompt must be written as 3 to 6 long sentences.
        - WARNING! MAX 1000 characters; if exceeded, compress adjectives and adverbs, never removing instrumentation or emotional intent.
        - MUSICAL IDENTITY overrides inferred conventions when conflict occurs.
        - Cinematic, detailed, and functional description.
        - Cinematic refers to emotional dynamics expressed through sound evolution, not imagery.”
        - Stylistic references must describe sonic characteristics, never explicit names.
        - Tempo (~BPM), time signature and key: infer from MUSICAL IDENTITY; if key unclear, deduce from primary genre and emotional vibe.
        - Optional harmonic progressions when characteristic of style.
        - Explicit instrumentation with functional role, including vocals and mix position.
        - Vocals described with range, timbre, interpretation, and mix placement.
        - High-fidelity audio terminology for timbre, dynamics, ambience, stereo field, and processing.
        - Climax, expansion, and layered evolution must be expressed through dynamic intensity,
          instrumentation density, and progressive textural buildup in arrangement and mix.
        - AVOID mentioning song and artist names.

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

  UNDERSTANDING:
  rule: "If MUSICAL IDENTITY attributes are vague or incomplete, infer missing musical details using consistency with stated emotional meaning and recording aesthetics, without contradicting explicit user intent."

  OUTPUT ORDER:
    note: "Do not add explanations, comments, or extra text beyond specified headers."
    order:
      - "# Title"
      - "─────────────────────────────────────────────"
      - "# Lyrics"
      - "─────────────────────────────────────────────"
      - "# Prompt for Suno"
"""

@st.cache_data
def load_dataset_cached(dataset_dir, arquivos_map):
    """Função isolada para permitir cache correto do Streamlit."""
    dados = {}
    for key, filename in arquivos_map.items():
        filepath = os.path.join(dataset_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                dados[key] = json.load(f)
        except FileNotFoundError:
            dados[key] = {}
            # Opcional: st.warning(f"Arquivo não encontrado: {filename}")
        except json.JSONDecodeError:
            dados[key] = {}
            # Opcional: st.error(f"Erro ao ler JSON: {filename}")
    return dados