# Student Career Guidance Agent

An intelligent, conversational AI agent built with the `google-genai` SDK and powered by Gemini. This agent acts as an empathetic career guidance counselor, helping students figure out their career paths, suggesting educational programs, and providing practical advice on skill development.

## Features

- **Interactive Conversational AI**: Employs Gemini 2.5 Flash to provide expert, empathetic career advice.
- **Native Career Tools**: Comes with built-in Python tools that the AI can call automatically to fetch structured advice:
  - **Roadmap Generator**: Generates step-by-step learning roadmaps for specific career goals.
  - **Course Finder**: Recommends courses based on learning topics.
  - **Project Recommender**: Suggests projects to build based on current skills and difficulty level.
- **Multi-MCP Server Architecture**: Features a robust, concurrent architecture capable of connecting to multiple **Model Context Protocol (MCP)** servers simultaneously. This allows the agent to securely integrate with external applications (like Google Calendar, Google Drive, LinkedIn) and use their tools.

## Prerequisites

- Python 3.10+
- A valid [Gemini API Key](https://aistudio.google.com/app/apikey)
- Node.js / `npx` (Required if you are connecting to `npm`-based MCP servers like Google Calendar or Google Drive)

## Installation

1. **Clone or Download the Repository**
2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment Variables:**
   - Open the `.env` file in the root directory.
   - Replace `your_actual_key_here` with your real Gemini API key.
   - (Optional) Configure any MCP servers you wish to connect to. See the **MCP Integration** section below.

## Usage

Run the agent script from your terminal:

```bash
python agent.py
```

The agent will initialize its native tools, attempt to connect to any configured MCP servers, and start an interactive chat loop. Just type your questions and hit Enter!

Example interactions:
- *"I'm a beginner at Python, what projects should I build?"* (Triggers Project Recommender)
- *"Generate a learning roadmap for becoming a Data Scientist."* (Triggers Roadmap Generator)

Type `exit` or `quit` to end the session.

## MCP Integration

This agent supports connecting to external Model Context Protocol (MCP) servers to extend its capabilities.

You can configure multiple servers in your `.env` file using the `MCP_X_COMMAND` and `MCP_X_ARGS` format, where `X` is a unique identifier (e.g., 1, 2, 3). 

### Example: Google Calendar & Google Drive

```env
# Google Calendar MCP
MCP_1_COMMAND=npx
MCP_1_ARGS=-y,@modelcontextprotocol/server-google-calendar

# Google Drive MCP
MCP_2_COMMAND=npx
MCP_2_ARGS=-y,@modelcontextprotocol/server-google-drive
```

*Note: Connecting to specific services like Google Calendar or Drive will require you to set up the appropriate OAuth credentials for those services and provide them as environment variables according to their specific package documentation.*
