import os
from langchain_astradb import AstraDBVectorStore
from typing import List
from langchain_core.documents import Document
from  prod_assistant.utils.config_loader import load_config
from prod_assistant.utils.model_loader import ModelLoader
from dotenv import load_dotenv


class Retriever:
    def __init__(self):
        self.model_loader = ModelLoader()
        self._load_env_variables()
        self.config = load_config()
        self.vstore = None
        self.retriever = None
        
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
        if not self.retriever:
            top_k = self.config['retriever']['top_k']
            self.retriever = self.vstore.as_retriever(search_kwargs={"k": top_k})
            print(f"Retriever Loaded successfully: {self.retriever}")
            return self.retriever
        
    def call_retriever(self,user_query):
        self.retriever = self.load_retriever()
        output = self.retriever.invoke(user_query)
        return output
    
if __name__=="__main__":
    retriever = Retriever()
    user_query = "What is the price of the product?"
    result  = retriever.call_retriever(user_query)
    
    for idx,doc in enumerate(result,1):
        print(f"Result {idx}:{doc.page_content}, Metadata: {doc.metadata}")
        
    