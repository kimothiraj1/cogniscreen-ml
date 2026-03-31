from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

from engines.game_scoring_engine import score_game
from engines.chat_scoring_engine import score_chat
from engines.webcam_scoring_engine import score_webcam
from engines.composite_engine import score_daily, get_stage
from engines.trend_engine import calculate_trend
from alerts.twilio_alert import send_caregiver_alert

load_dotenv()

app = FastAPI(title="CogniScreen ML API", version="1.0.0")

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your Express backend URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API KEY AUTH ─────────────────────────────────────────────────────────────
API_KEY_NAME = "X-ML-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

def verify_api_key(api_key: str = Security(api_key_header)):
    expected = os.getenv("ML_API_KEY")
    if not expected:
        raise HTTPException(status_code=500, detail="ML_API_KEY not configured on server")
    if api_key != expected:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# ─── MODELS ───────────────────────────────────────────────────────────────────
class GamePayload(BaseModel):
    userId: str
    testType: str           # memory_mosaic | word_garden | path_finder
    score: float            # 0.0 to 1.0
    timeTaken: int          # ms
    errors: int
    hesitationGaps: List[int]   # ms between each tap
    age: int

class ChatPayload(BaseModel):
    userId: str
    avgWPM: float
    wpmDelta: float         # this session minus previous session WPM
    backspaceRate: float    # backspaces / total keystrokes
    avgPauseBetweenMessages: int   # ms
    repetitionCount: int
    avgSentenceLength: float
    messages: List[str]     # raw texts — we run TextBlob here
    sessionDuration: int    # ms
    messageCount: int
    timeOfDay: int          # hour 0-23

class WebcamPayload(BaseModel):
    userId: str
    dominantEmotion: str    # happy|sad|angry|fearful|disgusted|surprised|neutral
    emotionConfidence: float
    avgBlinkRate: float     # blinks per minute
    gazeStabilityScore: float   # variance — lower = more stable
    sessionDuration: int

class DailyPayload(BaseModel):
    userId: str
    gameScore: float
    chatScore: float
    webcamScore: float
    taskCompletionRate: float
    last7Scores: List[float]
    age: int
    livesAlone: bool
    caregiverPhone: Optional[str] = None

class TaskLogPayload(BaseModel):
    userId: str
    date: str           # YYYY-MM-DD
    tasksCompleted: int
    tasksTotal: int
    streakDay: int

# ─── ROUTES ───────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "CogniScreen ML API"}

@app.post("/score/game")
def score_game_endpoint(data: GamePayload, _=Depends(verify_api_key)):
    risk = score_game(
        data.testType, data.score, data.timeTaken,
        data.errors, data.hesitationGaps, data.age
    )
    stage, explanation = get_stage(risk, 0)
    level_map = {0: "Low", 1: "Low", 2: "Medium", 3: "High"}
    return {
        "riskScore": round(risk, 2),
        "riskLevel": level_map[stage],
        "stage": stage,
        "trendSlope": 0,
        "explanation": explanation,
        "sources": {"gameScore": round(risk, 2)}
    }

@app.post("/score/chat")
def score_chat_endpoint(data: ChatPayload, _=Depends(verify_api_key)):
    risk = score_chat(
        data.avgWPM, data.wpmDelta, data.backspaceRate,
        data.repetitionCount, data.messages
    )
    stage, explanation = get_stage(risk, 0)
    level_map = {0: "Low", 1: "Low", 2: "Medium", 3: "High"}
    return {
        "languageScore": round(risk, 2),
        "riskLevel": level_map[stage],
        "stage": stage,
        "explanation": explanation
    }

@app.post("/score/webcam")
def score_webcam_endpoint(data: WebcamPayload, _=Depends(verify_api_key)):
    risk = score_webcam(
        data.dominantEmotion, data.emotionConfidence,
        data.avgBlinkRate, data.gazeStabilityScore
    )
    stage, explanation = get_stage(risk, 0)
    level_map = {0: "Low", 1: "Low", 2: "Medium", 3: "High"}
    return {
        "stressScore": round(risk, 2),
        "riskLevel": level_map[stage],
        "stage": stage,
        "explanation": explanation
    }

@app.post("/score/daily")
def score_daily_endpoint(data: DailyPayload, _=Depends(verify_api_key)):
    trend = calculate_trend(data.last7Scores)
    composite = score_daily(
        data.gameScore, data.chatScore,
        data.webcamScore, data.taskCompletionRate
    )
    # If lives alone, lower the stage threshold (more sensitive)
    effective_slope = trend * (1.3 if data.livesAlone else 1.0)
    stage, explanation = get_stage(composite, effective_slope)
    level_map = {0: "Low", 1: "Low", 2: "Medium", 3: "High"}

    result = {
        "compositeRiskScore": round(composite, 2),
        "riskLevel": level_map[stage],
        "stage": stage,
        "trendSlope": round(trend, 4),
        "explanation": explanation,
        "sources": {
            "gameScore": round(data.gameScore, 2),
            "chatScore": round(data.chatScore, 2),
            "webcamScore": round(data.webcamScore, 2),
            "taskRate": round(data.taskCompletionRate, 2)
        }
    }

    # Trigger SMS alert if high concern
    if stage == 3 and data.caregiverPhone:
        try:
            send_caregiver_alert(data.caregiverPhone, data.userId, explanation)
            result["alertSent"] = True
        except Exception as e:
            result["alertSent"] = False
            result["alertError"] = str(e)

    return result

@app.post("/tasks/log")
def log_task(data: TaskLogPayload, _=Depends(verify_api_key)):
    completion_rate = data.tasksCompleted / max(data.tasksTotal, 1)
    return {
        "userId": data.userId,
        "date": data.date,
        "completionRate": round(completion_rate, 2),
        "streakDay": data.streakDay,
        "status": "logged"
    }
