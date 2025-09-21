from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai.embeddings import OpenAIEmbeddings
from prod_assistant.exception.custom_exception import ProductAssistantException
from prod_assistant.logger import GLOBAL_LOGGER as log
from prod_assistant.utils.config_loader import load_config
import asyncio
import json
import os
import sys

class ApiManager:
    REQUIRED_KEYS =['OPENAI_API_KEY','GOOGLE_API_KEY','GROQ_API_KEY']
    
    def __init__(self):
        self.api_keys = {}
        raw  = os.getenv("api_keys")
        
        if raw:
            try:
                parsed = json.load(raw)
                if not isinstance(parsed,dict):
                    raise ValueError("API keys must be a valid JSON object")
                self.api_keys = parsed
                log.info("API keys loaded from environment variable")
                
            except Exception as e:
                log.warning("Error parsing API keys from environment variable",error = str(e))
                
        for key in self.REQUIRED_KEYS:
            if not self.api_keys.get(key):
                eval_val = os.getenv(key)
                
                if eval_val:
                    self.api_keys[key]  = eval_val
                    log.info(f"API key {key} loaded from environment variable")
        #final check
        missing = [key for key in self.REQUIRED_KEYS if not self.api_keys.get(key)]
        if missing:
            log.error("missing api keys", missing_keys = missing)
            raise ProductAssistantException("Missing API keys",sys)
        log.info("API Keys loaded successfully")
    
    def get(self,key:str):
        val = self.api_keys.get(key)
        if not val:
            raise KeyError(f"API key {key} not found")
        return val
    
class ModelLoader:
    "load models based on config"
    def __init__(self):
        if os.getenv("ENV","local").lower() != 'production':
            load_dotenv(override =True)
            load_dotenv()
            log.info('Running in local,env loaded')
        else:
            log.info('Running in Production mode')
            
        self.api_key_mgr = ApiManager()
        self.config  = load_config()
        log.info("Config loaded successfully",config_keys = list(self.config.keys()))
            
    def load_embedding_model(self):
        try:
            model_name = self.config['embedding_model']['model_name']
            log.info("Loading embedding model", model_name = model_name)
                
            try:
                asyncio.get_event_loop()
            except RuntimeError:
                asyncio.set_event_loop(asyncio.new_event_loop())
                
            return OpenAIEmbeddings(model=model_name,api_key = self.api_key_mgr.get("OPENAI_API_KEY"))
        except Exception as e:
            log.error("Error loading embedding model", error = str(e))
            raise ProductAssistantException("Error loading embedding model", sys)
    def load_llm(self):
        llm_block = self.config['llm']
        provider = os.getenv('LLM_PROVIDER','openai')
                
        if provider not in llm_block:
            log.error(f"Provider {provider} not found in config")
            raise ValueError(f"Provider {provider} not found in config")
                
        llm_config = llm_block[provider]
        provider = llm_config.get('provider')
        model_name = llm_config.get('model_name')
        temperature = llm_config.get('temprature',0.2)
        max_tokens = llm_config.get('max_output_tokens', 1000)
                
        log.info('Loading LLM',provider = provider, model_name = model_name)
                
        if provider == 'openai':
            return ChatOpenAI(model_name = model_name, api_key = self.api_key_mgr.get("OPENAI_API_KEY"), temperature=temperature, max_tokens = max_tokens) 
                    
        elif provider == 'google':
            return ChatGoogleGenerativeAI(model = model_name, api_key = self.api_key_mgr.get("GOOGLE_API_KEY"), temperature=temperature, max_tokens = max_tokens)
        elif provider  == 'groq':
            return ChatGroq(model = model_name, api_key = self.api_key_mgr.get("GROQ_API_KEY"), temperature=temperature, max_tokens = max_tokens)
                
        else:
            log.error("unsupported LLM provider",provider = provider)
            raise ValueError(f"Unsupported LLM provider {provider}")

if __name__ == "__main__":
    loader = ModelLoader()

    # Test Embedding
    embeddings = loader.load_embedding_model()
    print(f"Embedding Model Loaded: {embeddings}")
    result = embeddings.embed_query("Hello, how are you?")
    print(f"Embedding Result: {result}")

    # Test LLM
    llm = loader.load_llm()
    print(f"LLM Loaded: {llm}")
    result = llm.invoke("Hello, how are you?")
    print(f"LLM Result: {result.content}")
                
    
                
                
            
                    
                
                
                
                
                
        
        
        
            
                