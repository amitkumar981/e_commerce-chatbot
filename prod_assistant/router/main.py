import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from prod_assistant.workflow.agentic_workflow_with_mcp import AgenticRAG

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Global Agent Instance ----
rag_agent: AgenticRAG | None = None


@app.on_event("startup")
async def startup_event():
    global rag_agent
    rag_agent = AgenticRAG()
    await rag_agent.async_init()   # load tools before first request
    print("✅ AgenticRAG initialized")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


@app.post('/get', response_class=HTMLResponse)
async def chat(msg: str = Form(...)):
    rag_agent = AgenticRAG()
    await rag_agent.async_init()
    response = await rag_agent.run(msg)
    print(f"Response: {response}")
    return response