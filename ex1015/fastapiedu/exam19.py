"""
간단한 AI Agent + FastAPI REST API 예제
- Python 3.12
- LLM : gpt-4o-mini (OpenAI Tool Calling 방식)
- 실행 : uvicorn exam19:app --reload   (원래 주석은 main:app이었는데 이 파일 이름에 맞게 고침)
- 문서 : http://127.0.0.1:8000/docs
"""

import ast
import json
import operator
import random
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field

client = OpenAI()  # 환경변수 OPENAI_API_KEY 사용

MODEL = "gpt-4o-mini"
MAX_STEPS = 5  # 에이전트가 도구를 연속으로 호출할 수 있는 최대 횟수 (무한루프 방지)

SYSTEM_PROMPT = (
    "너는 '유니코'라는 이름의 친절하고 유쾌한 한국어 AI 비서야. "
    "시간, 계산, 주사위, 점심 메뉴 추천이 필요하면 반드시 제공된 도구를 사용해. "
    "답변은 짧고 재미있게 해줘."
)


# ──────────────────────────────────────────────
# 1. 도구(Tool) 정의 : 에이전트가 직접 실행할 수 있는 파이썬 함수들
# ──────────────────────────────────────────────
def get_current_time(timezone: str = "Asia/Seoul") -> dict:
    """지정한 타임존의 현재 시각을 반환"""
    try:
        now = datetime.now(ZoneInfo(timezone))
    except Exception:
        return {"error": f"알 수 없는 타임존: {timezone}"}
    return {"timezone": timezone, "now": now.strftime("%Y-%m-%d %H:%M:%S")}


# 안전한 계산기 : eval() 대신 ast 로 사칙연산만 허용
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


# 수식 문자열을 파이썬 문법 트리(AST)로 바꾼 뒤, 숫자와 위에 등록한 연산자만 직접 계산한다.
# eval()과 달리 함수 호출이나 import 같은 코드는 실행되지 않는다. ("__import__('os')" -> "지원하지 않는 수식입니다.")
MAX_POW_BITS = 10_000  # 추가: 거듭제곱 결과 크기 상한 (약 3천 자리)


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        # 추가: 거듭제곱 지수 제한.
        # 원래 코드는 '9**9**8'처럼 지수가 큰 식도 그대로 계산해서, 테스트해 보니 20초가 지나도 끝나지 않았다.
        # 이 계산기는 LLM이 사용자 문장을 보고 호출하는 API 도구라, 누구든 이런 식으로 서버를 멈추게 할 수 있어서 상한을 두었다.
        # 지수만 막으면 ((10**1000)**1000)**1000처럼 나눠서 키울 수 있어서, 결과의 크기(비트 수)를 미리 어림해서 막는다.
        # (실수는 너무 크면 OverflowError가 바로 나서 아래 calculate의 except가 처리한다)
        if isinstance(node.op, ast.Pow):
            base, exp = _eval(node.left), _eval(node.right)
            if isinstance(base, int) and isinstance(exp, int) and abs(base) > 1 and exp > 0 \
                    and exp * abs(base).bit_length() > MAX_POW_BITS:
                raise ValueError("거듭제곱 결과가 너무 큽니다.")
            return operator.pow(base, exp)
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("지원하지 않는 수식입니다.")


def calculate(expression: str) -> dict:
    """사칙연산 수식을 계산 (예: '(12 + 8) * 3')"""
    try:
        return {"expression": expression, "result": _eval(ast.parse(expression, mode="eval").body)}
    except Exception as e:
        return {"error": str(e)}


def roll_dice(sides: int = 6, count: int = 1) -> dict:
    """주사위를 굴림"""
    count = max(1, min(count, 10))
    sides = max(2, min(sides, 1000))
    rolls = [random.randint(1, sides) for _ in range(count)]
    return {"sides": sides, "rolls": rolls, "total": sum(rolls)}


def recommend_lunch(mood: str = "보통") -> dict:
    """기분에 맞는 점심 메뉴를 추천 (더미 데이터)"""
    menu = {
        "우울": ["돈까스", "떡볶이", "치킨"],
        "피곤": ["삼계탕", "갈비탕", "장어덮밥"],
        "신남": ["마라탕", "삼겹살", "피자"],
        "보통": ["김치찌개", "비빔밥", "제육볶음"],
    }
    return {"mood": mood, "recommend": random.choice(menu.get(mood, menu["보통"]))}


# 함수 이름 → 실제 함수 매핑
TOOL_FUNCS = {
    "get_current_time": get_current_time,
    "calculate": calculate,
    "roll_dice": roll_dice,
    "recommend_lunch": recommend_lunch,
}

# LLM 에게 알려줄 도구 명세 (JSON Schema)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "특정 타임존의 현재 날짜와 시각을 알려준다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "예: Asia/Seoul, America/New_York"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "사칙연산 수식을 계산한다.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "예: (12 + 8) * 3"}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "roll_dice",
            "description": "주사위를 굴린다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sides": {"type": "integer", "description": "주사위 면의 수 (기본 6)"},
                    "count": {"type": "integer", "description": "굴릴 주사위 개수 (기본 1)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_lunch",
            "description": "사용자의 기분(우울/피곤/신남/보통)에 맞는 점심 메뉴를 추천한다.",
            "parameters": {
                "type": "object",
                "properties": {"mood": {"type": "string", "description": "우울, 피곤, 신남, 보통 중 하나"}},
            },
        },
    },
]


# ──────────────────────────────────────────────
# 2. 에이전트 루프 : LLM 호출 → 도구 실행 → 결과 전달 → 최종 답변
# ──────────────────────────────────────────────
sessions: dict[str, list[dict]] = {}  # session_id → 대화 기록 (메모리 저장, 서버 재시작 시 초기화)
# (지우지 않으면 계속 쌓이고, 서버를 여러 개 띄우면 서로 공유되지 않는다. 실서비스에서는 DB나 Redis에 저장한다)


def run_agent(session_id: str, user_message: str) -> tuple[str, list[dict]]:
    messages = sessions.setdefault(session_id, [{"role": "system", "content": SYSTEM_PROMPT}])
    messages.append({"role": "user", "content": user_message})
    tool_logs: list[dict] = []

    for _ in range(MAX_STEPS):
        res = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        msg = res.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        # 도구 호출이 없으면 최종 답변
        if not msg.tool_calls:
            return msg.content, tool_logs

        # 도구 호출이 있으면 실행하고 결과를 대화에 추가
        # 한 응답에 도구 호출이 여러 개 올 수 있어서 하나씩 실행한다.
        # 주의: LLM이 함수에 없는 인자를 넣으면(예: roll_dice에 color) TypeError가 나서 /chat 전체가 500으로 끝난다.
        for call in msg.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments or "{}")
            result = TOOL_FUNCS[name](**args)
            tool_logs.append({"tool": name, "args": args, "result": result})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    return "생각이 너무 길어져서 멈췄어요. 질문을 조금 더 간단히 해주세요!", tool_logs


# ──────────────────────────────────────────────
# 3. FastAPI : 에이전트를 REST API 로 서비스
# ──────────────────────────────────────────────
app = FastAPI(title="유니코 AI Agent API", description="도구를 사용하는 간단한 AI 에이전트", version="1.0.0")


class ChatRequest(BaseModel):
    message: str = Field(..., description="에이전트에게 보낼 메시지", examples=["지금 서울 몇 시야?"])
    session_id: str | None = Field(None, description="이전 대화를 이어가려면 응답받은 session_id 전달")


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    tool_calls: list[dict]  # 이번 질문에서 에이전트가 사용한 도구 기록


@app.get("/", summary="서버 상태 확인")
def health():
    return {"status": "ok", "model": MODEL, "agent": "유니코"}


@app.get("/tools", summary="에이전트가 사용할 수 있는 도구 목록")
def list_tools():
    return [{"name": t["function"]["name"], "description": t["function"]["description"]} for t in TOOLS]


@app.post("/chat", response_model=ChatResponse, summary="에이전트와 대화")
def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())[:8]
    try:
        answer, tool_logs = run_agent(session_id, req.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"에이전트 실행 오류: {e}")
    return ChatResponse(session_id=session_id, answer=answer, tool_calls=tool_logs)


@app.get("/sessions/{session_id}", summary="대화 기록 조회")
def get_history(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="존재하지 않는 session_id 입니다.")
    return [
        {"role": m["role"], "content": m["content"]}
        for m in sessions[session_id]
        if m["role"] in ("user", "assistant") and m.get("content")
    ]


@app.delete("/sessions/{session_id}", summary="대화 기록 삭제")
def delete_history(session_id: str):
    if sessions.pop(session_id, None) is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 session_id 입니다.")
    return {"deleted": session_id}
