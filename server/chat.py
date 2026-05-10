import os
from dotenv import load_dotenv
from groq import Groq
from src.embedder import GeminiEmbedder
from src.database import SupabaseDB

def main():
    load_dotenv()
    
    print("Initializing PAF-IAST Chatbot...")
    embedder = GeminiEmbedder()
    db = SupabaseDB()
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    print("\n" + "="*50)
    print("Welcome to the PAF-IAST University Chatbot!")
    print("Type 'quit' or 'exit' to stop.")
    print("="*50 + "\n")
    
    while True:
        query = input("You: ")
        if query.lower() in ['quit', 'exit']:
            break
            
        try:
            # 1. Embed the user's query
            query_embedding = embedder.embed_query(query)
            
            # 2. Search Supabase for the most relevant context
            search_results = db.search(query_embedding, limit=3)
            
            if not search_results:
                print("Bot: I couldn't find any relevant information to answer your question.")
                continue
                
            # 3. Construct the context prompt
            context_text = "\n\n---\n\n".join([f"Source ({res['url']}):\n{res['content']}" for res in search_results])
            
            system_prompt = (
                "You are a helpful, accurate, and professional chatbot for PAF-IAST University. "
                "You must use the provided context to answer the user's questions. "
                "If the answer is not in the context, say 'I do not have enough information to answer that.' "
                "Keep your answers concise and cite your sources if possible."
            )
            
            user_prompt = f"Context Information:\n{context_text}\n\nUser Question: {query}\n\nAnswer:"
            
            # 4. Generate answer using Groq (Llama 3 8B)
            completion = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=500,
            )
            
            answer = completion.choices[0].message.content
            print(f"\nBot: {answer}\n")
            
        except Exception as e:
            print(f"\nAn error occurred: {e}\n")

if __name__ == "__main__":
    main()
