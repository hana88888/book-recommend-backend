from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
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
    allow_origins=[
        "*",
        "http://localhost:8081",
        "https://swipe-api-tunnel-xnpp02tu.devinapps.com",
        "https://user:29bb2d1d694ad67daa723202a96f7376@swipe-api-tunnel-xnpp02tu.devinapps.com",
        "https://swipe-api-tunnel-6864jt82.devinapps.com",
        "https://user:c9adad803341d702b5ba66faf2e16df6@swipe-api-tunnel-6864jt82.devinapps.com"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
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
    title: str
    cover_image_url: str
    summary: str = ""

@app.options("/{path:path}")
async def options_handler(path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

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
            "author": swipe.author,
            "title": swipe.title,
            "cover_image_url": swipe.cover_image_url,
            "summary": swipe.summary
        }).execute()
        
        return {"message": "Swipe recorded successfully", "data": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record swipe: {str(e)}")

@app.get("/favorites/{user_id}")
async def get_favorites(user_id: str):
    try:
        liked_swipes = supabase.table("swipes").select("book_isbn, title, author, cover_image_url, summary").eq("user_id", user_id).eq("liked", True).execute()
        
        if not liked_swipes.data:
            return {"Items": []}
        
        formatted_books = []
        for swipe in liked_swipes.data:
            if swipe["title"] and swipe["author"]:
                formatted_books.append({
                    "title": swipe["title"],
                    "author": swipe["author"],
                    "largeImageUrl": swipe["cover_image_url"],
                    "isbn": swipe["book_isbn"],
                    "summary": swipe.get("summary", "")
                })
        
        return {"Items": formatted_books}
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get favorites: {str(e)}")

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
                data = response.json()
                if 'Items' in data:
                    for item in data['Items']:
                        if 'Item' in item and 'itemCaption' in item['Item']:
                            item['Item']['summary'] = item['Item']['itemCaption']
                        else:
                            item['Item']['summary'] = ''
                return data
            else:
                raise HTTPException(status_code=500, detail=f"Rakuten API error: {response.status_code}")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")
