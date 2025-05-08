import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from groq import Groq
import time
import json
import logging
from datetime import datetime
from pathlib import Path
import re
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from enum import Enum

class ActionType(Enum):
    """Enum for different types of actions"""
    CLICK = "click"
    TYPE = "type"
    UNKNOWN = "unknown"

@dataclass
class Action:
    """Data class to represent a web action"""
    type: ActionType
    selector: str
    value: Optional[str] = None

class WebAgent:
    """A web automation agent that can interact with web pages and record/execute flows."""
    
    def __init__(self):
        """Initialize the WebAgent with necessary configurations."""
        self._setup_environment()
        self._initialize_components()
        self._load_registries()

    def _setup_environment(self) -> None:
        """Setup environment variables and logging."""
        load_dotenv()
        self._setup_logging()
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))

    def _setup_logging(self) -> None:
        """Configure logging settings."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "agent.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _initialize_components(self) -> None:
        """Initialize browser components and registries."""
        self.playwright = sync_playwright().start()
        self.browser = None
        self.context = None
        self.page = None
        self.action_registry = {}
        self.flow_registry = {}
        self.current_flow = None
        self.current_flow_actions = []

    def _load_registries(self) -> None:
        """Load action and flow registries from files."""
        self.load_action_registry()
        self.load_flow_registry()

    def load_action_registry(self) -> None:
        """Load action registry from file with error handling."""
        registry_path = Path("logs/action_registry.json")
        try:
            if registry_path.exists() and registry_path.stat().st_size > 0:
                with open(registry_path, 'r') as f:
                    self.action_registry = json.load(f)
            else:
                self._initialize_empty_registry(registry_path)
        except Exception as e:
            self.logger.error(f"Error loading action registry: {e}")
            self.action_registry = {}

    def load_flow_registry(self) -> None:
        """Load flow registry from file with error handling."""
        registry_path = Path("logs/flow_registry.json")
        try:
            if registry_path.exists() and registry_path.stat().st_size > 0:
                with open(registry_path, 'r') as f:
                    self.flow_registry = json.load(f)
            else:
                self._initialize_empty_registry(registry_path)
        except Exception as e:
            self.logger.error(f"Error loading flow registry: {e}")
            self.flow_registry = {}

    def _initialize_empty_registry(self, registry_path: Path) -> None:
        """Initialize an empty registry file."""
        registry_path.parent.mkdir(exist_ok=True)
        with open(registry_path, 'w') as f:
            json.dump({}, f, indent=2)

    def save_action_registry(self) -> None:
        """Save action registry to file with error handling."""
        self._save_registry("logs/action_registry.json", self.action_registry)

    def save_flow_registry(self) -> None:
        """Save flow registry to file with error handling."""
        self._save_registry("logs/flow_registry.json", self.flow_registry)

    def _save_registry(self, path: str, data: Dict) -> None:
        """Generic method to save registry data."""
        try:
            registry_path = Path(path)
            registry_path.parent.mkdir(exist_ok=True)
            with open(registry_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving registry to {path}: {e}")

    def discover_page_actions(self) -> List[Dict]:
        """Discover all possible actions on the current page."""
        try:
            elements = self._get_interactive_elements()
            return self._analyze_elements(elements)
        except Exception as e:
            self.logger.error(f"Error discovering page actions: {e}")
            return []

    def _get_interactive_elements(self) -> List[Dict]:
        """Get all interactive elements from the current page."""
        return self.page.evaluate("""() => {
            const elements = [];
            document.querySelectorAll('button, input, [role="button"], a, [onclick]').forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    elements.push({
                        tag: el.tagName.toLowerCase(),
                        type: el.type || '',
                        id: el.id || '',
                        class: el.className || '',
                        text: el.textContent?.trim() || '',
                        placeholder: el.placeholder || '',
                        role: el.getAttribute('role') || '',
                        isVisible: true
                    });
                }
            });
            return elements;
        }""")

    def _analyze_elements(self, elements: List[Dict]) -> List[Dict]:
        """Analyze elements using Groq to determine possible actions."""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a web page analyzer. For each interactive element, identify what actions can be performed.
Return a JSON array of objects with these fields:
- action: The type of action (click, type, select)
- description: A human-readable description of what the element does
- selector: The CSS selector to use (#id, .class, etc.)
- requirements: Any constraints or requirements for using this element"""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze these interactive elements: {json.dumps(elements, indent=2)}"
                    }
                ],
                temperature=0.3,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            
            actions = json.loads(response.choices[0].message.content)
            if isinstance(actions, dict) and 'actions' in actions:
                actions = actions['actions']
            
            self._update_action_registry(actions)
            return actions
        except Exception as e:
            self.logger.error(f"Error analyzing elements: {e}")
            return []

    def _update_action_registry(self, actions: List[Dict]) -> None:
        """Update the action registry with new actions."""
        self.action_registry[self.page.url] = {
            'timestamp': datetime.now().isoformat(),
            'actions': actions
        }
        self.save_action_registry()

    def interpret_command(self, command: str, available_actions: List[Dict]) -> List[str]:
        """Interpret natural language command into specific actions."""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are a web automation expert. Convert natural language commands into specific actions.
Available actions: {json.dumps(available_actions, indent=2)}

IMPORTANT: Return ONLY the actions in this exact format, one per line:
click .income-btn
type #description with Salary
type #amount with 100
click .submit-btn

DO NOT include any explanations or additional text. Only return the actions."""
                    },
                    {
                        "role": "user",
                        "content": f"Convert this command into actions: {command}"
                    }
                ],
                temperature=0.3,
                max_tokens=256
            )
            
            # Get the response and clean it
            actions_text = response.choices[0].message.content.strip()
            
            # Split into lines and clean each action
            actions = []
            for line in actions_text.split('\n'):
                line = line.strip()
                if line and not line.startswith(('To', 'The', 'We', 'This', 'Here')):
                    # Remove any numbering or bullet points
                    line = re.sub(r'^\d+\.\s*|^-\s*', '', line)
                    if line.startswith(('click', 'type')):
                        actions.append(line)
            
            if not actions:
                self.logger.error(f"Could not interpret command: {command}")
                return []
                
            return actions
        except Exception as e:
            self.logger.error(f"Error interpreting command: {e}")
            return []

    def execute_action(self, action: str) -> None:
        """Execute a single action with proper error handling."""
        try:
            # Clean the action string
            action = action.strip()
            
            # Validate action format
            if not action.startswith(('click', 'type')):
                raise ValueError(f"Invalid action format: {action}")
            
            if action.startswith("type"):
                # Handle type action: "type #selector with value"
                parts = action.split(" with ")
                if len(parts) != 2:
                    raise ValueError(f"Invalid type action format: {action}")
                selector = parts[0].replace("type ", "").strip()
                value = parts[1].strip()
                self.page.fill(selector, value)
                print(f"Typed '{value}' into {selector}")
            elif action.startswith("click"):
                # Handle click action: "click selector"
                selector = action.replace("click ", "").strip()
                self.page.click(selector)
                print(f"Clicked {selector}")
            
            # Add a small delay after each action
            time.sleep(0.5)
            
        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
            raise

    def run(self, url: str) -> None:
        """Main run loop for the agent."""
        try:
            self._initialize_browser()
            self._navigate_to_url(url)
            self._show_welcome_message()
            self._main_loop()
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
        finally:
            self.cleanup()

    def _initialize_browser(self) -> None:
        """Initialize the browser and context."""
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def _navigate_to_url(self, url: str) -> None:
        """Navigate to the specified URL."""
        self.page.goto(url)
        self.discover_page_actions()

    def _show_welcome_message(self) -> None:
        """Display the welcome message and available commands."""
        print("\nWelcome to Web Assistant!")
        print("Available commands:")
        print("- 'flow > flow_name' or 'flows > flow_name' to start recording a flow")
        print("- 'end_flow' to stop recording")
        print("- 'run_flow flow_name' to execute a saved flow")
        print("- 'quit' to exit")
        print("- Any other input will be treated as a natural language command\n")

    def _main_loop(self) -> None:
        """Main command processing loop."""
        available_actions = self.discover_page_actions()
        
        while True:
            user_input = input("\nEnter command: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.startswith(('flow >', 'flows >')):
                self._handle_flow_start(user_input)
            elif user_input.lower() == 'end_flow':
                self._handle_flow_end()
            elif user_input.startswith('run_flow'):
                self._handle_flow_execution(user_input)
            else:
                self._handle_natural_language_command(user_input, available_actions)
                available_actions = self.discover_page_actions()

    def _handle_flow_start(self, user_input: str) -> None:
        """Handle starting a new flow recording."""
        flow_name = user_input.split('>', 1)[1].strip()
        if not flow_name:
            print("Please provide a flow name after 'flow >' or 'flows >'")
            return
        self.start_flow(flow_name)
        print(f"Started recording flow: {flow_name}")

    def _handle_flow_end(self) -> None:
        """Handle ending the current flow recording."""
        if not self.current_flow:
            print("No flow is currently being recorded")
            return
        self.end_flow()
        print("Flow recording ended and saved")

    def _handle_flow_execution(self, user_input: str) -> None:
        """Handle executing a saved flow."""
        flow_name = user_input.replace('run_flow', '').strip()
        if not flow_name:
            print("Please provide a flow name after 'run_flow'")
            return
        if flow_name not in self.flow_registry:
            print(f"Flow '{flow_name}' not found. Available flows: {', '.join(self.flow_registry.keys())}")
            return
        print(f"Executing flow: {flow_name}")
        self.execute_flow(flow_name)

    def execute_flow(self, flow_name: str) -> bool:
        """Execute a saved flow.
        
        Args:
            flow_name: Name of the flow to execute
            
        Returns:
            bool: True if flow executed successfully, False otherwise
        """
        if flow_name not in self.flow_registry:
            self.logger.error(f"Flow {flow_name} not found")
            return False

        flow = self.flow_registry[flow_name]
        self.logger.info(f"Executing flow: {flow_name}")
        
        # Navigate to the flow's starting URL if different from current
        if self.page.url != flow["url"]:
            self.page.goto(flow["url"])
            available_actions = self.discover_page_actions()
        else:
            available_actions = self.discover_page_actions()

        # Execute each command in the flow
        for command in flow["actions"]:
            print(f"\nProcessing command: {command}")
            
            # Interpret the command into specific actions
            actions = self.interpret_command(command, available_actions)
            if not actions:
                print(f"Could not interpret command: {command}")
                continue
            
            # Execute each interpreted action
            for action in actions:
                try:
                    self.execute_action(action)
                    print(f"Executed: {action}")
                except Exception as e:
                    self.logger.error(f"Error executing action in flow {flow_name}: {e}")
                    print(f"Error executing action: {action}")
                    return False
            
            # Refresh available actions after each command
            available_actions = self.discover_page_actions()

        return True

    def start_flow(self, flow_name: str) -> None:
        """Start recording a new flow.
        
        Args:
            flow_name: Name of the flow to start recording
        """
        self.current_flow = flow_name
        self.current_flow_actions = []
        self.logger.info(f"Started recording flow: {flow_name}")

    def end_flow(self) -> None:
        """End recording the current flow and save it."""
        if self.current_flow:
            self.flow_registry[self.current_flow] = {
                "actions": self.current_flow_actions,
                "url": self.page.url,
                "timestamp": datetime.now().isoformat()
            }
            self.save_flow_registry()
            self.logger.info(f"Saved flow: {self.current_flow} with {len(self.current_flow_actions)} actions")
            self.current_flow = None
            self.current_flow_actions = []

    def _handle_natural_language_command(self, command: str, available_actions: List[Dict]) -> None:
        """Handle a natural language command."""
        actions = self.interpret_command(command, available_actions)
        if not actions:
            print("I couldn't understand that command. Please try again.")
            return
        
        if self.current_flow:
            self.current_flow_actions.append(command)
            print(f"Added command to flow {self.current_flow}: {command}")
        
        print("\nProcessing your request...")
        for action in actions:
            try:
                self.execute_action(action)
                print(f"Executed: {action}")
            except Exception as e:
                print(f"Error executing action {action}: {e}")

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self.logger.info("Agent session ended")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    agent = WebAgent()
    agent.run("http://localhost:3000/") 