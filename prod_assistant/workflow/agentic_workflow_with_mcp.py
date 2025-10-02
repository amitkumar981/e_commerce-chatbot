
from typing import Annotated, Sequence, TypedDict, Literal
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from prod_assistant.prompt_library.prompts import PromptType, PROMPT_REGISTRY
from prod_assistant.utils.model_loader import ModelLoader
from langgraph.checkpoint.memory import MemorySaver
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio


class AgenticRAG:
    """AgenticRAG pipeline using Langgraph and MCP Server"""

    class AgentState(TypedDict):
        messages: Annotated[Sequence[BaseMessage], add_messages]

    def __init__(self):
        self.model_loader = ModelLoader()
        self.llm = self.model_loader.load_llm()
        self.checkpointer = MemorySaver()

        self.mcp_client = MultiServerMCPClient(
            {
                "hybrid_search": {
                    "transport": "streamable_http",
                    "url": "http://localhost:8000/mcp"
                }
            }
        )

        self.mcp_tools = None
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile(checkpointer=self.checkpointer)

    async def async_init(self):
        """Initialize async dependencies (must be awaited before use)"""
        self.mcp_tools = await self.mcp_client.get_tools()

    def _ai_assistant(self, state: AgentState):
        print("calling ai_assistant... ")
        last_message = state["messages"][-1].content

        if any(word in last_message.lower() for word in ['price', 'review', 'product']):
            return {"messages": [HumanMessage(content="TOOL: retriever")]}
        else:
            prompt = ChatPromptTemplate.from_template(
                "You are a helpful assistant. Answer the user directly.\n\nQuestion: {question}\nAnswer:"
            )
            chain = prompt | self.llm | StrOutputParser()
            response = chain.invoke({"question": last_message})
            return {"messages": [HumanMessage(content=response)]}

    async def _vector_retriever(self, state: AgentState):
        print("calling vector_retriever... ")
        query = state["messages"][-1].content
        tool = next(t for t in self.mcp_tools if t.name == "get_product_info")

        result = await tool.ainvoke({"query": query})
        context = result if result else "No context found"
        return {"messages": [HumanMessage(content=context)]}

    def _web_search(self, state: AgentState):
        print("calling web_search...")
        query = state["messages"][-1].content
        tool = next(t for t in self.mcp_tools if t.name == "search_web")

        result =  asyncio.run(tool.ainvoke({"query": query}))
        context = result if result else "No data from web"
        return {"messages": [HumanMessage(content=context)]}
    
    def _grade_documents(self, state: AgentState) -> Literal["Generator", "Rewriter"]:
        print("calling grade_documents...")
        question = state['messages'][0].content
        docs = state['messages'][-1].content

        prompt = PromptTemplate(
            template="""You are a grader.
            Question: {question}
            Docs: {docs}
            Are docs relevant to the question? Answer yes or no""",
            input_variables=['question', 'docs']
        )

        chain = prompt | self.llm | StrOutputParser()
        score = chain.invoke({"question": question, "docs": docs})

        return "Generator" if "yes" in score.lower() else "Rewriter"

    def _generate(self, state: AgentState):
        print("calling generate..")
        question = state['messages'][0].content
        docs = state['messages'][-1].content
        prompt = ChatPromptTemplate.from_template(
            PROMPT_REGISTRY[PromptType.PRODUCT_BOT].template
        )
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({"context": docs, "question": question})
        return {"messages": [HumanMessage(content=response)]}

    def _rewriter(self, state: AgentState):
        print("calling rewriter...")
        question = state['messages'][0].content
        prompt = ChatPromptTemplate.from_template(
            "Rewrite this user query to make it more clear and specific for a search engine. "
            "Do NOT answer the query. Only rewrite it.\n\nQuery: {question}\nRewritten Query:"
        )
        chain = prompt | self.llm | StrOutputParser()
        new_question = chain.invoke({"question": question})
        return {"messages": [HumanMessage(content=new_question.strip())]}

    def _build_workflow(self):
        workflow = StateGraph(self.AgentState)

        workflow.add_node("Assistant", self._ai_assistant)
        workflow.add_node("Retriever", self._vector_retriever)
        workflow.add_node("Generator", self._generate)
        workflow.add_node("Rewriter", self._rewriter)
        workflow.add_node("WebSearch", self._web_search)

        workflow.add_edge(START, "Assistant")

        workflow.add_conditional_edges(
            "Assistant",
            lambda state: "Retriever" if "TOOL" in state["messages"][-1].content else END,
            {"Retriever": "Retriever", END: END}
        )

        workflow.add_conditional_edges(
            "Retriever", self._grade_documents,
            {"Generator": "Generator", "Rewriter": "Rewriter"}
        )

        workflow.add_edge("Generator", END)
        workflow.add_edge("Rewriter", 'WebSearch')
        workflow.add_edge("WebSearch", "Generator")

        return workflow

    async def run(self, query: str, thread_id: str = 'default_thread') -> str:
        """Run workflow for a given query (async)"""
        result = await self.app.ainvoke(
            {"messages": [HumanMessage(content=query)]},
            config={"configurable": {"thread_id": thread_id}}
        )
        return result['messages'][-1].content

if __name__ == "__main__":
    async def main():
        agentic_rag = AgenticRAG()
        await agentic_rag.async_init()
        result = await agentic_rag.run("What is the price of iPhone 16?")
        print("\n\nFinal Result: ", result)

    asyncio.run(main())
