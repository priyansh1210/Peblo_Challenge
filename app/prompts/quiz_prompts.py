def build_quiz_prompt(context: str, num_questions: int, question_types: list[str], difficulty: str, grade: int | None = None) -> str:
    grade_info = f" for Grade {grade} students" if grade else ""

    type_list = ", ".join(question_types)

    return f"""Generate {num_questions} {difficulty} quiz questions{grade_info} from this content. Mix these types: {type_list}.

Content:
{context}

Rules:
- MCQ: 4 options with FULL answer text (not just letters), correct_answer must match one option exactly
- true_false: options ["True", "False"], correct_answer is "True" or "False"
- fill_blank: question_text must have "___", options is null

Return ONLY a JSON array like this:
[
  {{"question_text": "How many sides does a triangle have?", "type": "mcq", "options": ["2 sides", "3 sides", "4 sides", "5 sides"], "correct_answer": "3 sides", "explanation": "A triangle has 3 sides.", "difficulty": "{difficulty}"}},
  {{"question_text": "A square has four equal sides.", "type": "true_false", "options": ["True", "False"], "correct_answer": "True", "explanation": "A square has four equal sides by definition.", "difficulty": "{difficulty}"}},
  {{"question_text": "5 + 3 = ___", "type": "fill_blank", "options": null, "correct_answer": "8", "explanation": "5 plus 3 equals 8.", "difficulty": "{difficulty}"}}
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
