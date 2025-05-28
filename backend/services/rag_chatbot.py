# services/rag_chatbot.py
from typing import List, TypedDict
from langchain.schema import BaseMessage, HumanMessage, AIMessage, Document, SystemMessage
from langchain.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import initialize_agent, AgentType
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
import os
from langchain_community.vectorstores import FAISS 
from pydantic import BaseModel, Field

from services.customeEmbedingModel import ClientAPIEmbeddings 
from core.config import settings



llm_default = ChatGroq(model="llama3-70b-8192", api_key=settings.GROK_API_KEY, temperature=0.2)
llm_fast = ChatGroq(model="llama3-70b-8192", api_key=settings.GROK_API_KEY, temperature=0.2)
groq_llm=ChatGroq(model="llama3-70b-8192", api_key=settings.GROK_API_KEY, temperature=0.6)

# Embeddings & vector store
emb = ClientAPIEmbeddings(api_key=settings.SYN_MODEL_API_KEY)
vector_path = settings.VECTOR_STORE_PATH 

vectorstore = None
retriever = None


if vector_path and os.path.exists(vector_path) and os.listdir(vector_path): 
    try:
        vectorstore = FAISS.load_local(vector_path, emb, allow_dangerous_deserialization=True)
        retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 5})
        print(f"Successfully loaded vector store from {vector_path}")
    except Exception as e:
        print(f"Error loading vector store from {vector_path}: {e}. Document retrieval will be limited.")
        vectorstore = None
        retriever = None
else:
    print(f"Vector store path {vector_path} not found, empty, or not configured. Document retrieval will be unavailable.")
    vectorstore = None
    retriever = None



# Define shared RAG prompt
template = '''Answer the question based on the following context and the Chathistory.
Especially take the latest question into consideration.
**Use Markdown for formatting your answer when appropriate, such as for titles, lists, bolding key terms, or code blocks if you are showing a query.**
**When presenting numerical data from the 'Context', ensure the numbers are copied exactly as provided in the 'Context'. You may add currency symbols or commas for readability, but the core numerical value itself must not be altered (e.g., do not add or remove digits or change its magnitude).**

Chathistory: {history}

Context: {context}

Question: {question}
'''
prompt_template = ChatPromptTemplate.from_template(template) 
rag_chain = prompt_template | llm_default


# AgentState definition
class AgentState(TypedDict):
    messages: List[BaseMessage]
    documents: List[Document]
    on_topic: str
    rephrased_question: str
    question: HumanMessage
    retrieval_intent_method: str
    hybrid_sql_question: str


# ------------- Question Rewriting and Classification -------------

def question_rewriter(state: AgentState):
    print(f"Entering question_rewriter with current question: {state['question'].content}")
    if 'messages' not in state or state['messages'] is None:
        state['messages'] = [] 

    state["documents"] = []
    state["on_topic"] = ""
    state["rephrased_question"] = ""
    state['retrieval_intent_method'] = ""
    state['hybrid_sql_question'] = ""


    current_question_content = state['question'].content

 
    if len(state['messages']) > 1:
        history_prior_to_current_question = state['messages'][:-1]


        human_only_history_for_rephrasing = [
            msg for msg in history_prior_to_current_question if isinstance(msg, HumanMessage)
        ]
  
        system_message_content = """You are an expert query rewriter. Your primary goal is to rephrase the 'Latest user question' into a clear, self-contained question optimized for information retrieval.

        Instructions:
        1.  **Focus entirely on the 'Latest user question'.** This is the most important piece of information.
        2.  If 'Previous User Questions' are provided, use them *only* to understand the context of the 'Latest user question', especially for resolving pronouns (e.g., "it", "that") or if the latest question is very short.
        3.  Do NOT invent information or infer too much from previous questions. The rephrased question must accurately reflect the user's *latest* intent.
        4.  The rephrased question must be standalone and understandable without needing to read any prior conversation not explicitly provided here.
        """

        msgs_for_rephrasing = [SystemMessage(content=system_message_content)]

        if human_only_history_for_rephrasing:
            for human_msg in human_only_history_for_rephrasing:
                msgs_for_rephrasing.append(HumanMessage(content=f"A Previous User Question: {human_msg.content}"))
        
        msgs_for_rephrasing.append(HumanMessage(content=f"Latest user question to rephrase: {current_question_content}"))
        
        rephrase_prompt_template = ChatPromptTemplate.from_messages(msgs_for_rephrasing)
        response = llm_fast.invoke(rephrase_prompt_template.format_messages())
        state['rephrased_question'] = response.content.strip()
        print(f"Rephrased question (using human-only history): {state['rephrased_question']}")
    else:
        state['rephrased_question'] = current_question_content
        print(f"No prior history, using original question: {state['rephrased_question']}")
    
    return state


class GradeOutput(BaseModel):
    decision: str = Field(description="Must be 'Yes' or 'No', indicating if the question is on topic.")

def question_classifier(state: AgentState):
    print("Entering question_classifier")
    system_msg = SystemMessage(content="""
You are an expert classifier for DataCoGlobal's supply chain chatbot.
Your task is to determine if a user's rephrased question is relevant to supply chain operations *within the context of DataCoGlobal*.

Relevant topics to DataCoGlobal's supply chain operations include, but are not limited to:
-   **Inventory Management:** Questions about inventory levels, stockouts, obsolete inventory, inventory turnover, stock locations, etc. (e.g., "How many units of product X are in stock?", "What is our policy on obsolete items?")
-   **Orders and Sales Data:** Questions about order status, fulfillment, lead times, sales figures, sales amounts, order details, customer orders, purchase orders. (e.g., "What is the total sales amount for all orders?", "Find orders for customer Y.", "What's the status of order 123?")
-   **Products (in a supply chain context):** Questions about product specifications relevant to supply, manufacturing, or logistics, Bill of Materials (BOM). (e.g., "What are the components of product Z?", "Which products use material A?")
-   **Suppliers:** Questions about supplier performance, supplier selection criteria, supplier compliance, and supplier details. (e.g., "List suppliers in region North America.", "What is our supplier ethical sourcing policy?")
-   **Logistics and Warehousing:** Questions about shipping, transportation, warehouse operations, and distribution. (e.g., "What are the shipping costs for order 456?", "Which warehouse holds item B?")
-   **Supply Chain Policies:** Questions asking to explain or apply specific supply chain policies (e.g., "Explain the return policy for damaged goods.", "How does the 'no-movers' policy define an item?")
-   **Data Security policy:**Questions asking to explain or apply security policies.
                               
Irrelevant topics (answer 'No' for these):
-   General knowledge questions (e.g., "What is the weather like today?", "Who won the world cup?").
-   Company HR policies, stock market performance, or overall business strategy unless directly and explicitly tied to a specific supply chain operation or data point mentioned above.
-   Marketing campaign strategies (unless specifically about product demand forecasting impacting supply).
-   Questions clearly outside the scope of internal supply chain data and policies.

You MUST use the 'GradeOutput' tool to provide your answer.
Based on the rephrased user question, if the question is relevant to DataCoGlobal's supply chain operations as described above, set the 'decision' field in the GradeOutput tool to 'Yes'.
If the question is not relevant, set the 'decision' field to 'No'.
""")
    human_msg = HumanMessage(content=f"User question: {state['rephrased_question']}")
    grade_prompt_template = ChatPromptTemplate.from_messages([system_msg, human_msg])
    
    structured_llm = llm_default.with_structured_output(GradeOutput) 
    
    try:
        result = (grade_prompt_template | structured_llm).invoke({})
        state['on_topic'] = result.decision.strip() # Use the 'decision' field from GradeOutput
    except Exception as e:
        print(f"Error in question_classifier during LLM call: {e}")
        state['on_topic'] = "No" 
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Groq API response text for question_classifier error: {e.response.text}")

    print(f"Question classified as on_topic: {state['on_topic']}")
    return state

def on_topic_router(state: AgentState) -> str:
    print("Entering on_topic_router (acting as condition)")
    is_on_topic = state.get("on_topic", "").strip().lower() == "yes"
    if is_on_topic:
        print("Routing via key 'retrieval_intent'")
        return "retrieval_intent"
    else:
        print("Routing via key 'off_topic_response'")
        return "off_topic_response"
    

# ------------- Intent Routing -------------

def determine_and_set_retrieval_intent_node(state: AgentState) -> AgentState:
    print("Entering determine_and_set_retrieval_intent_node")
    
    sys_msg_content = """
You are an intent classifier. Your goal is to classify the user's rephrased question.
You MUST use the 'IntentClassification' tool to provide your answer.
The 'intent' field in your response must be one of: 'fetch_doc', 'fetch_sql', 'hybrid', or 'off_topic_response'.

Consider these rules carefully for choosing the intent:
- 'fetch_doc': The question asks *about* a policy, a definition, a procedure, or qualitative information typically found in documents. It does NOT ask for specific data values that would require calculations or direct database lookups based on that policy.
    
- 'fetch_sql': The question asks for specific data, numbers, counts, lists, or aggregations that would come from a database. It does NOT refer to a policy to define its terms or conditions for the data retrieval.
    
- 'hybrid': The question *first* requires understanding a policy or definition from a document, and *then* uses that understanding to query for specific data in the database. The question will typically refer to a policy term AND ask for data related to it.
    Examples:
        "Which inventory items qualify as no-movers *according to our policy*, AND how many do we currently have?"
        "Based on our *supplier selection criteria policy*, which suppliers failed the audit last quarter AND what was their order volume?"
        "What is the value of obsolete stock *as defined in the handling procedure*, for items in warehouse Y?"
NOTE: IN FUE CASES DON'T ATTEMPT TO GO FOR fetch_sql, eg. okay now can you tell me about slow movers items, HERE YOU DONT KNOW POLICY FOR SLOW MOVER SO HYBRID METHOD CHOOSE.
- 'off_topic_response': The question isn’t about our supply chain policies or related data.

The document repository contains policies on: Inventory Management, Obsolete Inventory Handling, HSE, Supplier Selection, Ethical Sourcing, etc.
The database contains transactional data for supply chain operations (orders, customers, products).

Classify the user's question based on the above guidelines.
User's question: """ 
    sys = SystemMessage(content=sys_msg_content)
    human = HumanMessage(content=f"{state['rephrased_question']}")

    class IntentClassification(BaseModel):
       intent: str = Field(description="The classification intent. Must be one of 'fetch_doc', 'fetch_sql', 'hybrid', or 'off_topic_response'.")

    structured_llm = llm_fast.with_structured_output(IntentClassification)
    intent_prompt_template = ChatPromptTemplate.from_messages([sys, human])
    
    try:
        result = (intent_prompt_template | structured_llm).invoke({}) 
        intent = result.intent.strip()
    except Exception as e:
        print(f"Error in determine_and_set_retrieval_intent_node during LLM call: {e}")
        intent = "off_topic_response"
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Groq API response text for intent_classification error: {e.response.text}")
            
    if retriever is None and intent in ['fetch_doc', 'hybrid']:
        print(f"Retriever not available. Original intent was '{intent}'. Downstream nodes will handle missing documents.")

    state['retrieval_intent_method'] = intent 
    print(f"determine_and_set_retrieval_intent_node: intent set to '{intent}' in state.")
    return state


def route_on_retrieval_intent_condition(state: AgentState) -> str:
    intent = state.get('retrieval_intent_method')
    if not intent:
        print("Error in route_on_retrieval_intent_condition: 'retrieval_intent_method' not found. Defaulting to off_topic_response.")
        return 'off_topic_response'
    print(f"route_on_retrieval_intent_condition: Routing via key '{intent}'")
    return intent

def retrieve_docs(state: AgentState): 
    print("Entered retrieve_docs method.")
    if retriever is None:
        print("retrieve_docs: Retriever is not available. Skipping document retrieval.")
        state["documents"] = []
        state["messages"].append(AIMessage(content="I cannot access policy documents right now to answer this fully."))
        return state
    

    documents = retriever.invoke(state["rephrased_question"])
    print(f"retrieve_docs: Retrieved {len(documents)} documents")
    state["documents"] = documents
    return state

def generate_doc_answer(state: AgentState):
    print("Entered generate_doc_answer method")

    
    history_for_generation = state["messages"] 
    documents_context = state["documents"]
    question_to_answer = state["rephrased_question"] 


    if not documents_context and retriever is None:
        if state.get('retrieval_intent_method') in ['fetch_doc', 'hybrid']:
            state["messages"].append(AIMessage(content="I am currently unable to access detailed policy documents. I will try to answer based on general knowledge and available data."))
            history_for_generation = state["messages"]


    response = rag_chain.invoke(
        {"history": history_for_generation, "context": documents_context, "question": question_to_answer}
    )
    generation = response.content.strip()

    state["messages"].append(AIMessage(content=generation))
    print(f"generate_doc_answer: Generated response: {generation}")
    return state




TABLE_NAMES = ["supply_chain_table"]
MAX_AGENT_ITERATIONS = 7 

try:
    db = SQLDatabase.from_uri(settings.DATABASE_URL)
    

    toolkit = SQLDatabaseToolkit(db=db, llm=groq_llm) 
    
    all_available_sql_tools = toolkit.get_tools()

    schema_tool = next((t for t in all_available_sql_tools if t.name == 'sql_db_schema'), None)
    query_tool = next((t for t in all_available_sql_tools if t.name == 'sql_db_query'), None)
    query_checker_tool = next((t for t in all_available_sql_tools if t.name == 'sql_db_query_checker'), None)

    if not all([schema_tool, query_tool, query_checker_tool]):
        missing = [
            name for name, tool_instance in [
                ('sql_db_schema', schema_tool), ('sql_db_query', query_tool), ('sql_db_query_checker', query_checker_tool)
            ] if not tool_instance
        ]
        raise ValueError(f"Essential SQL tools missing: {missing}. Ensure they are provided by the SQLDatabaseToolkit.")


    sql_tools_for_agent = [schema_tool, query_checker_tool, query_tool]

    schema_text_for_prompt = ""
    if schema_tool:
        try:
            schema_text_for_prompt = schema_tool.invoke(",".join(TABLE_NAMES))
        except Exception as e:
            print(f"Warning: Could not fetch schema for {TABLE_NAMES} for prompt: {e}")
            schema_text_for_prompt = f"Schema for {', '.join(TABLE_NAMES)} unavailable. Use `{schema_tool.name}` tool."
    

    agent_prefix = (
        f"You are a PostgreSQL SQL agent. Your goal is to answer user questions using the table(s): {', '.join(TABLE_NAMES)}.\n"
        f"You MUST use the following tools in this general order for querying:\n"
        f"1. `{schema_tool.name}`: Input a comma-separated string of table names (e.g., '{TABLE_NAMES[0]}'). Use this to understand table columns and structure BEFORE writing a query.\n"
        f"2. `{query_checker_tool.name}`: Input the SQL query string you constructed. Use this to validate your PostgreSQL query for correctness BEFORE executing it.\n"
        f"3. `{query_tool.name}`: Input the validated SQL query string to get results from the database.\n\n"
        "IMPORTANT RULES:\n"
        f"- Focus on the {', '.join(TABLE_NAMES)} table(s).\n"
        "- For queries returning lists of data (not aggregations like COUNT), use `LIMIT` (e.g., `LIMIT 5` or `LIMIT 10`) unless the user asks for all items. If a query returns more than 10-15 rows, consider if a more specific query or an aggregation is needed, or summarize the findings instead of listing all rows in your final answer.\n"
        "- If the user asks for a count (e.g., 'order counts for X'), your final answer should be the count, not just the SQL query or intermediate IDs.\n"
        "- If you encounter an error, analyze it, use the schema tool if needed, correct your query, re-check it, and then try executing again.\n"
        f"- You have a maximum of {MAX_AGENT_ITERATIONS} steps to answer the question.\n"
        f"- Initial schema for {', '.join(TABLE_NAMES)} (always verify with `{schema_tool.name}` before querying):\n{schema_text_for_prompt}\n"
        "When you need to inspect table structure, call the tool sql_db_schema with argument supply_chain_table.\n"
        "When you need to execute a SQL query, call the tool sql_db_query and pass exactly your SQL string.\n"
        "**VERY IMPORTANT**: Unless the user explicitly asks for ALL items or a very large number then compute yourself, if list of outcome is there then YOU MUST ALWAYS add a `LIMIT` clause to your SQL queries to return a small number of results.\n"
        "In database there are 180,000 transactions so write query in efficient way.\n" 
        "Fetch data by yourself using sql_db_query instead of returning all thousands or millions of rows.\n"
        "Focus on answering the user's question accurately using the available tools and table schema.\n"
        "If there any error happans while computing or fetching then debug it.\n"
        "if you ae facing error like searching for any varaible example **JUST FOR Reference** **Region** == Southwest but there is no any region in our database so if you are facing error problem then do unique values but wait if you search unique vlues once if there is no value then give reponse No such value which you are asking, so think logically.\n "
        "If your rows exceeds 20 output then give count of that instead of giving rows in response and restrict yourself to use 'LIMIT' other wise it will through LLM token exhausted error.\n"
        "If told to find count then create sql query and run using tool sql_db_query then after finding count give response.\n"
        "Do NOT call or reference any other tool or table.\n"
        "If facing error then do max try for 2 times then give error in response."
        "Think step-by-step. First, understand the question. Then, use the tools as described to get the data."
    )

    sql_agent = initialize_agent( 
        tools=sql_tools_for_agent, 
        llm=groq_llm,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        agent_kwargs={"prefix": agent_prefix},
        max_iterations=MAX_AGENT_ITERATIONS,
        early_stopping_method="generate",
        handle_parsing_errors=True
    )
    print("SQL Agent initialized successfully with simplified prefix and essential tools.")

except Exception as e:
    print(f"Error initializing SQL Agent: {e.__class__.__name__}: {e}. SQL functionalities will be unavailable.")
    db = None
    sql_agent = None

def standalone_sql_agent_node(state: AgentState):
    result = sql_agent.run(state['rephrased_question'])
    response = rag_chain.invoke({
        'history': state['messages'],
        'context': result,
        'question': state['rephrased_question']
    })
    state['messages'].append(AIMessage(content=response.content.strip()))
    return state


def hybrid_sql_agent_node(state: AgentState):
    result = sql_agent.run(state['hybrid_sql_question'])
    response = rag_chain.invoke({
        'history': state['messages'],
        'context': result,
        'question': state['rephrased_question']
    })
    state['messages'].append(AIMessage(content=response.content.strip()))
    return state






# ------------- Off-topic -------------
def off_topic_response_node(state: AgentState): 
    print("Entering off_topic_response_node")

    state["messages"].append(AIMessage(content="I'm sorry, I can only answer questions related to DataCoGlobal's supply chain operations. How can I help you with that?"))
    return state

# ------------- Hybrid Steps -------------
def hybrid_step_1_analyze_docs_node(state: AgentState):
    print("Entering hybrid_step_1_analyze_docs_node.")
    state = retrieve_docs(state) 
    state = generate_doc_answer(state) 
    return state

def hybrid_step_2_fetch_sql_node(state: AgentState): 
    print("Entering hybrid_step_2_fetch_sql_node.")

    doc_analysis_response = ""
    if state['messages'] and isinstance(state['messages'][-1], AIMessage):
        doc_analysis_response = state['messages'][-1].content
    
    enriched_hybrid_question = f"Based on the user question: '{state['rephrased_question']}', and the following information found from documents: '{doc_analysis_response}', now answer the data-specific part of the user's question."
    state['hybrid_sql_question'] = enriched_hybrid_question
    state = hybrid_sql_agent_node(state) 
    return state

# ------------- LangGraph Wiring -------------
workflow = StateGraph(AgentState) 

# Add nodes
workflow.add_node('question_rewriter_node', question_rewriter) 
workflow.add_node('question_classifier_node', question_classifier)
workflow.add_node('determine_intent_node', determine_and_set_retrieval_intent_node)
workflow.add_node('retrieve_documents_node', retrieve_docs)
workflow.add_node('generate_doc_answer_node', generate_doc_answer)
workflow.add_node('standalone_sql_node', standalone_sql_agent_node)
workflow.add_node('off_topic_node', off_topic_response_node)
workflow.add_node('hybrid_analyze_docs_node', hybrid_step_1_analyze_docs_node)
workflow.add_node('hybrid_fetch_sql_node', hybrid_step_2_fetch_sql_node)


# Entry point
workflow.set_entry_point('question_rewriter_node')

# Edges
workflow.add_edge('question_rewriter_node', 'question_classifier_node')

# Conditional Edges after question_classifier
workflow.add_conditional_edges(
    'question_classifier_node',  
    on_topic_router,        
    {
        'retrieval_intent': 'determine_intent_node',
        'off_topic_response': 'off_topic_node'
    }
)

workflow.add_conditional_edges(
    'determine_intent_node', 
    route_on_retrieval_intent_condition,    
    {
        'fetch_doc': 'retrieve_documents_node',
        'fetch_sql': 'standalone_sql_node',
        'hybrid': 'hybrid_analyze_docs_node',
        'off_topic_response': 'off_topic_node' 
    }
)

# Paths for final actions
workflow.add_edge('retrieve_documents_node', 'generate_doc_answer_node')
workflow.add_edge('generate_doc_answer_node', END)
workflow.add_edge('standalone_sql_node', END)
workflow.add_edge('off_topic_node', END)
workflow.add_edge('hybrid_analyze_docs_node', 'hybrid_fetch_sql_node')
workflow.add_edge('hybrid_fetch_sql_node', END)



runnable = workflow.compile()

print("RAG Chatbot Runnable compiled successfully.")
