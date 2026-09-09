import os
import yaml
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("mmo_adapter.prompts")

class PromptManager:
    """Loads localized prompts and builds context-aware message chains for PlayerBots."""

    def __init__(self, locales_dir: str, default_lang: str = "tr"):
        self.locales_dir = locales_dir
        self.active_lang = default_lang
        self.locales: Dict[str, Dict[str, Any]] = {}
        self.load_all_locales()

    def load_all_locales(self):
        if not os.path.exists(self.locales_dir):
            logger.error(f"Locales directory does not exist: {self.locales_dir}")
            return

        for filename in os.listdir(self.locales_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                lang_code = os.path.splitext(filename)[0]
                filepath = os.path.join(self.locales_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        self.locales[lang_code] = yaml.safe_load(f)
                    logger.info(f"Loaded locale: {lang_code}")
                except Exception as e:
                    logger.error(f"Failed to load locale {filepath}: {e}")

    def set_language(self, lang_code: str):
        if lang_code in self.locales:
            self.active_lang = lang_code
        else:
            logger.warning(f"Locale {lang_code} not found, falling back to {self.active_lang}")

    def get_locale_data(self, lang_code: Optional[str] = None) -> Dict[str, Any]:
        target_lang = lang_code or self.active_lang
        return self.locales.get(target_lang, self.locales.get("tr", {}))

    def build_system_prompt(self, bot_profile: Dict[str, Any]) -> str:
        """
        Builds a rich system prompt tailored to the bot's identity and active language.
        bot_profile:
            name: str
            job: str (warrior, sura, ninja, shaman)
            level: int
            map_name: str
            hp_percent: int
            current_activity: str
            in_party: bool
            party_leader: Optional[str]
        """
        loc = self.get_locale_data()
        rules = "\n".join(f"- {r}" for r in loc.get("system_rules", []))
        
        job_key = str(bot_profile.get("job", "warrior")).lower()
        archetypes = loc.get("archetypes", {})
        arch_data = archetypes.get(job_key, archetypes.get("warrior", {}))
        
        persona_name = arch_data.get("name", job_key.title())
        persona_role = arch_data.get("role", "")
        persona_speech = arch_data.get("speech_style", "")
        examples = "\n".join(f"- {example}" for example in loc.get("style_examples", []))
        personality_names = {
            0: "istikrarli maceraci",
            1: "metin kirici",
            2: "takim arkadasi",
            3: "ekipman uzmani",
            4: "dikkatli toplayici",
            5: "tacir",
            6: "gezgin",
            7: "metin dusurucusu",
            8: "M3 dusurucusu",
            9: "M2 dusurucusu",
            10: "madalya dusurucusu",
        }
        saved_personality = bot_profile.get("personality") or personality_names.get(
            bot_profile.get("personality_id", 0), "istikrarli maceraci"
        )

        prompt = f"""[METIN2 PLAYERBOT IDENTITY]
Character Name: {bot_profile.get('name', 'PlayerBot')}
Class / Job: {persona_name} (Level {bot_profile.get('level', 1)})
Location: {bot_profile.get('map_name', 'Bokjung')}
Health: {bot_profile.get('hp_percent', 100)}%
Current Status: {bot_profile.get('current_activity', 'Kasilma')}
Party Status: {'In Party with ' + str(bot_profile.get('party_leader')) if bot_profile.get('in_party') else 'Solo'}

Role Background: {persona_role}
Speech Tone & Style: {persona_speech}
Saved Personality: {saved_personality}
Backstory: {bot_profile.get('backstory') or 'Not specified'}
Speech Quirks: {bot_profile.get('speech_quirks') or 'None'}
Typing realism: Make occasional small natural typos only if the profile allows it; do not make every message sloppy.

BEHAVIORAL RULES:
{rules}

ORIGINAL STYLE EXAMPLES (do not copy verbatim; use only as tone guidance):
{examples}

SON GOREV:
Oyuncunun son mesajina dogrudan cevap ver. Cevabi sadece ASCII Turkce yaz ve Lehce kelime veya Lehce kisaltma
kullanma; `BK` beceri kitabi demektir ve Lehce `KU` kullanma. En fazla
iki kisa cumle kullan. Dusunce sureci, analiz, Ingilizce, JSON, markdown veya cevap
etiketi yazma. Oyuncu ne istedigini soruyorsa kisa ve dogal bir cevap ver; emin
degilsen "Su an bilmiyorum, birazdan bakarim." de. Bir oyun aksiyonu gerekiyorsa
uygun araci kullan ve varsa mesaj alanina ayni kurallara uyan kisa Turkce metin koy.
"""
        return prompt

    def get_farewell_text(self, lang_code: Optional[str] = None) -> str:
        loc = self.get_locale_data(lang_code)
        farewells = loc.get("farewells", ["Gorusuruz!"])
        import random
        return random.choice(farewells)

    def get_busy_reply_text(self, lang_code: Optional[str] = None) -> str:
        loc = self.get_locale_data(lang_code)
        busy = loc.get("busy_replies", ["Su an mesgulum, sonra yazisalim."])
        import random
        return random.choice(busy)
