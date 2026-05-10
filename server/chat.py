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
                print("PAF-IAST Bot: I'm sorry, I couldn't find any specific information in my database to answer that. You might find what you're looking for on our official website: https://paf-iast.edu.pk/")
                continue
                
            # 3. Construct the context prompt
            context_text = "\n\n---\n\n".join([f"Source ({res['url']}):\n{res['content']}" for res in search_results])
            
            system_prompt = (
                "You are 'PAF-IAST Bot', the official AI assistant for the Pak-Austria Fachhochschule: Institute of Applied Sciences and Technology. "
                "Your purpose is to assist students, parents, and visitors with accurate information about scholarships, admissions, faculty, and campus life. "
                "Always base your answers on the provided Context Information. If the context is insufficient, "
                "say: 'I'm sorry, I don't have specific details on that in my current records. Please visit https://paf-iast.edu.pk/ for the most up-to-date information.' "
                "Keep your tone professional, helpful, and welcoming. Cite the source URL if available in the context."
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
            print(f"\nPAF-IAST Bot: {answer}\n")
            
        except Exception as e:
            print(f"\nAn error occurred: {e}\n")

if __name__ == "__main__":
    main()
