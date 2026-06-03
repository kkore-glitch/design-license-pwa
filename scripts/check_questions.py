#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_JSON = ROOT / "src" / "data" / "questions.json"


def normalize_key(text: str) -> str:
    return "".join(text.split()).replace("，", ",").replace("。", ".")


def has_cjk_split_space(text: str) -> bool:
    import re

    return bool(re.search(r"[\u4e00-\u9fff]\s+[\u4e00-\u9fff]", text))


def main() -> None:
    payload = json.loads(QUESTIONS_JSON.read_text(encoding="utf-8"))
    questions = payload["questions"]
    errors = []
    seen = Counter(normalize_key(item["question"]) for item in questions)

    for item in questions:
        if len(item["choices"]) != 4:
            errors.append(f"{item['id']} choices != 4")
        if item["answerIndex"] not in [0, 1, 2, 3]:
            errors.append(f"{item['id']} invalid answerIndex")
        if not item.get("answerIndices") or any(index not in [0, 1, 2, 3] for index in item["answerIndices"]):
            errors.append(f"{item['id']} invalid answerIndices")
        if len(set(item.get("answerIndices", []))) != len(item.get("answerIndices", [])):
            errors.append(f"{item['id']} repeated answerIndices")
        if not item["question"].strip():
            errors.append(f"{item['id']} empty question")
        if any(not choice.strip() for choice in item["choices"]):
            errors.append(f"{item['id']} empty choice")
        if has_cjk_split_space(item["question"]):
            errors.append(f"{item['id']} CJK split space in question")
        for choice in item["choices"]:
            if has_cjk_split_space(choice):
                errors.append(f"{item['id']} CJK split space in choice")

    duplicates = [key for key, count in seen.items() if count > 1]
    chapter_counts = Counter(item["chapter"] for item in questions)
    image_count = sum(1 for item in questions if item["needsImage"])
    image_refs = {item["image"] for item in questions if item.get("image")}
    image_files = {str(path.relative_to(ROOT)) for path in (ROOT / "assets" / "questions").glob("*.png")}
    sim_ready = sum(1 for item in questions if not item["needsImage"])
    multi_count = sum(1 for item in questions if len(item["answerIndices"]) > 1)

    for image in image_refs:
        if not (ROOT / image).exists():
            errors.append(f"missing image file {image}")
    for image in sorted(image_files - image_refs):
        errors.append(f"unreferenced image file {image}")

    print(f"questionCount={len(questions)}")
    print(f"simulationReady={sim_ready}")
    print(f"needsImage={image_count}")
    print(f"imageQuestions={len(image_refs)}")
    print(f"multiSelect={multi_count}")
    print("chapterCounts=" + json.dumps(dict(chapter_counts), ensure_ascii=False))
    print(f"duplicateQuestionTexts={len(duplicates)}")

    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    if len(questions) < 650:
        raise SystemExit("Expected at least 650 usable questions from the official PDF")
    if sim_ready < 80:
        raise SystemExit("Expected at least 80 simulation-ready questions")


if __name__ == "__main__":
    main()
