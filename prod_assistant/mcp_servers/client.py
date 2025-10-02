import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

async def main():
    client = MultiServerMCPClient({
        "hybrid_search": {
            "command": "python",
            "args": [
                r"C:\Users\redhu\OneDrive\Desktop\eccom_prod_assistant\prod_assistant\mcp_servers\server.py"
            ],
            "transport": "streamable-http",
            "url": "http://localhost:8000/mcp"
        }
    })
    
    tools = await client.get_tools()
    print("available tools: ",[t.name for t in tools])
    
    retriever_tool  = next(t for t in tools if t.name == "get_product_info")
    web_search_tool = next(t for t in tools if t.name == "search_web")
    
    query = "iphone 17"
    
    retriever_result = await retriever_tool.ainvoke({"query": query})
    print("retriever result: ", retriever_result)
    
    if not retriever_result.strip():
        web_search_result = await web_search_tool.ainvoke({"query": query})
        print("web search result:", web_search_result)
        
if __name__ == "__main__":
    asyncio.run(main())
    