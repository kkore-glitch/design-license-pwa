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

IMAGE_PATTERNS = (
    "左圖",
    "下圖",
    "此符號",
    "本立體圖",
    "本圖",
    "下列圖",
)

QUESTION_IMAGES = {
    question_id: f"assets/questions/{question_id}.png"
    for question_id in [
        "12600-A12-001",
        "12600-A12-004",
        "12600-A12-005",
        "12600-A12-006",
        "12600-A12-008",
        "12600-A12-011",
        "12600-A12-012",
        "12600-A12-013",
        "12600-A12-014",
        "12600-A12-015",
        "12600-A12-017",
        "12600-A12-018",
        "12600-A12-019",
        "12600-A12-020",
        "12600-A12-022",
        "12600-A12-030",
        "12600-A12-031",
        "12600-A12-032",
        "12600-A12-033",
        "12600-A12-043",
        "12600-A12-044",
        "12600-A12-045",
        "12600-A12-048",
        "12600-A12-051",
        "12600-A12-052",
        "12600-A12-053",
        "12600-A12-054",
        "12600-A12-055",
        "12600-A12-056",
        "12600-A12-057",
        "12600-A12-058",
        "12600-A12-059",
        "12600-A12-060",
        "12600-A12-061",
        "12600-A12-062",
        "12600-A12-063",
        "12600-A12-064",
        "12600-A12-065",
        "12600-A12-067",
        "12600-A12-068",
        "12600-A12-069",
        "12600-A12-070",
        "12600-A12-079",
        "12600-A12-095",
        "12600-A12-305",
    ]
}

VISUAL_CHOICES = ["圖中①", "圖中②", "圖中③", "圖中④"]

MANUAL_VISUAL_QUESTIONS = [
    (1, 43, [2], "本立體圖的正視圖為"),
    (1, 44, [2], "本立體圖的右側視圖為"),
    (1, 45, [4], "左圖為已知上圖為俯視圖及下圖為正視圖，請選擇符合正確之右側視圖"),
    (1, 52, [1, 2, 4], "依 CNS11567 之 A1042 建築圖符號及圖例規定，下列哪些屬於材料、構造圖例？"),
    (1, 54, [1, 2, 3], "依 CNS11567 之 A1042 建築設備圖表示法規定，下列哪些屬於消防設備符號？"),
    (1, 57, [2, 4], "依中華民國國家標準 CNS11567 之 A1042 建築設備圖表示法規定，下列哪些符號為電氣設備符號？"),
    (1, 59, [1, 4], "依中華民國國家標準 CNS11567 之 A1042 建築設備圖表示法規定，下列哪些符號為空調及機械設備圖例？"),
    (1, 60, [1, 2], "依中華民國國家標準 CNS11567 之 A1042 建築設備圖表示法規定，下列哪些符號為電信、電鈴、電視設備符號？"),
    (1, 61, [1, 4], "依中華民國國家標準 CNS11567 之 A1042 建築設備圖表示法規定，下列哪些符號為給排水及衛生設備符號？"),
    (1, 62, [2, 3, 4], "依據 CNS11567-A1042 建築製圖規定，下列哪些為空調及機械設備圖例之符號？"),
    (1, 63, [1, 3, 4], "依據 CNS11567-A1042 建築製圖規定，下列哪些為電氣設備圖例標準圖例之符號？"),
    (1, 64, [1, 2, 3], "依據 CNS11567-A1042 建築製圖規定，下列哪些為給排水及衛生設備符號？"),
    (1, 65, [2, 3, 4], "依據 CNS11567-A1042 建築製圖規定，下列哪些為電信、電鈴、電視設備符號？"),
    (1, 67, [2, 3, 4], "依據 CNS11567-A1042 建築製圖規定，哪些為空調及機械設備圖例之符號？"),
    (1, 68, [1, 4], "依據 CNS11567-A1042 建築製圖規定，哪些為電氣設備符號？"),
    (1, 69, [1, 3], "依據 CNS11567-A1042 建築製圖規定，哪些為電信、電鈴、電視設備符號？"),
    (1, 70, [1, 2, 4], "依據 CNS11567-A1042 建築製圖規定，哪些為給排水及衛生設備符號？"),
    (2, 3, [1], "水平管放樣時，管內水面靜止，液面呈曲面狀態，在訂定水面高度時下列何者正確？"),
]


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


def compact_choice(text: str, strip_choice_suffix: bool = False) -> str:
    text = text.strip(" 。")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"(?<=[\u4e00-\u9fffA-Za-z0-9])\s+(?=[，。；：、！？）」])", "", text)
    text = re.sub(r"(?<=[，,])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"(?<=[（「])\s+(?=[\u4e00-\u9fffA-Za-z0-9])", "", text)
    text = re.sub(r"([：:/×~＝=<>≦≧≤≥])\s+(\d)", r"\1\2", text)
    text = re.sub(r"(\d)\s+([：:/×~＝=<>≦≧≤≥])", r"\1\2", text)
    text = re.sub(r"([A-Za-z])\s+(\d)", r"\1\2", text)
    text = re.sub(r"(\d)\s+([A-Za-z])", r"\1\2", text)
    text = text.replace("m 2", "m2").replace("公 分", "公分").replace("平 方", "平方")
    text = text.replace("「 ", "「").replace(" 」", "」")
    if strip_choice_suffix:
        text = re.sub(r"(表示|為宜)$", "", text)
    return text.strip(" 。")


def needs_image_question(question_text: str) -> bool:
    if "此符號『" in question_text:
        return False
    if any(pattern in question_text for pattern in IMAGE_PATTERNS):
        return True
    return bool(re.search(r"(圖例中|符號中|設備圖中|工程之圖說標準中)[，,]?代表$", question_text))


def extract_law_name(question_text: str) -> str | None:
    quoted = re.findall(r"[「『]([^」』]+)[」』]", question_text)
    for item in quoted:
        if item.endswith(("法", "規則", "辦法", "標準")):
            return item
    for name in ["建築法", "消防法", "建築技術規則", "建築物室內裝修管理辦法", "職業安全衛生法"]:
        if name in question_text:
            return name
    return None


def focus_text(question_text: str) -> str:
    text = question_text
    text = re.sub(r"^依中華民國國家標準\s*CNS\s*規定[，,]?", "", text)
    text = re.sub(r"^依[「『][^」』]+[」』]規定[，,；]?", "", text)
    text = text.strip(" ，。？")
    return text[:56] + ("..." if len(text) > 56 else "")


def build_explanation(question_text: str, choices: list[str], answers: list[int], chapter: str, needs_image: bool) -> str:
    answer_text = "、".join(choices[index - 1] for index in answers)
    is_multi = len(answers) > 1
    is_negative = any(word in question_text for word in ["非", "不是", "不正確", "錯誤", "不得", "不宜"])
    law_name = extract_law_name(question_text)
    focus = focus_text(question_text)

    if needs_image:
        return f"答案重點：此題須配合圖形或符號判讀；官方 A12 題庫給出的對應答案是「{answer_text}」。若要複習這題，請對照官方 PDF 的圖例位置一起看。"

    if "CNS" in question_text or chapter == "圖說判讀":
        return f"答案重點：此題考 CNS 圖例、建築製圖代號或圖面規則。題幹中的判讀對象是「{focus}」，在官方 A12 題庫中對應為「{answer_text}」。"

    if law_name:
        return f"答案重點：此題考「{law_name}」下的條件、程序、罰則或名詞歸屬。題幹問的是「{focus}」，答案選「{answer_text}」是因為它符合該法規脈絡。"

    if is_negative:
        if is_multi:
            return f"答案重點：這是複選否定題，題幹要找不符合或錯誤的選項；「{answer_text}」是官方 A12 題庫列出的不符合項目。"
        return f"答案重點：這是否定題，題幹要找不符合、錯誤或不應採用的選項；「{answer_text}」才是被排除的項目。"

    if any(word in question_text for word in ["工具", "要用", "宜用", "機具", "切割", "施工"]):
        return f"答案重點：此題考施工工具、機具或工序用途。題幹描述的工作是「{focus}」，適用的答案是「{answer_text}」。"

    if any(word in question_text for word in ["坪", "平方", "公尺", "台尺", "才", "換算", "面積", "數量", "估價", "工料"]):
        return f"答案重點：此題考工程數量、面積、單位或工料估算。答案「{answer_text}」是依題幹條件換算或歸類後的結果。"

    if is_multi:
        return f"答案重點：這是複選題；「{answer_text}」這些選項共同符合題幹條件。作答時要逐一核對每個選項是否都符合「{focus}」。"

    return f"答案重點：題幹問的是「{focus}」，官方 A12 題庫中與這個條件對應的答案是「{answer_text}」。"


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
        choices.append(compact_choice(body[pos + 1 : end], strip_choice_suffix=True))

    if not question_text or len(choices) != 4 or any(not choice for choice in choices):
        return None

    start, _end, chapter = chapter_for_index(chapter_index)
    global_number = start + local_number - 1
    question_id = f"12600-A12-{global_number:03d}"
    image = QUESTION_IMAGES.get(question_id)
    needs_image = needs_image_question(question_text) and image is None
    explanation = build_explanation(question_text, choices, answers, chapter, needs_image)

    return Question(
        id=question_id,
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
        image=image,
        needsImage=needs_image,
    )


def manual_visual_question(chapter_index: int, local_number: int, answers: list[int], question_text: str) -> Question:
    start, _end, chapter = chapter_for_index(chapter_index)
    global_number = start + local_number - 1
    question_id = f"12600-A12-{global_number:03d}"
    choices = VISUAL_CHOICES.copy()
    explanation = build_explanation(question_text, choices, answers, chapter, False)
    return Question(
        id=question_id,
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
        image=QUESTION_IMAGES[question_id],
        needsImage=False,
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
        headings = list(chapter_heading.finditer(page))
        segments: list[tuple[int, str]] = []
        cursor = 0
        for heading in headings:
            if heading.start() > cursor:
                segments.append((current_chapter, page[cursor : heading.start()]))
            current_chapter = int(heading.group(1))
            cursor = heading.end()
        segments.append((current_chapter, page[cursor:]))

        for chapter_index, segment in segments:
            chunks = question_start.split(segment)
            for chunk in chunks:
                match = question_head.match(chunk)
                if not match:
                    continue
                local_number = int(re.sub(r"\s+", "", match.group(1)))
                answers = [int(char) for char in match.group(2)]
                question = parse_question(chapter_index, local_number, answers, match.group(3))
                if question:
                    questions.append(question)

    by_id = {question.id: question for question in questions}
    for item in MANUAL_VISUAL_QUESTIONS:
        question = manual_visual_question(*item)
        by_id.setdefault(question.id, question)
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
