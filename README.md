# Web Agent AI

## Project Description
Web Agent AI is an agentic AI system that automates web page interaction using Playwright and advanced language models (Groq/OpenAI). It enables users to control browsers, analyze web pages, and perform complex workflows via natural language commands. The agent can record, save, and replay action flows, making it ideal for web automation, testing, and intelligent browsing tasks.

---

**Tags:**
AI agent, browser automation, Playwright, OpenAI, Groq, Python, web automation, agentic AI, natural language, RPA, LLM

---

## Tech Stack
- **Python 3.x**
- **Playwright** (browser automation)
- **Groq** (AI/NLP processing)
- **OpenAI API** (for LLMs)
- **python-dotenv** (environment management)
- **httpx** (HTTP requests)
- **Logging** (Python standard library)

---

## Features
- Automated web page interaction (click, type, navigate)
- AI-powered page analysis and action suggestion
- Natural language command interpretation
- Interactive command-line interface
- Action and flow registry (record, save, and replay action sequences)
- Error handling and resource cleanup
- Logging of all actions and errors
- Persistent state and session management
- Flow execution for multi-step automation
- Support for custom flows and reusable automation scripts
- Modular, extensible architecture

---

## Implementation Notes
- **Architecture:** Modular, with clear separation between web interaction, AI processing, state management, and logging.
- **Web Automation:** Uses Playwright for robust, cross-browser automation.
- **AI Integration:** Employs Groq/OpenAI for element analysis and natural language command interpretation.
- **Registries:** Action and flow registries are stored as JSON for persistence and replayability.
- **Logging:** Logs to both file and console for debugging and monitoring.
- **Error Handling:** Handles browser, network, and AI-related errors gracefully.
- **Environment:** Uses `.env` for API keys and configuration.

---

## Deployment Notes
- Requires Python 3.x and Playwright browsers installed.
- Needs valid OpenAI and Groq API keys in `.env`:
  ```
  OPENAI_API_KEY=your_openai_key
  GROQ_API_KEY=your_groq_key
  ```
- Run locally for development; for production, consider Dockerizing and setting up monitoring/alerting.
- Logs and registries are stored in the `logs/` directory.
- For scaling: use stateless agent instances with shared registry storage.

---

## Setup

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:

```bash
playwright install
```

3. Create a `.env` file in the project root and add your API keys:

```
OPENAI_API_KEY=your_api_key_here
GROQ_API_KEY=your_groq_key_here
```

---

## Usage

1. Make sure your local web application is running on `http://localhost:3000/` (or update the URL as needed).

2. Run the agent:

```bash
python agent.py
```

3. The agent will:
   - Open a browser window
   - Navigate to the specified URL
   - Analyze the page content
   - Allow you to input actions to perform on the page

4. Available actions:
   - Click elements: `click #button-id` or `click .class-name`
   - Type text: `type #input-id with your text`
   - Start/stop flows: `start flow flow_name`, `end flow`, `run flow flow_name`
   - Use natural language: e.g., `add item to cart`, `login with credentials`

5. Type 'quit' to exit the agent

---

## Example Flows
- Record a sequence of actions as a flow and replay them for automation or testing.
- Automate login, form filling, or shopping cart operations using natural language or direct commands.

---

## Troubleshooting & Logs
- All actions and errors are logged to `logs/agent.log`.
- Check logs for error details and debugging information.
- Ensure Playwright browsers are installed and API keys are valid.

---

## License
MIT
