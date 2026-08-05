from fastapi import FastAPI
from pydantic import BaseModel
from raven import ask_raven
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Question(BaseModel):
    question: str
    history: list = []


@app.post("/chat")
def chat(data: Question):

    print("Received:", data.question)

    answer = ask_raven(
        data.question,
        data.history
    )

    print("Answer:", answer)

    return {
        "answer": answer
    }
