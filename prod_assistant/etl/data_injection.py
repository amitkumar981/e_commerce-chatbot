import os
import pandas as pd
from dotenv import load_dotenv
from typing import List 
from langchain_core.documents import Document
from langchain_astradb import AstraDBVectorStore
from prod_assistant.utils.model_loader import ModelLoader
from prod_assistant.utils.config_loader import load_config

class DataIngestion:
    def __init__(self):
        print("initializing DataIngestion pipelines....")
        self.model_loader = ModelLoader()
        self._load_env_var()
        self.csv_path = self._get_csv_path()
        self.product_data = self._load_csv()
        self.config = load_config()
    def _load_env_var(self):
        "load and validate the required the environment variables"
        load_dotenv()
        required_keys = ['OPENAI_API_KEY','ASTRA_DB_API_ENDPOINT','ASTRA_DB_APPLICATION_TOKEN','ASTRA_DB_KEYSPACE']
        missing_var = [var for var in required_keys if os.getenv(var) is None]
        if missing_var:
            raise ValueError(f"Missing required environment variables: {missing_var}")
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.ASTRA_DB_API_ENDPOINT = os.getenv('ASTRA_DB_API_ENDPOINT')
        self.ASTRA_DB_APPLICATION_TOKEN = os.getenv('ASTRA_DB_APPLICATION_TOKEN')
        self.ASTRA_DB_KEYSPACE = os.getenv('ASTRA_DB_KEYSPACE')
        
    def  _get_csv_path(self):
        "get the csv path located inside the 'data' folder"
        csv_path = os.path.join(os.getcwd(),'data','product_reviews.csv')
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found at {csv_path}")
        return csv_path
        
    def _load_csv(self):
        " load product data from csv"
        df = pd.read_csv(self.csv_path)
        expected_columns = {'product_id','product_title', 'rating', 'total_reviews','price', 'top_reviews'}
        if not expected_columns.issubset(df.columns):
            raise ValueError(f"CSV file does not contain all expected columns: {expected_columns}")
        return df 
    
    def transform(self):
        "Transform product data into list of LangChain Document object"
        product_list = []
        for _,rows in self.product_data.iterrows():
            product_entry={
                'product_id':rows['product_id'],
                'product_title':rows['product_title'],
                'rating':rows['rating'],
                'total_reviews':rows['total_reviews'],
                'price':rows['price'],
                'top_reviews':rows['top_reviews']
            }
            product_list.append(product_entry)
        
        documents =[]
        for entry in product_list:
            metadata = {
                'product_id':entry['product_id'],
                'product_title':entry['product_title'],
                'rating':entry['rating'],
                'total_reviews':entry['total_reviews'],
                'price':entry['price']
            }
            doc = Document(page_content=entry['top_reviews'],metadata=metadata)
            documents.append(doc)
        print(f"Transformed {len(documents)} documents")
        return documents
    def store_in_vector_db(self,documents: List[Document]):
        "store documents into database"
        collection_name = self.config['astra_db']['collection_name']
        vstore = AstraDBVectorStore(
            embedding=self.model_loader.load_embedding_model(),
            collection_name=collection_name,
            api_endpoint=self.ASTRA_DB_API_ENDPOINT,
            token=self.ASTRA_DB_APPLICATION_TOKEN,
        )
        inserted_ids = vstore.add_documents(documents)
        print(f"Inserted {len(inserted_ids)} documents into the vector database")
        return vstore,inserted_ids
    def run_pipeline(self):
        "run full data ingestion pipelines"
        documents = self.transform()
        vstore,_ =  self.store_in_vector_db(documents)
        
        #Optionally do a quick search
        query = "Can you tell me the low budget iphone?"
        results = vstore.similarity_search(query)

        print(f"\nSample search results for query: '{query}'")
        for res in results:
            print(f"Content: {res.page_content}\nMetadata: {res.metadata}\n")

# Run if this file is executed directly
if __name__ == "__main__":
    ingestion = DataIngestion()
    ingestion.run_pipeline()
        
    
    
    
    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        