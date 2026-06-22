import asyncio
import os
import sys
from contextlib import AsyncExitStack
from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables
load_dotenv()

# --- Native Tools Implementation ---
def generate_roadmap(career_goal: str, current_skill_level: str) -> str:
    """Generates a learning roadmap for a given career goal."""
    return f"Roadmap for {career_goal} (Level: {current_skill_level}):\n1. Learn Basics: Fundamentals of the field.\n2. Build Projects: Create portfolio items.\n3. Apply for jobs: Networking and applying."

def find_courses(topic: str) -> str:
    """Finds recommended courses for a specific topic."""
    return f"Recommended courses for {topic}:\n1. Coursera: {topic} Specialization\n2. Udemy: Complete {topic} Bootcamp"

def recommend_projects(skill: str, difficulty: str) -> str:
    """Recommends projects to build based on a skill and difficulty level."""
    return f"Project ideas for {skill} ({difficulty}):\n1. Build a basic {skill} app.\n2. Contribute to an open source {skill} repository."

NATIVE_TOOLS_MAP = {
    "generate_roadmap": generate_roadmap,
    "find_courses": find_courses,
    "recommend_projects": recommend_projects
}

def get_native_tool_declarations():
    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="generate_roadmap",
                    description="Generates a learning roadmap for a given career goal. Parameters: career_goal (string), current_skill_level (string).",
                ),
                types.FunctionDeclaration(
                    name="find_courses",
                    description="Finds recommended courses for a specific topic. Parameter: topic (string)."
                ),
                types.FunctionDeclaration(
                    name="recommend_projects",
                    description="Recommends projects to build based on a skill and difficulty level. Parameters: skill (string), difficulty (string)."
                )
            ]
        )
    ]

async def interactive_chat(client: genai.Client, mcp_sessions: dict[str, ClientSession]):
    system_instruction = """
    You are an expert student career guidance counselor. Your role is to help students 
    figure out their career paths, suggest suitable educational programs, provide advice on 
    skill development, and answer any questions they have about their future careers.
    Be empathetic, encouraging, and provide practical, actionable advice.
    """

    tools = get_native_tool_declarations()
    
    # Map to keep track of which tool belongs to which MCP session
    mcp_tool_to_session_map = {}

    for name, session in mcp_sessions.items():
        try:
            mcp_tools = await session.list_tools()
            for tool in mcp_tools.tools:
                tools.append(
                    types.Tool(
                        function_declarations=[
                            types.FunctionDeclaration(
                                name=tool.name,
                                description=tool.description,
                            )
                        ]
                    )
                )
                mcp_tool_to_session_map[tool.name] = session
                print(f"Loaded MCP Tool from {name}: {tool.name}")
        except Exception as e:
            print(f"Warning: Failed to load tools from MCP server {name}: {e}")

    config_args = {
        "system_instruction": system_instruction,
        "temperature": 0.7,
    }
    if tools:
        config_args["tools"] = tools

    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(**config_args)
    )

    print("\nStudent Career Guidance Agent Initialized.")
    print("Native Tools Loaded: Roadmap Generator, Course Finder, Project Recommender.")
    if mcp_sessions:
        print(f"Connected to {len(mcp_sessions)} MCP Server(s).")
    else:
        print("Running without any MCP servers.")
    print("Type 'exit' or 'quit' to end the session.\n")

    while True:
        try:
            user_input = await asyncio.to_thread(input, "You: ")
            if user_input.lower() in ['exit', 'quit']:
                print("Agent: Best of luck with your career journey! Goodbye.")
                break
            
            if not user_input.strip():
                continue

            response = chat.send_message(user_input)
            
            while response.function_calls:
                for function_call in response.function_calls:
                    print(f"  [Agent is using tool: {function_call.name}]")
                    
                    args = function_call.args if hasattr(function_call, 'args') and function_call.args else {}
                    if not isinstance(args, dict):
                        args = dict(args)

                    # Dispatcher
                    if function_call.name in NATIVE_TOOLS_MAP:
                        # Native Tool
                        try:
                            func = NATIVE_TOOLS_MAP[function_call.name]
                            result = func(**args)
                            response = chat.send_message(
                                types.Part.from_function_response(
                                    name=function_call.name,
                                    response={"result": result}
                                )
                            )
                        except Exception as e:
                            print(f"  [Error running native tool {function_call.name}: {e}]")
                            response = chat.send_message(
                                types.Part.from_function_response(
                                    name=function_call.name,
                                    response={"error": str(e)}
                                )
                            )
                    elif function_call.name in mcp_tool_to_session_map:
                        # MCP Tool
                        mcp_session = mcp_tool_to_session_map[function_call.name]
                        try:
                            mcp_result = await mcp_session.call_tool(
                                function_call.name, 
                                arguments=args
                            )
                            tool_response_text = "\n".join(
                                [c.text for c in mcp_result.content if getattr(c, 'type', '') == "text"]
                            )
                            if not tool_response_text:
                                tool_response_text = str(mcp_result)
                            
                            response = chat.send_message(
                                types.Part.from_function_response(
                                    name=function_call.name,
                                    response={"result": tool_response_text}
                                )
                            )
                        except Exception as e:
                            print(f"  [Error running MCP tool {function_call.name}: {e}]")
                            response = chat.send_message(
                                types.Part.from_function_response(
                                    name=function_call.name,
                                    response={"error": str(e)}
                                )
                            )
                    else:
                        print(f"  [Error: Tool {function_call.name} not found]")
                        response = chat.send_message(
                            types.Part.from_function_response(
                                name=function_call.name,
                                response={"error": "Tool not found"}
                            )
                        )

            print(f"Agent: {response.text}\n")
            
        except KeyboardInterrupt:
            print("\nAgent: Goodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")

async def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("Please set your GEMINI_API_KEY in the .env file.")
        return

    client = genai.Client()

    # Find all MCP configurations in .env
    mcp_configs = {}
    for key, value in os.environ.items():
        if key.startswith("MCP_") and key.endswith("_COMMAND"):
            prefix = key[:-8] # Remove '_COMMAND'
            args_key = f"{prefix}_ARGS"
            args_str = os.getenv(args_key, "")
            mcp_configs[prefix] = {
                "command": value,
                "args": args_str.split(",") if args_str else []
            }

    async with AsyncExitStack() as stack:
        mcp_sessions = {}
        for name, config in mcp_configs.items():
            if not config["command"]:
                continue
            
            server_parameters = StdioServerParameters(
                command=config["command"],
                args=config["args"],
                env=None
            )
            print(f"Starting MCP server ({name}): {config['command']} {' '.join(config['args'])}")
            
            try:
                # Enter context for stdio_client
                read, write = await stack.enter_async_context(stdio_client(server_parameters))
                # Enter context for ClientSession
                session = await stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                mcp_sessions[name] = session
            except Exception as e:
                print(f"Failed to connect to MCP server {name} ({e}). It will be skipped.")

        await interactive_chat(client, mcp_sessions)

if __name__ == "__main__":
    asyncio.run(main())
