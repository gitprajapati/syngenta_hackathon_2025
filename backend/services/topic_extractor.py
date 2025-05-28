#services/topic_extractor.py
from pydantic import BaseModel, Field
from typing import List
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from services.ClaudeRunnable import LLM
from langchain_core.runnables import Runnable
from langchain_core.messages import AIMessage
from typing import Optional
from core.config import settings


class TopicSchema(BaseModel):
    topics: List[str] = Field(..., description="3 to 7 relevant high-level topics extracted from the document text.")


parser = PydanticOutputParser(pydantic_object=TopicSchema)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a professional knowledge extraction agent. Your task is to analyze text content and extract 3 to 7 high-level topics "
     "that best represent the main ideas in the text. The topics should help in classifying or routing agent if later any user asks any question so looking at these topics routing agent can reply back. "
     "Avoid vague or generic terms. Do not explain anything, just extract."),
    ("human", "{input_text}\n\n{format_instructions}")
])



def extract_topics_from_text(text: str, model: Optional[Runnable] = None) -> List[str]:
    """
    Uses an LLM and LangChain prompt structure to extract topics from text.
    """
    if not model:
        model = LLM(api_key=settings.SYN_MODEL_API_KEY,model_id='claude-3-haiku',temperature=0.2)

    chain = prompt | model | parser

    try:
        result: TopicSchema = chain.invoke({
            "input_text": text,
            "format_instructions": parser.get_format_instructions()
        })
        print()
        return result.topics
    except Exception as e:
        print(f"[Topic Extraction Error] {e}")
        return []
