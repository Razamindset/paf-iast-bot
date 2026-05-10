import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
from src.embedder import GeminiEmbedder
from src.database import SupabaseDB

load_dotenv()

app = FastAPI(title="PAF-IAST Bot Web Interface")

# Mount static files and templates
# We'll create these files in a moment
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize components
embedder = GeminiEmbedder()
db = SupabaseDB()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class ChatRequest(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    query = request.message
    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        # 1. Embed the user's query
        query_embedding = embedder.embed_query(query)
        
        # 2. Search Supabase for the most relevant context
        search_results = db.search(query_embedding, limit=3)
        
        # 3. Construct the context prompt
        if search_results:
            context_text = "\n\n---\n\n".join([f"Source ({res['url']}):\n{res['content']}" for res in search_results])
            sources = [res['url'] for res in search_results]
        else:
            context_text = "No specific university documents were found matching this query."
            sources = []
        
        system_prompt = (
            "You are 'PAF-IAST Bot', the official AI assistant for the Pak-Austria Fachhochschule: Institute of Applied Sciences and Technology. "
            "Your purpose is to assist students, parents, and visitors with accurate information about scholarships, admissions, faculty, and campus life. "
            "Always base your answers on the provided Context Information. If the context is insufficient, "
            "say: 'I'm sorry, I don't have specific details on that in my current records. Please visit https://paf-iast.edu.pk/ for the most up-to-date information.' "
            "Use Markdown formatting (bold, bullet points, numbered lists, etc.) to make your responses highly readable and professional. "
            "Keep your tone professional, helpful, and welcoming. Cite the source URL if available in the context."
        )
        
        user_prompt = f"Context Information:\n{context_text}\n\nUser Question: {query}\n\nAnswer:"
        
        # 4. Generate answer using Groq (Llama 3.1 8B)
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=800,
        )
        
        answer = completion.choices[0].message.content
        return {"answer": answer, "sources": sources}
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
