from typing import TypedDict, Annotated, Optional, Literal
from langgraph.graph import add_messages, StateGraph, START, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessageChunk, HumanMessage, ToolMessage
from langchain_core.messages import BaseMessage
from langgraph.prebuilt import ToolNode, tools_condition
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import json


load_dotenv()

model = ChatOpenAI(model="gpt-4o-mini")
search_tool = TavilySearch(max_results=4)
tools = [search_tool]
memory = MemorySaver()
llm_with_tools = model.bind_tools(tools=tools)

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

async def model_node(state: State, config):
    result = await llm_with_tools.ainvoke(state["messages"], config)
    return {
        "messages": [result], 
    }

def tools_router(state: State) -> Literal["tool_node", END]:       # can use tool_condition instead
    last_message = state["messages"][-1]

    if(hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0):
        return "tool_node"
    else: 
        return END


graph_builder = StateGraph(State)

tool_node = ToolNode(tools)

graph_builder.add_node("model", model_node)
graph_builder.add_node("tool_node", tool_node)

graph_builder.add_edge(START, "model")

graph_builder.add_conditional_edges("model", tools_router)
graph_builder.add_edge("tool_node", "model")

graph = graph_builder.compile(checkpointer=memory)


###  APP  ###

app = FastAPI()

# Add CORS middleware with settings that match frontend requirements
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # accepts requests from any origin (for now)
    allow_credentials=True,     # allows cookies/auth headers to be sent cross-origin
    allow_methods=["*"],        # permits any HTTP method
    allow_headers=["*"],        # permits any HTTP header
    expose_headers=["Content-Type"],
)

# Serialize Streamed Chunks - Guard Function. When the LLM streams tokens, LangChain emits them as AIMessageChunk objects, not plain strings. This function extracts the actual textfrom a chunk, and raises loudly if something unexpected shows up instead.
def serialise_ai_message_chunk(chunk): 
    if(isinstance(chunk, AIMessageChunk)):
        return chunk.content
    else:
        raise TypeError(
            f"Object of type {type(chunk).__name__} is not correctly formatted for serialisation"
        )

# Async Generator Function. It yields a chunks of text over time. Normally a function returns once, but calling this generator doesn't execute everything. Each time you ask for the next value, you get each value. The function pauses after every yield.
async def generate_chat_responses(message: str, checkpoint_id: Optional[str] = None):
    is_new_conversation = checkpoint_id is None
    
    if is_new_conversation:
        # Generate new checkpoint ID for first message in conversation
        new_checkpoint_id = str(uuid4())

        config = {
            "configurable": {
                "thread_id": new_checkpoint_id
            }
        }
        
        # Initialize with first message. This doesn't run the graph yet. just return a generator only executes when we iterate it
        events = graph.astream_events(
            {"messages": [HumanMessage(content=message)]},
            version="v2",
            config=config
        )
        
        # First send the checkpoint ID. First SSE (Server-Sent-Event). Format: start with data: and end with a blank line (\n\n). This tells the client, this event is complete
        checkpoint_payload = json.dumps({"type": "checkpoint", "checkpoint_id": new_checkpoint_id})
        yield f"data: {checkpoint_payload}\n\n"
    else:
        config = {
            "configurable": {
                "thread_id": checkpoint_id
            }
        }
        # Continue existing conversation
        events = graph.astream_events(
            {"messages": [HumanMessage(content=message)]},
            version="v2",
            config=config
        )

    async for event in events:
        event_type = event["event"]
        
        if event_type == "on_chat_model_stream":
            chunk_content = serialise_ai_message_chunk(event["data"]["chunk"])
            # Skip empty chunks — these occur while a tool call's arguments are being streamed (content is '' during that phase), so this avoids sending a burst of empty "content" events to the client.
            if not chunk_content:
                continue
            # Escape single quotes and newlines for safe JSON parsing
            payload = json.dumps({"type": "content", "content": chunk_content})
            
            yield f"data: {payload}\n\n"   # token-by-token streaming
            
        elif event_type == "on_chat_model_end":
            # Check if there are tool calls for search, if so get the details, or []
            tool_calls = event["data"]["output"].tool_calls if hasattr(event["data"]["output"], "tool_calls") else []
            search_calls = [call for call in tool_calls if call["name"] == search_tool.name]
            
            if search_calls:
                # Signal that a search is starting. Extracts the query text the model want search for
                search_query = search_calls[0]["args"].get("query", "")  
                # Escape quotes and special characters. Again may need improvement
                payload = json.dumps({"type": "search_start", "query": search_query})
                yield f"data: {payload}\n\n"
        
        # Once the actual tool execution finishes (Tavily returns real results), grab its output        
        elif event_type == "on_tool_end" and event["name"] == search_tool.name:
            # Search completed - send results or error
            output = event["data"]["output"]    # Output is a ToolMessage. And inside its content is JSON strings
            
            raw_content = getattr(output, "content", output)    # get output.content if that attribute exists; otherwise, fall back to output itself unchanged
            
            try:
                parsed = json.loads(raw_content) if isinstance(raw_content, str) else raw_content   # loads turns JSON string into dict
            except json.JSONDecodeError:
                parsed = {}     # catches the case where raw_content looks like a string but isn't valid JSON, just return {}
                
            results = parsed.get("results", []) if isinstance(parsed, dict) else []
            urls = [item["url"] for item in results if isinstance(item, dict) and "url" in item]
            
            payload = json.dumps({"type": "search_results", "urls": urls})
            yield f"data: {payload}\n\n"
    
    # Send an end event (for frontend)
    yield f"data: {{\"type\": \"end\"}}\n\n"

@app.get("/chat_stream/{message}")
async def chat_stream(message: str, checkpoint_id: Optional[str] = Query(None)):
    return StreamingResponse(
        generate_chat_responses(message, checkpoint_id), 
        media_type="text/event-stream"
    )
# StreamingResponse wraps our async generator and streams its yielded chunks to the client as they're produced, rather than buffering the whole response
# media_type="text/event-stream" is the standard MIME type telling the browser (or an EventSource client) to treat this as SSE


#using GET with the message embedded in the URL path (/chat_stream/{message}) means long messages, special characters, or messages containing / could cause URL-encoding issues or hit URL length limits. A POST endpoint with the message in the request body is generally more robust for chat input — though SSE via EventSource in browsers only supports GET natively