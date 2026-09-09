import os
import pytest
from llm.prompts import PromptManager
from core.text import (
    add_realistic_typo,
    has_bad_turkish_pattern,
    limit_profanity,
    sanitize_game_text,
)

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "locales")

def test_locales_load_successfully():
    pm = PromptManager(locales_dir=LOCALES_DIR, default_lang="tr")
    assert "tr" in pm.locales
    assert "en" in pm.locales
    assert pm.active_lang == "tr"

def test_language_switch():
    pm = PromptManager(locales_dir=LOCALES_DIR, default_lang="tr")
    pm.set_language("en")
    assert pm.active_lang == "en"
    
    # Check that system prompt uses English archetype
    prompt = pm.build_system_prompt({"job": "warrior", "name": "Conan", "level": 45})
    assert "Warrior" in prompt
    assert "Conan" in prompt
    assert "Level 45" in prompt

def test_turkish_system_prompt():
    pm = PromptManager(locales_dir=LOCALES_DIR, default_lang="tr")
    prompt = pm.build_system_prompt({"job": "sura", "name": "KaraBuyu99", "level": 65})
    assert "Sura" in prompt
    assert "KaraBuyu99" in prompt
    assert "Level 65" in prompt
    assert "PlayerBot" in prompt

def test_ascii_character_safety():
    pm = PromptManager(locales_dir=LOCALES_DIR, default_lang="tr")
    tr_data = pm.get_locale_data("tr")
    # Verify archetypes and system rules exist
    assert "archetypes" in tr_data
    assert "warrior" in tr_data["archetypes"]
    assert "actions" in tr_data


def test_game_text_is_ascii_safe_and_uses_legacy_turkish_transliteration():
    text = sanitize_game_text("Şöyle güzel: İğne, çadır, Ümit — tamam 🙂")
    assert text == "Soyle guzel: Igne, cadir, Umit  tamam "
    assert text.isascii()


def test_typo_injection_is_optional_and_ascii_safe():
    text = add_realistic_typo("selam kankam", probability=1.0)
    assert text.isascii()
    assert text != "selam kankam"


def test_profanity_is_limited_per_reply():
    text = limit_profanity("amk siktir, bu boktan is aq")
    assert text == "amk of, bu sacma is ya"


def test_bad_turkish_pattern_is_detected():
    assert has_bad_turkish_pattern("slotlarim basini cozuyorum")
    assert not has_bad_turkish_pattern("Su an slot kesiyorum")


def test_saved_personality_fields_are_included_in_prompt():
    pm = PromptManager(locales_dir=LOCALES_DIR, default_lang="tr")
    prompt = pm.build_system_prompt({
        "name": "KaraKilic",
        "job": "warrior",
        "personality": "Cekingen ama yardimsever",
        "backstory": "Eski loncasini ariyor",
        "speech_quirks": "Kisa yazar, bazen kanka der",
    })
    assert "Cekingen ama yardimsever" in prompt
    assert "Eski loncasini ariyor" in prompt
    assert "Kisa yazar, bazen kanka der" in prompt
    assert "ORIGINAL STYLE EXAMPLES" in prompt


def test_numeric_saved_personality_is_named_in_prompt():
    pm = PromptManager(locales_dir=LOCALES_DIR, default_lang="tr")
    prompt = pm.build_system_prompt({"name": "Gezgin", "personality_id": 6})
    assert "gezgin" in prompt
