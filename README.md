# Web Agent AI

This project implements an AI agent that can interact with web pages using Playwright and OpenAI.

## Setup

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:

```bash
playwright install
```

3. Create a `.env` file in the project root and add your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Make sure your local web application is running on `http://localhost:3000/`

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

5. Type 'quit' to exit the agent

## Features

- Automated web page interaction
- AI-powered page analysis
- Interactive command interface
- Support for clicking and typing actions
- Error handling and resource cleanup
