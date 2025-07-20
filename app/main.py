from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import os
import httpx
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
RAKUTEN_APP_ID = os.getenv("RAKUTEN_APP_ID")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

class SwipeRequest(BaseModel):
    user_id: str
    book_isbn: str
    liked: bool
    author: str

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/swipe")
async def create_swipe(swipe: SwipeRequest):
    try:
        result = supabase.table("swipes").insert({
            "user_id": swipe.user_id,
            "book_isbn": swipe.book_isbn,
            "liked": swipe.liked,
            "author": swipe.author
        }).execute()
        
        return {"message": "Swipe recorded successfully", "data": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record swipe: {str(e)}")

@app.get("/recommendations/{user_id}")
async def get_recommendations(user_id: str):
    try:
        liked_swipes = supabase.table("swipes").select("author").eq("user_id", user_id).eq("liked", True).execute()
        
        if liked_swipes.data:
            authors = [swipe["author"] for swipe in liked_swipes.data if swipe["author"]]
            if authors:
                author_counts = Counter(authors)
                most_frequent_author = author_counts.most_common(1)[0][0]
                search_keyword = most_frequent_author
            else:
                search_keyword = "プログラミング"
        else:
            search_keyword = "プログラミング"
        
        if not RAKUTEN_APP_ID:
            raise HTTPException(status_code=500, detail="Rakuten API Application ID not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://app.rakuten.co.jp/services/api/BooksBook/Search/20170404",
                params={
                    "format": "json",
                    "keyword": search_keyword,
                    "applicationId": RAKUTEN_APP_ID,
                    "hits": 10
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=500, detail=f"Rakuten API error: {response.status_code}")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")
