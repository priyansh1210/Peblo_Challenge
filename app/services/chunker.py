import re


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Split text into chunks based on sentence boundaries with overlap."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        word_count = len(sentence.split())

        if current_length + word_count > chunk_size and current_chunk:
            chunk_text_str = " ".join(current_chunk)
            chunks.append(chunk_text_str)

            # Keep overlap words from the end
            overlap_words = []
            overlap_count = 0
            for s in reversed(current_chunk):
                s_words = len(s.split())
                if overlap_count + s_words > overlap:
                    break
                overlap_words.insert(0, s)
                overlap_count += s_words

            current_chunk = overlap_words
            current_length = overlap_count

        current_chunk.append(sentence)
        current_length += word_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def detect_topics(text: str) -> str | None:
    """Simple topic detection from chunk content."""
    topic_keywords = {
        "Shapes": ["triangle", "circle", "square", "rectangle", "shape", "sides"],
        "Numbers": ["number", "count", "counting", "digit", "addition", "subtraction"],
        "Grammar": ["noun", "verb", "adjective", "sentence", "tense", "pronoun"],
        "Vocabulary": ["word", "meaning", "synonym", "antonym", "vocabulary"],
        "Plants": ["plant", "leaf", "root", "stem", "flower", "seed", "photosynthesis"],
        "Animals": ["animal", "mammal", "reptile", "bird", "fish", "habitat"],
    }

    text_lower = text.lower()
    best_topic = None
    best_count = 0

    for topic, keywords in topic_keywords.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > best_count:
            best_count = count
            best_topic = topic

    return best_topic if best_count >= 2 else None
