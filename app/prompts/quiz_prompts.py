def build_quiz_prompt(context: str, num_questions: int, question_types: list[str], difficulty: str, grade: int | None = None) -> str:
    grade_info = f"These questions are for Grade {grade} students." if grade else ""

    type_instructions = []
    if "mcq" in question_types:
        type_instructions.append(
            '- MCQ: Include "type": "mcq", "options" (exactly 4 choices as a list), and "correct_answer" (must be one of the options)'
        )
    if "true_false" in question_types:
        type_instructions.append(
            '- True/False: Include "type": "true_false", "options": ["True", "False"], and "correct_answer" ("True" or "False")'
        )
    if "fill_blank" in question_types:
        type_instructions.append(
            '- Fill in the blank: Include "type": "fill_blank", "options": null, and "correct_answer" (the word/phrase that fills the blank). The question_text MUST contain "___" where the blank is.'
        )

    types_str = "\n".join(type_instructions)

    return f"""You are an expert educational content creator. Generate exactly {num_questions} quiz questions from the following educational content.

{grade_info}

Difficulty level: {difficulty}
- easy: Simple recall questions, basic facts
- medium: Understanding and application questions
- hard: Analysis, comparison, and critical thinking questions

Question types to generate (mix them evenly):
{types_str}

CONTENT:
\"\"\"
{context}
\"\"\"

IMPORTANT RULES:
1. Questions MUST be directly based on the provided content only
2. Each question must be clear, unambiguous, and age-appropriate
3. For MCQ, all 4 options must be plausible but only one correct
4. Provide a brief explanation for each answer
5. Return ONLY a valid JSON array, no other text. Do NOT include any trailing commas. Keep strings on single lines.

Return a JSON array with this exact structure:
[
  {{
    "question_text": "...",
    "type": "mcq|true_false|fill_blank",
    "options": ["A", "B", "C", "D"] or ["True", "False"] or null,
    "correct_answer": "...",
    "explanation": "...",
    "difficulty": "{difficulty}"
  }}
]"""


def build_validation_prompt(question_text: str, question_type: str, options: list | None, correct_answer: str) -> str:
    return f"""Evaluate this quiz question for quality on a scale of 0.0 to 1.0.

Question: {question_text}
Type: {question_type}
Options: {options}
Correct Answer: {correct_answer}

Rate on these criteria:
1. Clarity: Is the question clear and unambiguous?
2. Correctness: Is the stated correct answer actually correct?
3. Difficulty appropriateness: Is it well-calibrated?
4. Educational value: Does it test meaningful understanding?

Return ONLY a JSON object:
{{"quality_score": 0.0-1.0, "feedback": "brief explanation"}}"""
