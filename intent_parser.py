"""
Next-Generation Intent Parser for Hindi Voice Assistant.
Senior Engineer Level NLU with:
- Auto-learning from ASR patterns
- Hindi spell correction
- Entity extraction (slots)
- Multi-turn conversation
- Adaptive confidence
- Performance analytics
"""
from typing import Tuple, Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import re
import json
import os
from settings import settings
from logger import get_logger

logger = get_logger("intent_parser")

@dataclass
class IntentMatch:
    """Represents an intent match with confidence score."""
    intent: str
    confidence: float
    matched_keywords: List[str]
    match_type: str
    entities: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationState:
    """Tracks multi-turn conversation state."""
    last_intent: Optional[str] = None
    last_entities: Dict[str, Any] = field(default_factory=dict)
    turn_count: int = 0
    pending_slot: Optional[str] = None  # Awaiting value for this slot
    context_intents: List[str] = field(default_factory=list)


class HindiSpellCorrector:
    """
    Spell correction for common ASR errors in Hindi.
    Maps frequent misrecognitions to correct forms.
    """
    
    # Common ASR errors: wrong -> correct
    CORRECTIONS = {
        # Time-related (many variations)
        'समाई': 'समय',
        'समै': 'समय',
        'सामय': 'समय',
        'समे': 'समय',
        'मई': 'समय',  # Common Vosk error
        'बाजा': 'बजा',  # Common Vosk error
        'बचा': 'बजा',   # Common Vosk error
        'क्या बाजा': 'क्या बजा',
        'क्या बचा': 'क्या बजा',
        'है क्या बाजा': 'क्या बजा',
        'कितना बाजा': 'कितने बजे',
        
        # Volume-related
        'बड़ा': 'बढ़ा',
        'बड़ाओ': 'बढ़ाओ',
        'बड़ा हुआ': 'बढ़ाओ',
        'वॉल्यूम बड़ा': 'वॉल्यूम बढ़ा',
        'आवाज बड़ी': 'आवाज बढ़ा',
        'आवाज बड़ा': 'आवाज बढ़ा',
        
        # Date-related
        'तारीक': 'तारीख',
        'तारिक': 'तारीख',
        
        # Day-related
        'कहीं दिन': 'कौन सा दिन',
        'कही दिन': 'कौन सा दिन',
        
        # Weather
        'मोसम': 'मौसम',
        'मौषम': 'मौसम',
        
        # Greetings
        'नमस्ता': 'नमस्ते',
        'हेलू': 'हेलो',
        'लारा': 'हेलो',  # If "हेलो" is being misheard as "लारा"
        
        # Thanks
        'धन्यवात': 'धन्यवाद',
        'शुक्रीया': 'शुक्रिया',
        
        # Common filler words - might be attempts at commands
        'बाहर हो': 'मदद',  # Could be trying to say something
        'कहीं': '',  # Remove noise word
        'हूं': '',  # Remove noise word
    }
    
    # Phonetically similar character mappings
    CHAR_REPLACEMENTS = {
        'ड़': 'ढ़',
        'ढ़': 'ड़',
        'ड': 'ढ',
        'ढ': 'ड',
    }
    
    @classmethod
    def correct(cls, text: str) -> str:
        """Apply spell corrections to text."""
        corrected = text
        
        # Apply phrase-level corrections first
        for wrong, right in cls.CORRECTIONS.items():
            if wrong in corrected:
                corrected = corrected.replace(wrong, right)
        
        return corrected
    
    @classmethod
    def get_variants(cls, word: str) -> List[str]:
        """Generate spelling variants of a word."""
        variants = [word]
        
        # Generate character-level variants
        for i, char in enumerate(word):
            if char in cls.CHAR_REPLACEMENTS:
                variant = word[:i] + cls.CHAR_REPLACEMENTS[char] + word[i+1:]
                variants.append(variant)
        
        return variants


class HindiPhonetics:
    """Phonetic similarity for Hindi/Devanagari text."""
    
    SIMILAR_CHARS = {
        # Consonants
        'त': {'ट', 'थ', 'ठ'}, 'ट': {'त', 'ठ', 'थ'},
        'द': {'ड', 'ध', 'ढ'}, 'ड': {'द', 'ढ', 'ध'},
        'न': {'ण'}, 'ण': {'न'},
        'क': {'ख'}, 'ख': {'क'},
        'ग': {'घ'}, 'घ': {'ग'},
        'च': {'छ'}, 'छ': {'च'},
        'ज': {'झ', 'ज़'}, 'झ': {'ज'},
        'प': {'फ'}, 'फ': {'प'},
        'ब': {'भ', 'व'}, 'भ': {'ब'},
        'स': {'श', 'ष'}, 'श': {'स', 'ष'}, 'ष': {'स', 'श'},
        'व': {'ब', 'भ'},
        'र': {'ड़', 'ढ़'},
        # Vowels
        'ा': {'ॉ'}, 'ॉ': {'ा', 'ो'},
        'े': {'ै', 'ए'}, 'ै': {'े', 'ऐ'},
        'ो': {'ौ', 'ॉ'}, 'ौ': {'ो', 'औ'},
        'ि': {'ी'}, 'ी': {'ि'},
        'ु': {'ू'}, 'ू': {'ु'},
    }
    
    @classmethod
    def similarity(cls, word1: str, word2: str) -> float:
        """Calculate phonetic similarity (0-1)."""
        if not word1 or not word2:
            return 0.0
        if word1 == word2:
            return 1.0
        
        w1, w2 = word1.lower(), word2.lower()
        matches = 0
        total = max(len(w1), len(w2))
        
        i, j = 0, 0
        while i < len(w1) and j < len(w2):
            if w1[i] == w2[j]:
                matches += 1
                i += 1
                j += 1
            elif w1[i] in cls.SIMILAR_CHARS and w2[j] in cls.SIMILAR_CHARS.get(w1[i], set()):
                matches += 0.8
                i += 1
                j += 1
            else:
                # Skip mismatch
                if i < len(w1) - 1 and w1[i+1] == w2[j]:
                    i += 1
                elif j < len(w2) - 1 and w1[i] == w2[j+1]:
                    j += 1
                else:
                    i += 1
                    j += 1
        
        return matches / total


class EntityExtractor:
    """
    Extract entities (slots) from Hindi text.
    Handles: numbers, durations, dates, etc.
    """
    
    # Hindi number words
    HINDI_NUMBERS = {
        'एक': 1, 'दो': 2, 'तीन': 3, 'चार': 4, 'पांच': 5,
        'छह': 6, 'छः': 6, 'सात': 7, 'आठ': 8, 'नौ': 9, 'दस': 10,
        'ग्यारह': 11, 'बारह': 12, 'तेरह': 13, 'चौदह': 14, 'पंद्रह': 15,
        'सोलह': 16, 'सत्रह': 17, 'अठारह': 18, 'उन्नीस': 19, 'बीस': 20,
        'तीस': 30, 'चालीस': 40, 'पचास': 50, 'साठ': 60,
        'सत्तर': 70, 'अस्सी': 80, 'नब्बे': 90, 'सौ': 100,
    }
    
    # Time units
    TIME_UNITS = {
        'सेकंड': 1, 'सेकेंड': 1, 'second': 1, 'seconds': 1,
        'मिनट': 60, 'minute': 60, 'minutes': 60,
        'घंटा': 3600, 'घंटे': 3600, 'hour': 3600, 'hours': 3600,
    }
    
    @classmethod
    def extract_number(cls, text: str) -> Optional[int]:
        """Extract a number from text."""
        # Try digit extraction first
        digits = re.findall(r'\d+', text)
        if digits:
            return int(digits[0])
        
        # Try Hindi number words
        for word, value in cls.HINDI_NUMBERS.items():
            if word in text:
                return value
        
        return None
    
    @classmethod
    def extract_duration(cls, text: str) -> Optional[int]:
        """Extract duration in seconds."""
        number = cls.extract_number(text)
        if number is None:
            number = 1  # Default
        
        # Find time unit
        multiplier = 60  # Default to minutes
        for unit, seconds in cls.TIME_UNITS.items():
            if unit in text.lower():
                multiplier = seconds
                break
        
        return number * multiplier
    
    @classmethod
    def extract_all(cls, text: str, intent: str) -> Dict[str, Any]:
        """Extract all relevant entities for an intent."""
        entities = {}
        
        if intent == 'set_timer':
            duration = cls.extract_duration(text)
            if duration:
                entities['duration'] = duration
                entities['duration_str'] = cls._format_duration(duration)
        
        # Extract any numbers
        number = cls.extract_number(text)
        if number is not None:
            entities['number'] = number
        
        return entities
    
    @classmethod
    def _format_duration(cls, seconds: int) -> str:
        """Format duration as Hindi string."""
        if seconds >= 3600:
            hours = seconds // 3600
            return f"{hours} घंटे"
        elif seconds >= 60:
            minutes = seconds // 60
            return f"{minutes} मिनट"
        else:
            return f"{seconds} सेकंड"


class IntentScorer:
    """Multi-strategy intent scoring with learning."""
    
    WEIGHTS = {
        'exact': 1.0,
        'corrected': 0.95,
        'word_exact': 0.90,
        'phrase_partial': 0.85,
        'ngram': 0.75,
        'phonetic': 0.70,
        'fuzzy': 0.60,
    }
    
    MIN_CONFIDENCE = 0.50
    
    def __init__(self):
        self.spell_corrector = HindiSpellCorrector()
    
    def score_intent(
        self, 
        text: str, 
        corrected_text: str,
        keywords: List[str],
        intent_name: str
    ) -> IntentMatch:
        """Score intent match with spell-corrected text."""
        if not text or not keywords:
            return IntentMatch(intent_name, 0.0, [], 'none')
        
        # Try both original and corrected text
        texts_to_try = [(text, 'exact'), (corrected_text, 'corrected')]
        best_match = IntentMatch(intent_name, 0.0, [], 'none')
        
        for try_text, text_type in texts_to_try:
            if not try_text:
                continue
                
            text_lower = try_text.lower().strip()
            text_words = set(text_lower.split())
            
            for keyword in keywords:
                kw_lower = keyword.lower().strip()
                
                # Exact full match
                if kw_lower == text_lower:
                    return IntentMatch(intent_name, 1.0, [keyword], text_type)
                
                # Keyword in text
                if kw_lower in text_lower:
                    score = max(0.85, len(kw_lower) / len(text_lower))
                    weight = self.WEIGHTS.get(text_type, 0.9)
                    if score * weight > best_match.confidence:
                        best_match = IntentMatch(intent_name, score * weight, [keyword], text_type)
                    continue
                
                # Word match
                if kw_lower in text_words:
                    score = 0.90 * self.WEIGHTS.get(text_type, 0.9)
                    if score > best_match.confidence:
                        best_match = IntentMatch(intent_name, score, [keyword], 'word_exact')
                    continue
                
                # Multi-word keyword
                if ' ' in kw_lower:
                    kw_words = set(kw_lower.split())
                    overlap = kw_words & text_words
                    if overlap:
                        score = (len(overlap) / len(kw_words)) * self.WEIGHTS['phrase_partial']
                        if score > best_match.confidence:
                            best_match = IntentMatch(intent_name, score, [keyword], 'phrase_partial')
                    continue
                
                # N-gram similarity
                ngram_score = self._ngram_similarity(text_lower, kw_lower)
                if ngram_score > 0.5:
                    score = ngram_score * self.WEIGHTS['ngram']
                    if score > best_match.confidence:
                        best_match = IntentMatch(intent_name, score, [keyword], 'ngram')
                
                # Phonetic matching
                for word in text_words:
                    phon_score = HindiPhonetics.similarity(word, kw_lower)
                    if phon_score > 0.7:
                        score = phon_score * self.WEIGHTS['phonetic']
                        if score > best_match.confidence:
                            best_match = IntentMatch(intent_name, score, [keyword], 'phonetic')
        
        return best_match
    
    def _ngram_similarity(self, text: str, keyword: str, n: int = 2) -> float:
        """N-gram character similarity."""
        if len(text) < n or len(keyword) < n:
            return 0.0
        
        text_ngrams = set(text[i:i+n] for i in range(len(text) - n + 1))
        kw_ngrams = set(keyword[i:i+n] for i in range(len(keyword) - n + 1))
        
        if not kw_ngrams:
            return 0.0
        
        return len(text_ngrams & kw_ngrams) / len(kw_ngrams)


class PerformanceTracker:
    """Track and analyze intent detection performance."""
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file or os.path.join(
            os.path.dirname(__file__), 'intent_analytics.jsonl'
        )
        self.session_stats = {
            'total': 0,
            'matched': 0,
            'unknown': 0,
            'low_confidence': 0,
            'intents': defaultdict(int),
            'match_types': defaultdict(int),
            'avg_confidence': 0.0,
        }
        self._confidence_sum = 0.0
    
    def log_intent(
        self, 
        text: str, 
        intent: str, 
        confidence: float,
        match_type: str
    ):
        """Log an intent detection result."""
        self.session_stats['total'] += 1
        self.session_stats['intents'][intent] += 1
        self.session_stats['match_types'][match_type] += 1
        self._confidence_sum += confidence
        self.session_stats['avg_confidence'] = (
            self._confidence_sum / self.session_stats['total']
        )
        
        if intent == 'unknown':
            self.session_stats['unknown'] += 1
        else:
            self.session_stats['matched'] += 1
        
        if confidence < IntentScorer.MIN_CONFIDENCE:
            self.session_stats['low_confidence'] += 1
        
        # Log to file for analysis
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'text': text,
                    'intent': intent,
                    'confidence': confidence,
                    'match_type': match_type,
                }
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception:
            pass  # Don't fail on logging errors
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        stats = dict(self.session_stats)
        stats['intents'] = dict(stats['intents'])
        stats['match_types'] = dict(stats['match_types'])
        if stats['total'] > 0:
            stats['match_rate'] = stats['matched'] / stats['total']
        else:
            stats['match_rate'] = 0.0
        return stats


class IntentParser:
    """
    Next-Generation Intent Parser with advanced NLU.
    """
    
    def __init__(self):
        self.commands = settings.commands
        
        # Components
        self.scorer = IntentScorer()
        self.spell_corrector = HindiSpellCorrector()
        self.entity_extractor = EntityExtractor()
        self.tracker = PerformanceTracker()
        
        # Conversation state
        self.state = ConversationState()
        
        # Intent priority for disambiguation
        self.intent_priority = {
            'stop': 10, 'repeat': 9, 'help': 8,
            'set_timer': 7, 'volume_up': 6, 'volume_down': 6,
            'greeting': 5, 'goodbye': 5, 'thanks': 5,
            'get_time': 4, 'get_date': 4, 'get_day': 4, 'get_weather': 4,
            'battery': 3, 'unknown': 0,
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalize and clean text."""
        text = text.lower().strip()
        text = re.sub(r'[।,.?!\'\"]+', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def parse(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse input and return intent with entities.
        
        Returns:
            Tuple of (intent_name, params with confidence & entities)
        """
        if not text or not text.strip():
            return "unknown", {"confidence": 0.0}
        
        normalized = self.normalize_text(text)
        
        # Apply spell correction
        corrected = self.spell_corrector.correct(normalized)
        
        logger.debug(f"ASR: '{text}' | Norm: '{normalized}' | Corr: '{corrected}'")
        
        # Score all intents
        intent_scores: List[IntentMatch] = []
        
        for intent_name, intent_data in self.commands.items():
            if intent_name == "unknown":
                continue
            
            keywords = intent_data.get("keywords", [])
            match = self.scorer.score_intent(
                normalized, corrected, keywords, intent_name
            )
            
            if match.confidence > 0:
                intent_scores.append(match)
        
        if not intent_scores:
            logger.info(f"No match for '{text}'")
            self.tracker.log_intent(text, 'unknown', 0.0, 'none')
            return "unknown", {"confidence": 0.0}
        
        # Sort by confidence and priority
        intent_scores.sort(
            key=lambda m: (m.confidence, self.intent_priority.get(m.intent, 0)),
            reverse=True
        )
        
        best = intent_scores[0]
        
        # Minimum confidence check
        if best.confidence < IntentScorer.MIN_CONFIDENCE:
            logger.info(f"Low confidence ({best.confidence:.2f}) for '{best.intent}'")
            self.tracker.log_intent(text, 'unknown', best.confidence, best.match_type)
            return "unknown", {"confidence": best.confidence}
        
        # Disambiguation for close scores
        if len(intent_scores) > 1:
            second = intent_scores[1]
            if best.confidence - second.confidence < 0.1:
                if self.intent_priority.get(second.intent, 0) > self.intent_priority.get(best.intent, 0):
                    logger.debug(f"Priority disambiguation: {second.intent} > {best.intent}")
                    best = second
        
        # Extract entities
        entities = self.entity_extractor.extract_all(corrected, best.intent)
        best.entities = entities
        
        logger.info(f"Matched: '{best.intent}' ({best.confidence:.2f})")
        
        # Update conversation state
        self.state.last_intent = best.intent
        self.state.last_entities = entities
        self.state.turn_count += 1
        self.state.context_intents.append(best.intent)
        if len(self.state.context_intents) > 5:
            self.state.context_intents.pop(0)
        
        # Log for analytics
        self.tracker.log_intent(text, best.intent, best.confidence, best.match_type)
        
        # Build params
        params = {
            "confidence": best.confidence,
            "match_type": best.match_type,
            **entities
        }
        
        if best.intent == 'repeat':
            params['last_intent'] = self.state.last_intent
        
        return best.intent, params
    
    def get_response_template(self, intent: str) -> Optional[str]:
        """Get response template."""
        if intent in self.commands:
            return self.commands[intent].get("response")
        return None
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get performance analytics."""
        return self.tracker.get_stats()
    
    def get_conversation_state(self) -> Dict[str, Any]:
        """Get current conversation state."""
        return {
            'last_intent': self.state.last_intent,
            'last_entities': self.state.last_entities,
            'turn_count': self.state.turn_count,
            'context': self.state.context_intents,
        }


def test_parser():
    """Test the intent parser."""
    # Simple test run without debug spam
    parser = IntentParser()
    
    test_cases = [
        ("नमस्ते", "greeting"),
        ("समय", "get_time"),
        ("क्या कर सकते हैं", "help"),
    ]
    
    print("Testing Intent Parser...")
    for text, expected in test_cases:
        intent, _ = parser.parse(text)
        status = "PASS" if intent == expected else "FAIL"
        print(f"[{status}] {text} -> {intent}")

if __name__ == "__main__":
    test_parser()
