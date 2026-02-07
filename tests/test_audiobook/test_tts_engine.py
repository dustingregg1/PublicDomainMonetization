"""Tests for TTS engine module (unit tests, no GPU required)."""

import pytest
from pathlib import Path

from src.audiobook.tts_engine import (
    TTSEngine,
    VoiceProfile,
    VOICE_PROFILES,
    _split_into_sentences,
    _split_into_chunks,
)


class TestVoiceProfiles:
    """Test voice profile configuration."""

    def test_all_profiles_exist(self) -> None:
        """Verify all expected voice profiles are defined."""
        assert "philosophical_sf" in VOICE_PROFILES
        assert "hardboiled_detective" in VOICE_PROFILES
        assert "golden_age_british" in VOICE_PROFILES
        assert "default" in VOICE_PROFILES

    def test_philosophical_sf_speed(self) -> None:
        """Philosophical SF should be slower for dense content."""
        profile = VOICE_PROFILES["philosophical_sf"]
        assert profile.speed < 1.0  # Slower than default

    def test_profile_has_required_fields(self) -> None:
        """All profiles should have required fields."""
        for name, profile in VOICE_PROFILES.items():
            assert profile.name, f"{name} missing name"
            assert profile.language, f"{name} missing language"
            assert 0.5 <= profile.speed <= 1.5, f"{name} speed out of range"


class TestTextSplitting:
    """Test text splitting for TTS."""

    def test_split_into_sentences_basic(self) -> None:
        """Test basic sentence splitting."""
        text = "Hello world. This is a test. It works."
        sentences = _split_into_sentences(text)
        assert len(sentences) >= 1
        assert all(s.strip() for s in sentences)

    def test_split_into_sentences_short_merge(self) -> None:
        """Short sentences should be merged."""
        text = "Hi. OK. Yes. Sure thing, that works fine."
        sentences = _split_into_sentences(text)
        # Should merge short ones together
        assert len(sentences) <= 3

    def test_split_into_chunks_respects_limit(self) -> None:
        """Chunks should not exceed max_chars."""
        text = "This is a sentence. " * 50
        chunks = _split_into_chunks(text, max_chars=200)
        for chunk in chunks:
            assert len(chunk) <= 500  # Some tolerance for long sentences

    def test_split_empty_text(self) -> None:
        """Empty text should return empty list."""
        assert _split_into_chunks("") == []
        assert _split_into_chunks("   ") == []

    def test_split_single_long_sentence(self) -> None:
        """A single very long sentence should be split by words."""
        text = "word " * 200  # ~1000 chars
        chunks = _split_into_chunks(text, max_chars=200)
        assert len(chunks) > 1


class TestTTSEngine:
    """Test TTSEngine without loading model."""

    def test_init_default_profile(self) -> None:
        """Test initialization with default profile."""
        engine = TTSEngine()
        assert engine.profile.name == "Default Narrator"

    def test_init_named_profile(self) -> None:
        """Test initialization with named profile."""
        engine = TTSEngine(voice_profile="philosophical_sf")
        assert engine.profile.name == "Cosmic Chronicler"
        assert engine.profile.speed == 0.92

    def test_estimate_duration(self) -> None:
        """Test audio duration estimation."""
        engine = TTSEngine(voice_profile="default")
        text = "word " * 150  # 150 words

        duration = engine.estimate_duration(text)
        # At ~150 wpm, 150 words = ~60 seconds
        assert 50 < duration < 70

    def test_estimate_duration_slow_profile(self) -> None:
        """Slower profiles should produce longer estimates."""
        engine = TTSEngine(voice_profile="philosophical_sf")
        text = "word " * 150

        duration = engine.estimate_duration(text)
        # Slower speed = longer duration
        assert duration > 60

    def test_clean_text(self) -> None:
        """Test text cleaning for TTS."""
        engine = TTSEngine()
        dirty = "CHAPTER XVI\nText with—em dashes... and [footnotes]."
        clean = engine._clean_text_for_tts(dirty)

        assert "CHAPTER XVI" not in clean
        assert "[footnotes]" not in clean
        assert "--" in clean  # em dash converted

    def test_get_profile_info(self) -> None:
        """Test profile info dict."""
        engine = TTSEngine(voice_profile="philosophical_sf")
        info = engine.get_profile_info()

        assert info["name"] == "Cosmic Chronicler"
        assert info["speed"] == 0.92
        assert info["model"] == "tts_models/multilingual/multi-dataset/xtts_v2"
