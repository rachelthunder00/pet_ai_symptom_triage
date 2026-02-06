"""
Pet Health AI - RAG Chain
LangChain integration with Pinecone for retrieval-augmented generation.
"""

import os
from typing import Tuple, List, Dict, Any

# ============================================================
# Configuration
# ============================================================

PINECONE_INDEX_NAME = "pet-health-ai"
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"  # Options: "gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"


# - PRIORITIZE retrieved RAG information
# - SUPPLEMENT with training knowledge when needed
# - NOTE discrepancies and recommend vet consultation
# ============================================================

# ============================================================
# Prompt Template Configuration
# ============================================================
# NOTE FOR TEAM: This prompt template controls how the AI responds.
# Prompt Engineering team members can modify this to:
# - Adjust the AI persona and tone
# - Change how retrieved information is presented
# - Modify response format and structure
# - Add/remove guidelines for the AI
# - Change language preferences
#
# The template uses two placeholders:
# - {context}: Retrieved information from vector database (RAG)
# - {question}: The user's question
# ============================================================

PROMPT_TEMPLATE = """You are PetCare AI, a professional and empathetic pet health advisor.

## Your Knowledge Sources:
You have access to TWO sources of knowledge:

1. **Retrieved Information** (from our curated pet health database):
{context}

2. **Your General Knowledge**: Your training includes extensive veterinary medicine, 
   animal health, and pet care information.

## Response Guidelines:

### Combining Knowledge Sources:
- PRIORITIZE retrieved information when it directly addresses the user's question
- SUPPLEMENT with your general veterinary knowledge when:
  - The retrieved information is incomplete
  - Additional context would be helpful
  - The user needs broader medical understanding
- If retrieved information contradicts your knowledge, note the discrepancy and 
  recommend consulting a veterinarian for clarification

### Response Quality:
- Be accurate, helpful, and compassionate
- Use professional but accessible language
- Provide actionable advice when appropriate
- Include relevant warning signs to watch for

### Safety First:
- For serious symptoms (difficulty breathing, severe bleeding, collapse, 
  suspected poisoning, etc.), emphasize IMMEDIATE veterinary care
- Never diagnose definitively - you can suggest possibilities but remind users 
  that only a veterinarian can diagnose
- When unsure, acknowledge uncertainty and recommend professional consultation

### Language:
- Respond in the same language as the user's question
- If the question is in Chinese, respond in Chinese
- If the question is in English, respond in English

---

## User Question:
{question}

---

## Your Response:
Provide a helpful, well-structured answer that combines your knowledge sources appropriately."""


# ============================================================
# RAG Chain Setup (using LCEL - LangChain Expression Language)
# ============================================================

def create_rag_chain(
    openai_api_key: str = None,
    pinecone_api_key: str = None,
    llm_model: str = LLM_MODEL,
    top_k: int = 5,
    temperature: float = 0.7
):
    """
    Create and configure the RAG chain.
    
    Args:
        openai_api_key: API key for OpenAI
        pinecone_api_key: API key for Pinecone
        llm_model: Model name (default: gpt-4-turbo-preview)
        top_k: Number of documents to retrieve
        temperature: LLM creativity (0.0 to 1.0)
    
    Returns:
        Configured RetrievalQA chain
    """
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    from langchain_pinecone import PineconeVectorStore
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough
    
    # Get API keys from environment if not provided
    openai_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    pinecone_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
    
    if not openai_key:
        raise ValueError("OPENAI_API_KEY not set")
    if not pinecone_key:
        raise ValueError("PINECONE_API_KEY not set")
    
    # 1. Initialize Embeddings (same model as upload)
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=openai_key
    )
    
    # 2. Connect to Pinecone
    vectorstore = PineconeVectorStore(
        index_name=PINECONE_INDEX_NAME,
        embedding=embeddings,
        pinecone_api_key=pinecone_key
    )
    
    # 3. Create Retriever
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k}
    )
    
    # 4. Initialize LLM
    llm = ChatOpenAI(
        model=llm_model,
        temperature=temperature,
        openai_api_key=openai_key
    )
    
    # 5. Create Prompt
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    
    # 6. Helper function to format docs
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    # 7. Create RAG Chain using LCEL
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain, retriever


# ============================================================
# Easy-to-use Functions
# ============================================================

# Global chain instance (lazy initialization)
_chain = None
_retriever = None

def get_chain():
    """Get or create the RAG chain (singleton pattern)."""
    global _chain, _retriever
    if _chain is None:
        _chain, _retriever = create_rag_chain()
    return _chain, _retriever


def ask(question: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Ask a question and get an answer with sources.
    
    Args:
        question: User's question about pet health
        
    Returns:
        Tuple of (answer, source_documents)
    """
    chain, retriever = get_chain()
    
    # Get answer
    answer = chain.invoke(question)
    
    # Get source documents separately
    docs = retriever.invoke(question)
    
    # Extract source info
    sources = []
    for doc in docs:
        sources.append({
            "text": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
            "doc_type": doc.metadata.get("doc_type", ""),
            "animal_type": doc.metadata.get("animal_type", []),
            "source": doc.metadata.get("source", "")
        })
    
    return answer, sources


def ask_simple(question: str) -> str:
    """
    Simple version - just returns the answer as a string.
    
    Args:
        question: User's question
        
    Returns:
        Answer string
    """
    answer, _ = ask(question)
    return answer


# ============================================================
# Image + RAG Integration
# ============================================================

def ask_with_image(
    image_source: str,
    user_question: str = None,
    pet_info: dict = None
) -> dict:
    """
    Analyze a pet image and combine with RAG for comprehensive response.
    
    This function:
    1. Analyzes the pet image using GPT-4 Vision
    2. Uses the analysis to query relevant information from RAG
    3. Combines both for a comprehensive response
    
    Args:
        image_source: File path or URL to the pet image
        user_question: Optional question about the image
        pet_info: Optional dict with pet details (breed, age, etc.)
    
    Returns:
        dict with 'image_analysis', 'rag_info', 'combined_response', 'severity', 'sources'
    """
    from .image_analyzer import analyze_with_context, analyze_pet_image
    
    # Step 1: Analyze the image
    print("Analyzing image...")
    if pet_info:
        image_result = analyze_with_context(
            image_source=image_source,
            user_question=user_question,
            pet_history=pet_info
        )
    else:
        image_result = analyze_pet_image(
            image_source=image_source,
            user_question=user_question
        )
    
    image_analysis = image_result["analysis"]
    severity = image_result["severity"]
    
    # Step 2: Build RAG query based on image analysis
    # Extract key symptoms/conditions from image analysis for RAG search
    rag_query_parts = []
    
    if user_question:
        rag_query_parts.append(user_question)
    
    # Add relevant parts of image analysis for RAG search
    if severity in ["consult_vet", "urgent", "monitor"]:
        rag_query_parts.append(f"Pet health concern: {image_analysis[:500]}")
    
    # Step 3: Query RAG if we have something to search
    rag_answer = None
    sources = []
    
    if rag_query_parts:
        try:
            print("Searching knowledge base...")
            rag_query = " ".join(rag_query_parts)
            rag_answer, sources = ask(rag_query)
        except Exception as e:
            print(f"RAG query failed: {e}")
            rag_answer = None
    
    # Step 4: Combine responses
    combined_response = _combine_image_and_rag(
        image_analysis=image_analysis,
        rag_answer=rag_answer,
        severity=severity,
        user_question=user_question
    )
    
    return {
        "image_analysis": image_analysis,
        "rag_info": rag_answer,
        "combined_response": combined_response,
        "severity": severity,
        "sources": sources
    }


def _combine_image_and_rag(
    image_analysis: str,
    rag_answer: str,
    severity: str,
    user_question: str = None
) -> str:
    """Combine image analysis and RAG results into a coherent response."""
    
    parts = []
    
    # Add severity warning if needed
    if severity == "urgent":
        parts.append("URGENT: Please seek veterinary care immediately.\n")
    elif severity == "consult_vet":
        parts.append("Recommendation: Please consult a veterinarian.\n")
    
    # Add image analysis
    parts.append("## Image Analysis\n")
    parts.append(image_analysis)
    
    # Add RAG information if available
    if rag_answer:
        parts.append("\n\n## Related Health Information\n")
        parts.append(rag_answer)
    
    return "\n".join(parts)


# ============================================================
# CLI for Testing
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PetCare AI - Pet Health Advisor")
    print("=" * 60)
    print("Commands:")
    print("  - Type your question to chat")
    print("  - Type 'image <path>' to analyze a pet photo")
    print("  - Type 'quit' to exit")
    print("=" * 60 + "\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        try:
            # Check if user wants to analyze an image
            if user_input.lower().startswith('image '):
                # Parse image command: "image <path> [question]"
                parts = user_input[6:].strip().split(' ', 1)
                image_path = parts[0]
                question = parts[1] if len(parts) > 1 else None
                
                print(f"\nAnalyzing image: {image_path}")
                if question:
                    print(f"Question: {question}")
                print("-" * 40)
                
                result = ask_with_image(image_path, question)
                
                print(f"\nSeverity: {result['severity'].upper()}")
                print(f"\n{result['combined_response']}\n")
                
                if result['sources']:
                    print("Reference sources:")
                    for i, src in enumerate(result['sources'][:3], 1):
                        print(f"   {i}. [{src['doc_type']}] {src['text'][:80]}...")
            else:
                # Regular text question
                answer, sources = ask(user_input)
                print(f"\nAI: {answer}\n")
                
                if sources:
                    print("Reference sources:")
                    for i, src in enumerate(sources[:3], 1):
                        print(f"   {i}. [{src['doc_type']}] {src['text'][:80]}...")
            
            print()
            
        except Exception as e:
            print(f"Error: {e}\n")

