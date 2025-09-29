import asyncio
from prod_assistant.utils.model_loader import ModelLoader
from ragas import SingleTurnSample
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import NonLLMContextPrecisionWithReference,ResponseRelevancy 
from grpc.experimental.aio import grpc_aio
