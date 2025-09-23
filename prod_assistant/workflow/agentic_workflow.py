from typing import Annotated,Sequence,TypedDict,Literal
from langchain_core.messages import BaseMessage,HumanMessage
from langchain_core.prompts import ChatPromptTemplate,PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages

from prod_assistant.prompt_library.prompts import PromptType,PROMPT_REGISTRY
from prod_assistant.retriever.retrieval import Retriever
from prod_assistant.utils.model_loader import ModelLoader
from langgraph.checkpoint.memory import MemorySaver
import asyncio

class AgenticRAG:
    "Agentic RAG Workflow"
    class AgenticState(TypedDict):
        messages: Annotated[Sequence[BaseMessage],add_messages] # type: ignore
        
    def __init__(self):
        self.retriever = Retriever()
        self.model_loader = ModelLoader()
        self.llm = self.model_loader.load_llm()
        self.checkpointer = MemorySaver()
        self.graph_builder = self._build_graph()
        self.app = self.graph_builder.compile(checkpointer=self.checkpointer)
        
    def _format_docs(self,docs):
        if not docs:
            return "No relevant information found."
        formatted_chunks = []
        for d in docs:
            meta = d.metadata or {}
            formatted = (
                f"Title: {meta.get('product_title','N/A')}\n"
                f"Price: {meta.get('price','N/A')}\n"
                f"Rating: {meta.get('rating', 'N/A')}\n"
                f"Reviews: \n{d.page_content.strip()}"
            )
            formatted_chunks.append(formatted)
        return "\n\n".join(formatted_chunks)
    
    def _ai_assistant(self,state:AgenticState):
        print("calling ai_assistant... ")
        last_message = state["messages"][-1].content
        
        if any(word in last_message.lower() for word in ['price','Reviews','product','rating']):
            return {"messages": [HumanMessage(content = "TOOL: retriever")]}
        else:
            prompt = ChatPromptTemplate.from_template(
                "you are a helpful assistant. Answer the user directly./n/n Question: {question}\nAnswer:"
            )
            chain = prompt | self.llm | StrOutputParser()
            response = chain.invoke({"question": last_message})
            return {"messages": [HumanMessage(content = response.content)]}
    
    def _vector_retriever(self,state: AgenticState):
        print("calling vector_retriever... ")
        query = state["messages"][-1].content
        retriever = self.retriever.load_retriever()
        docs = retriever.invoke(query)
        context  = self._format_docs(docs)
        return {"messages": [HumanMessage(content = context)]}
    
    def _grade_documents(self,state:AgenticState):
        print("calling grade_documents...")
        question = state['messages'][0].content
        docs = state['messages'][-1].content
        
        prompt = PromptTemplate(
            template = """you are a grader.question: {question}\ndocs: {docs}\n
            Are docs are relevant to the question? answer yes or no""",
            input_variables = ['question','docs']
        )
        
        chain = prompt | self.llm | StrOutputParser()
        score = chain.invoke({"question": question, "docs": docs})
        
        return "generator" if "yes" in score.lower() else "rewriter"
    
    def _generate(self,state: AgenticState):
        print("calling generate..")
        question = state['messages'][0].content
        docs = state['messages'][-1].content
        prompt = ChatPromptTemplate.from_template(
            PROMPT_REGISTRY[PromptType.PRODUCT_BOT].template
        )
        chain  = prompt | self.llm | StrOutputParser()
        response = chain.invoke({"context": docs, "question": question})
        return {"messages": [HumanMessage(content = response)]}
    
    def _rewriter(self,state: AgenticState):
        print("calling rewriter...")
        question = state['messages'][0].content
        new_question  = self.llm.invoke(
            [HumanMessage(content = f"Rewrite the question: {question}")]
        )
        return [HumanMessage(content = new_question.content)]
    
    
    def _build_graph(self):
        builder  = StateGraph(self.AgenticState)
        
        builder.add_node("ai_assistant", self._ai_assistant)
        builder.add_node('retriever',self._vector_retriever)
        builder.add_node('generator',self._generate)
        builder.add_node('rewriter',self._rewriter)
        
        #add edges
        builder.add_edge(START,'ai_assistant')
        builder.add_conditional_edges('ai_assistant',
                                    lambda state: 'retriever' if 'TOOL' in state['messages'][-1].content else 'END'
                                    )
        builder.add_conditional_edges(
            'retriever',
            self._grade_documents,
            {
                'generator': 'generator',
                'rewriter': 'rewriter'
            }
        )
        builder.add_edge("generator",END)
        builder.add_edge("rewriter", 'ai_assistant')
        return builder
    
    def run(self,query:str,thread_id: str = 'default_thread') -> str:
        "run workflow for a given query"
        result = self.app.invoke({"messages": [HumanMessage(content = query)]}, config = {"configurable": {"thread_id": thread_id}})
        return result['messages'][-1].content
if __name__=='__main__':
    agentic_rag = AgenticRAG()
    result = agentic_rag.run("What is the price of the product?")
    print(result)
    
    
        

        
        