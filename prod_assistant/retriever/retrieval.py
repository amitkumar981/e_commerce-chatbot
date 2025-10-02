import os
from langchain_astradb import AstraDBVectorStore
from langchain.retrievers.document_compressors import LLMChainFilter
from langchain.retrievers import ContextualCompressionRetriever
from typing import List
from langchain_core.documents import Document
from  prod_assistant.utils.config_loader import load_config
from prod_assistant.utils.model_loader import ModelLoader
from prod_assistant.evaluation.ragas_eval import evaluate_context_precision,evaluate_response_relevancy
from dotenv import load_dotenv


class Retriever:
    def __init__(self):
        self.model_loader = ModelLoader()
        self._load_env_variables()
        self.config = load_config()
        self.vstore = None
        self.retriever_instance = None
        
    def _load_env_variables(self):
        load_dotenv()
        required_keys = ['OPENAI_API_KEY','ASTRA_DB_API_ENDPOINT','ASTRA_DB_APPLICATION_TOKEN','ASTRA_DB_KEYSPACE']
        missing_vars = [var for var in required_keys if os.getenv(var) is None]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.ASTRA_DB_API_ENDPOINT = os.getenv('ASTRA_DB_API_ENDPOINT')
        self.ASTRA_DB_APPLICATION_TOKEN = os.getenv('ASTRA_DB_APPLICATION_TOKEN')
        self.ASTRA_DB_KEYSPACE = os.getenv('ASTRA_DB_KEYSPACE')
        
    def load_retriever(self):
        if not self.vstore:
            collection_name = self.config['astra_db']['collection_name']
            
            self.vstore = AstraDBVectorStore(
                embedding=self.model_loader.load_embedding_model(),
                collection_name=collection_name,
                token=self.ASTRA_DB_APPLICATION_TOKEN,
                api_endpoint=self.ASTRA_DB_API_ENDPOINT,
                namespace=self.ASTRA_DB_KEYSPACE
            )
        if not self.retriever_instance:
            top_k = self.config["retriever"]["top_k"] if "retriever" in self.config else 3
            
            mmr_retriever=self.vstore.as_retriever(
                search_type="mmr",
                search_kwargs={"k": top_k,
                                "fetch_k": 20,
                                "lambda_mult": 0.7,
                                "score_threshold": 0.6
                            })
            print("Retriever loaded successfully.")
            
            llm = self.model_loader.load_llm()
            
            compressor=LLMChainFilter.from_llm(llm)
            
            self.retriever_instance = ContextualCompressionRetriever(
                base_compressor=compressor, 
                base_retriever=mmr_retriever
            )
            
        return self.retriever_instance
        
    def call_retriever(self,user_query):
        retriever = self.load_retriever()
        output = retriever.invoke(user_query)
        return output
    
if __name__=='__main__':
    user_query = "Can you suggest good budget iPhone under 1,00,00 INR?"
    
    retriever_obj = Retriever()
    
    retrieved_docs = retriever_obj.call_retriever(user_query)
    
    def _format_docs(docs) -> str:
        if not docs:
            return "No relevant documents found."
        formatted_chunks = []
        for d in docs:
            meta = d.metadata or {}
            formatted = (
                f"Title: {meta.get('product_title', 'N/A')}\n"
                f"Price: {meta.get('price', 'N/A')}\n"
                f"Rating: {meta.get('rating', 'N/A')}\n"
                f"Reviews:\n{d.page_content.strip()}"
            )
            formatted_chunks.append(formatted)
        return "\n\n---\n\n".join(formatted_chunks)
    
    retrieved_contexts = [_format_docs(doc) for doc in retrieved_docs]
    
    #this is not an actual output this have been written to test the pipeline
    response="iphone 16 plus, iphone 16, iphone 15 are best phones under 1,00,000 INR."
    
    context_score = evaluate_context_precision(user_query,response,retrieved_contexts)
    relevancy_score = evaluate_response_relevancy(user_query,response,retrieved_contexts)
    
    print("\n--- Evaluation Metrics ---")
    print("Context Precision Score:", context_score)
    print("Response Relevancy Score:", relevancy_score)
    
        
    