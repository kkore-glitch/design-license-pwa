#!/usr/bin/env python3
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "src" / "data"
ACADEMIC_PDF = RAW_DIR / "126002A12.pdf"
QUESTIONS_JSON = OUT_DIR / "questions.json"


CHAPTERS = [
    (1, 76, "圖說判讀"),
    (77, 107, "丈量及放樣"),
    (108, 240, "相關法規"),
    (241, 284, "安全維護"),
    (285, 334, "施工機具"),
    (335, 612, "相關施工作業"),
    (613, 718, "裝修工程管理"),
]

IMAGE_HINTS = ("左圖", "下圖", "此符號", "符號", "圖例", "立體圖", "視圖", "圖中")


@dataclass
class Question:
    id: str
    number: int
    localNumber: int
    source: str
    sourceRef: str
    chapter: str
    question: str
    choices: list[str]
    answerIndex: int
    answerIndices: list[int]
    explanation: str
    isHistorical: bool
    year: int | None
    image: str | None
    needsImage: bool


def normalize_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"Page \d+ of \d+", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.replace("㎜", "mm").replace("㎡", "m2").replace("㎝", "cm")
    return text.strip()


def chapter_for_index(index: int) -> tuple[int, int, str]:
    return CHAPTERS[index - 1]


def compact_choice(text: str) -> str:
    text = text.strip(" 。")
    return re.sub(r"\s+", " ", text)


def parse_question(chapter_index: int, local_number: int, answers: list[int], body: str) -> Question | None:
    markers = ["①", "②", "③", "④"]
    positions = [body.find(marker) for marker in markers]
    if any(pos < 0 for pos in positions):
        return None
    if positions != sorted(positions):
        return None

    question_text = compact_choice(body[: positions[0]])
    choices = []
    for index, pos in enumerate(positions):
        end = positions[index + 1] if index + 1 < len(positions) else len(body)
        choices.append(compact_choice(body[pos + 1 : end]))

    if not question_text or len(choices) != 4 or any(not choice for choice in choices):
        return None

    needs_image = any(hint in question_text for hint in IMAGE_HINTS)
    start, _end, chapter = chapter_for_index(chapter_index)
    global_number = start + local_number - 1
    answer_text = "、".join(choices[index - 1] for index in answers)
    if len(answers) == 1:
        explanation = f"本題答案為「{answer_text}」。複習時請回到「{chapter}」章節，確認題幹中的法規、CNS 圖例或施工管理概念。"
    else:
        explanation = f"本題為複選，答案為「{answer_text}」。複習時請逐一核對每個選項的法規、CNS 圖例或施工管理概念。"

    return Question(
        id=f"12600-A12-{global_number:03d}",
        number=global_number,
        localNumber=local_number,
        source="勞動部技能檢定中心公開學科測試參考資料",
        sourceRef="126002A12.pdf",
        chapter=chapter,
        question=question_text,
        choices=choices,
        answerIndex=answers[0] - 1,
        answerIndices=[answer - 1 for answer in answers],
        explanation=explanation,
        isHistorical=False,
        year=None,
        image=None,
        needsImage=needs_image,
    )


def parse_academic_pdf() -> list[Question]:
    reader = PdfReader(str(ACADEMIC_PDF))
    pages = [normalize_text(reader.pages[i].extract_text() or "") for i in range(1, len(reader.pages))]
    questions = []

    current_chapter = 1
    chapter_heading = re.compile(r"工作項目\s*([0-9]{2})\s*：\s*([^0-9]+)")
    question_start = re.compile(r"(?=(?<!\d)(?:\d\s*){1,3}\.\s*\(\s*[1-4]{1,4}\s*\))")
    question_head = re.compile(r"((?:\d\s*){1,3})\.\s*\(\s*([1-4]{1,4})\s*\)\s*(.+)")

    for page in pages:
        heading = chapter_heading.search(page)
        if heading:
            current_chapter = int(heading.group(1))
            page = page[heading.end() :]

        chunks = question_start.split(page)
        for chunk in chunks:
            match = question_head.match(chunk)
            if not match:
                continue
            local_number = int(re.sub(r"\s+", "", match.group(1)))
            answers = [int(char) for char in match.group(2)]
            question = parse_question(current_chapter, local_number, answers, match.group(3))
            if question:
                questions.append(question)

    by_id = {question.id: question for question in questions}
    return [by_id[key] for key in sorted(by_id, key=lambda item: int(item.rsplit("-", 1)[1]))]


def main() -> None:
    if not ACADEMIC_PDF.exists():
        raise SystemExit(f"Missing {ACADEMIC_PDF}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    questions = parse_academic_pdf()
    payload = {
        "meta": {
            "title": "建築物室內裝修工程管理乙級學科題庫",
            "examCode": "12600",
            "version": "A12",
            "sourcePdf": "https://owinform.wdasec.gov.tw/owInform/DLowFile/126002A12.pdf",
            "generatedFrom": "data/raw/126002A12.pdf",
            "questionCount": len(questions),
            "chapterCount": len(CHAPTERS),
            "notes": "圖片題保留題幹與選項，若 PDF 文字抽取無法呈現圖形，前端會排除於模擬測驗。",
        },
        "chapters": [
            {
                "id": f"{index:02d}",
                "name": name,
                "start": start,
                "end": end,
                "expectedCount": end - start + 1,
            }
            for index, (start, end, name) in enumerate(CHAPTERS, start=1)
        ],
        "questions": [asdict(question) for question in questions],
    }
    QUESTIONS_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(questions)} questions to {QUESTIONS_JSON}")


if __name__ == "__main__":
    main()
