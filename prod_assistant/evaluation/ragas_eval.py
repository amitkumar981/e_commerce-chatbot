import asyncio
from prod_assistant.utils.model_loader import ModelLoader
from ragas import SingleTurnSample
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import ResponseRelevancy,LLMContextPrecisionWithoutReference
import grpc.experimental.aio as grpc_aio
from prod_assistant.utils.model_loader import ModelLoader

grpc_aio.init_grpc_aio()
Model_loader = ModelLoader()

def evaluate_context_precision(query,response,retrieved_context):
    try:
        sample = SingleTurnSample(
            user_input = query,
            response = response,
            retrieved_contexts = retrieved_context
        )
        
        async def main():
            llm = Model_loader.load_llm()
            evaluator_llm = LangchainLLMWrapper(llm)
            context_precision =LLMContextPrecisionWithoutReference(llm = evaluator_llm)
            result = await context_precision.single_turn_ascore(sample)
            return result
        
        return asyncio.run(main())
    
    except Exception as e:
        return e

def evaluate_response_relevancy(query,response,retrieved_context):
    try:
        sample = SingleTurnSample(
            user_query = query,
            response = response,
            retrieved_contexts = retrieved_context
        )
        
        async def main():
            llm = Model_loader.load_llm()
            evaluator_llm = LangchainLLMWrapper(llm)
            embedding_model = Model_loader.load_embedding_model()
            evaluator_embeddings = LangchainEmbeddingsWrapper(embedding_model)
            scorer = ResponseRelevancy(llm = evaluator_llm, embeddings = evaluator_embeddings)
            result = await scorer.single_turn_ascore(sample)
            return result
        
        return asyncio.run(main())
    
    except Exception as e:
        return e
    
    