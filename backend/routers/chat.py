# routers/chat.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from schemas.chat import ChatRequest, ChatResponse, ChatMessageSchema
from services.rag_chatbot import runnable as rag_runnable, AgentState
from langchain.schema import HumanMessage, AIMessage, BaseMessage as LangchainBaseMessage, SystemMessage
from typing import List
from uuid import uuid4 

from core.database import get_db
from models.base_models import User as DBUser, Conversation, ChatMessage as DBChatMessage
from core.security import get_current_active_user 
from datetime import datetime

router = APIRouter(prefix="/chat", tags=["Chatbot"])

def convert_db_messages_to_langchain(db_messages: List[DBChatMessage]) -> List[LangchainBaseMessage]:
    lc_messages = []
    for msg in db_messages:
        if msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "ai":
            lc_messages.append(AIMessage(content=msg.content))
        elif msg.role == "system":
            lc_messages.append(SystemMessage(content=msg.content))
    return lc_messages

def convert_langchain_messages_to_schema(lc_messages: List[LangchainBaseMessage]) -> List[ChatMessageSchema]:
    schema_messages = []
    for msg in lc_messages:
        role = "unknown"
        if isinstance(msg, HumanMessage): role = "user"
        elif isinstance(msg, AIMessage): role = "ai"
        elif isinstance(msg, SystemMessage): role = "system"
        schema_messages.append(ChatMessageSchema(role=role, content=msg.content))
    return schema_messages


@router.post("/", response_model=ChatResponse)
async def handle_chat_message(
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    conversation: Conversation | None = None
    lc_history: List[LangchainBaseMessage] = []

    if chat_request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == chat_request.conversation_id,
            Conversation.user_id == current_user.id 
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found or access denied.")
        lc_history = convert_db_messages_to_langchain(conversation.messages)
    else:
        conversation = Conversation(user_id=current_user.id, title=chat_request.query[:100]) 
        db.add(conversation)
        db.commit() 
        db.refresh(conversation)

    user_db_message = DBChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=chat_request.query,
        user_id = current_user.id
    )
    db.add(user_db_message)

    current_human_message = HumanMessage(content=chat_request.query)
    messages_for_state = lc_history + [current_human_message]

    initial_state_input: AgentState = {
        "question": current_human_message,
        "messages": messages_for_state,
        "documents": [], "on_topic": "", "rephrased_question": "",
        "retrieval_intent_method": "", "hybrid_sql_question": ""
    }
    
    try:
        final_state = rag_runnable.invoke(initial_state_input)
    except Exception as e:
        db.rollback()
        print(f"Error invoking RAG runnable: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")

    if not final_state or 'messages' not in final_state or not final_state['messages']:
        db.rollback()
        raise HTTPException(status_code=500, detail="Chatbot returned an empty or invalid response state.")

    ai_response_lc_message = final_state['messages'][-1]
    if not isinstance(ai_response_lc_message, AIMessage):
        db.rollback()
        print(f"Warning: Last message from RAG was not an AIMessage. Type: {type(ai_response_lc_message)}")
        raise HTTPException(status_code=500, detail="Chatbot produced an unexpected response type.")
    
    ai_answer_content = ai_response_lc_message.content
        
    ai_db_message = DBChatMessage(
        conversation_id=conversation.id,
        role="ai",
        content=ai_answer_content,
        user_id = current_user.id
    )
    db.add(ai_db_message)

    conversation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(conversation) 
    full_updated_lc_history = convert_db_messages_to_langchain(conversation.messages)
    api_history_for_response = convert_langchain_messages_to_schema(full_updated_lc_history)
    
    return ChatResponse(
        answer=ai_answer_content,
        conversation_id=conversation.id,
        history=api_history_for_response 
    )

@router.get("/conversations", response_model=List[dict]) 
async def get_user_conversations(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    conversations = db.query(Conversation).filter(Conversation.user_id == current_user.id).order_by(Conversation.updated_at.desc()).all()
    return [
        {"id": conv.id, "title": conv.title, "created_at": conv.created_at, "updated_at": conv.updated_at} 
        for conv in conversations
    ]

@router.get("/conversations/{conversation_id}", response_model=List[ChatMessageSchema])
async def get_conversation_history(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied.")
    
    return convert_langchain_messages_to_schema(
        convert_db_messages_to_langchain(conversation.messages)
    )