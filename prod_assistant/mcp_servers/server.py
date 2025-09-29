from mcp.server.fastmcp import FastMCP
from langchain_community.tools import DuckDuckGoSearchRun
from prod_assistant.retriever.retrieval import Retriever



mcp = FastMCP('Hybrid_search')
retriever_obj = Retriever()
retriever = retriever_obj.load_retriever()
search = DuckDuckGoSearchRun()

def format_docs(docs):
    "format retriever docs into readable format"
    if not docs:
        return "No context found"
    format_chunks = []
    for d in docs:
        meta = d.metadata or {}
        formatted = (
            f"Title: {meta.get('product_title','N/A')}\n"
            f"Price: {meta.get('price','N/A')}\n"
            f"Rating: {meta.get('rating', 'N/A')}\n"
            f"Reviews: \n{d.page_content.strip()}"
        )
        format_chunks.append(formatted)
    return "\n\n".join(format_chunks)

@mcp.tool()
async def get_product_info(query: str):
    "retrieve product information for a given query"
    try:
        docs = retriever.invoke(query)
        context = format_docs(docs)
        if not context.strip():
            return "No context found"
    except Exception as e:
        return f"error in retrieving product info {e}"
    
@mcp.tool()
async def search_web(query: str):
    "search web for a given query"
    try:
        return search.run(query)
    except Exception as e:
        return f"error in searching web {e}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
    
    
        