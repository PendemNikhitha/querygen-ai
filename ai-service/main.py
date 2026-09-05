from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from pinecone import Pinecone
from database import init_db, execute_sql
import os
import re
import uuid
from dotenv import load_dotenv
cache={}

load_dotenv()

app = FastAPI(
    title="QueryGen AI - Text-to-SQL Service",
    description="Converts natural language to SQL queries using Groq LLM + RAG",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init DB
init_db()

# Clients
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(
    name=os.getenv("PINECONE_INDEX"),
    host=os.getenv("PINECONE_HOST")
)

# ─── Models ───────────────────────────────────────────────
class QueryRequest(BaseModel):
    query: str
    database_schema: str = "users(id, name, email, city, age)"

class QueryResponse(BaseModel):
    success: bool
    natural_language_query: str
    generated_sql: str
    model_used: str
    keywords: list
    similar_queries: list
    query_results: dict
def extract_keywords(query: str) -> list:
    stop_words = {
        'show', 'me', 'all', 'the', 'find', 'get', 'list', 'give',
        'who', 'what', 'where', 'how', 'many', 'with', 'and', 'or',
        'from', 'in', 'of', 'a', 'an', 'is', 'are', 'have', 'has',
        'users', 'user', 'records', 'data', 'entries'
    }
    words = re.findall(r'\b[a-zA-Z0-9]+\b', query.lower())
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return list(set(keywords))
def get_unique_values(keywords: list) -> dict:
    db_values = {
        "city": ["Delhi", "Mumbai", "Hyderabad", "Chennai", "Bangalore"],
        "age":  ["18", "21", "25", "30", "35", "40"],
        "name": ["Alice", "Bob", "Charlie", "Diana"],
    }
    relevant = {}
    for keyword in keywords:
        for column, values in db_values.items():
            if keyword in [v.lower() for v in values] or keyword == column:
                relevant[column] = values
    return relevant

def store_query_in_pinecone(query: str, sql: str):
    try:
        embedding = pc.inference.embed(
            model="llama-text-embed-v2",
            inputs=[query],
            parameters={"input_type": "passage"}
        )
        vector = embedding[0].values
        index.upsert(
            vectors=[{
                "id": str(uuid.uuid4()),
                "values": vector,
                "metadata": {
                    "natural_query": query,
                    "sql": sql
                }
            }],
            namespace="queries"
        )
        print(f"✅ Stored in Pinecone")
    except Exception as e:
        print(f"⚠️ Pinecone upsert error: {e}")
def find_similar_queries(query: str) -> list:
    try:
        embedding = pc.inference.embed(
            model="llama-text-embed-v2",
            inputs=[query],
            parameters={"input_type": "query"}
        )
        vector = embedding[0].values
        results = index.query(
            namespace="queries",
            vector=vector,
            top_k=3,
            include_metadata=True
        )
        print(f"🔍 Raw scores: {[(m.score, m.metadata.get('natural_query','')) for m in results.matches]}")
        similar = []
        for match in results.matches:
            if match.score > 0.5:
                similar.append({
                    "query": match.metadata.get("natural_query", ""),
                    "sql":   match.metadata.get("sql", ""),
                    "score": round(match.score, 3)
                })
        return similar
    except Exception as e:
        print(f"⚠️ Pinecone search error: {e}")
        return []

# ─── Routes ───────────────────────────────────────────────
@app.get("/")
def read_root():
    return {"message": "QueryGen AI v2 - RAG enabled", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ai-service", "rag": "enabled"}

@app.get("/debug/pinecone")
async def debug_pinecone():
    try:
        stats = index.describe_index_stats()
        results = index.query(
            namespace="queries",
            vector=[0] * 1024,
            top_k=5,
            include_metadata=True
        )
        return {
            "stats": str(stats),
            "raw_results": str(results)
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/text-to-sql", response_model=QueryResponse)
async def generate_sql(request: QueryRequest):
    try:
        print(f"📥 Query: {request.query}")

        # Step 1: Keywords
        keywords = extract_keywords(request.query)
        print(f"🔑 Keywords: {keywords}")

        # Step 2: Unique values
        unique_values = get_unique_values(keywords)
        print(f"📊 Unique values: {unique_values}")

        # Step 3: Similar queries
        similar_queries = find_similar_queries(request.query)
        print(f"🔍 Similar: {len(similar_queries)} found")

        # Step 4: Build RAG prompt
        context = ""
        if unique_values:
            context += "\nRelevant column values in the database:\n"
            for col, vals in unique_values.items():
                context += f"  - {col}: {', '.join(vals)}\n"

        if similar_queries:
            context += "\nSimilar past queries for reference:\n"
            for sq in similar_queries:
                context += f"  NL: {sq['query']}\n  SQL: {sq['sql']}\n\n"

        prompt = f"""You are a SQL expert. Convert the natural language query to SQL.

Database Schema: {request.database_schema}
{context}
Natural Language Query: {request.query}

Instructions:
1. Generate ONLY the SQL query, nothing else
2. Use proper SQL syntax
3. Use exact column values from context if available
4. Do not include explanations or markdown

SQL Query:"""

        # Step 5: Groq
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a SQL expert. Generate only SQL queries."},
                {"role": "user",   "content": prompt}
            ],
            model="openai/gpt-oss-20b",
            temperature=0.1,
            max_tokens=500
        )

        generated_sql = chat_completion.choices[0].message.content.strip()

        if generated_sql.startswith("```sql"):
            generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
        elif generated_sql.startswith("```"):
            generated_sql = generated_sql.replace("```", "").strip()

        print(f"✅ SQL: {generated_sql}")

        # Step 6: Store in Pinecone
        store_query_in_pinecone(request.query, generated_sql)

        # Step 7: Execute SQL against SQLite
        sql_results = execute_sql(generated_sql)
        print(f"📊 Results: {sql_results.get('count', 0)} rows")

        return QueryResponse(
            success=True,
            natural_language_query=request.query,
            generated_sql=generated_sql,
            model_used="openai/gpt-oss-20b",
            keywords=keywords,
            similar_queries=similar_queries,
            query_results=sql_results
        )

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")