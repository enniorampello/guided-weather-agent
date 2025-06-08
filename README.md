# Weather Agent

An AI-powered weather agent that provides real-time weather information through an intuitive command-line interface. The agent can search for weather information, manage favorite cities, and provide conversational weather updates using an LLM.

## 🏗️ Architecture & Approach

### Core Components

1. **Weather Agent (`WeatherAgent`)**: Handles web scraping and interaction with Weather.com
   - Automated login and session management
   - Weather data extraction and parsing
   - Favorites management

2. **LLM Integration (`utils.py`)**: Flexible AI provider support
   - Automatic detection of available AI providers
   - Unified interface for OpenAI and Azure OpenAI
   - Fallback mechanism and error handling

3. **LangGraph Framework**: Orchestrates the conversational AI flow
   - Tool-calling capabilities for weather functions
   - State management for multi-turn conversations
   - Conditional routing based on user intents

### Technical Decisions

#### Web Scraping Strategy

- **Selenium WebDriver**: Chosen for reliable interaction with dynamic JavaScript content
- **Chrome Options**: Configured to disable notifications and geolocation prompts
- **Cookie Handling**: Automated acceptance of privacy management dialogs
- **Wait Strategies**: Explicit waits for reliable element interaction

#### Data Processing

- **Markdown Conversion**: Weather data converted to markdown for better AI processing
- **LLM of Choice**: Using gpt-4o for simplicity and cost-effectiveness
- **

## 📋 Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Chrome browser (for Selenium WebDriver)
- OpenAI API key OR Azure OpenAI credentials
- Weather.com account credentials

## 🚀 Installation

1. **Install uv** (if you haven't already):

   ```bash
   brew install uv
   ```

2. **Clone the repository**:

   ```bash
   git clone https://github.com/enniorampello/weather-agent.git
   cd weather-agent
   ```

3. **Install dependencies**:

   ```bash
   uv sync
   ```

4. **Install Chrome WebDriver** (if not already available):

   ```bash
   # macOS with Homebrew
   brew install chromedriver
   
   # Or download from https://chromedriver.chromium.org/
   ```

## ⚙️ Configuration

Create a `.env` file in the project root with your credentials:

### Option 1: Using OpenAI

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o  # Optional, defaults to gpt-4o

# Weather.com Credentials
WEATHER_EMAIL=your_weather_email@example.com
WEATHER_PASSWORD=your_weather_password
```

### Option 2: Using Azure OpenAI

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_api_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-4o  # Optional, defaults to gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview  # Optional

# Weather.com Credentials
WEATHER_EMAIL=your_weather_email@example.com
WEATHER_PASSWORD=your_weather_password
```

### Additional Options

```bash
# Browser Settings (Optional)
HEADLESS=true  # Run browser in headless mode
BROWSER_TIMEOUT=10  # Timeout in seconds for web operations
```

## 🎯 Usage

### Start the Weather Agent

```bash
uv run python src/main.py
```

### Example Conversations

```
You: What's the weather like in London?
Weather Agent: [Searches for London and provides current weather conditions]

You: Add Paris to my favorites
Weather Agent: [Adds Paris to your Weather.com favorites list]

You: What's the 10-day forecast for Tokyo?
Weather Agent: [Retrieves and displays Tokyo's extended forecast]

You: Remove Berlin from favorites
Weather Agent: [Removes Berlin from your favorites list]
```

### Available Commands

- **Weather Queries**: "What's the weather in [city]?"
- **Forecast Requests**: "Show me the 10-day forecast for [city]"
- **Favorites Management**: "Add [city] to favorites" / "Remove [city] from favorites"
- **Exit**: Type "exit" or "quit" to close the application

### Project Structure

```
weather-agent/
├── src/
│   ├── main.py              # CLI entry point and conversation loop
│   ├── weather_agent.py     # Core weather scraping and interaction
│   ├── utils.py             # LLM setup and configuration utilities
│   └── calendar_client.py   # Google Calendar integration (future use)
├── tests/                   # Test suite
├── pyproject.toml          # Project configuration and dependencies
├── .env.example            # Environment variables template
└── README.md              # This documentation
```

## 🔧 Engineering Decisions

### Why Selenium Over Requests/BeautifulSoup?

Weather.com heavily relies on JavaScript for dynamic content loading and user interactions. Selenium provides:

- Reliable handling of dynamic content
- Ability to interact with search dropdowns and buttons
- Proper cookie and session management

### Why LangGraph Over Simple API Calls?

LangGraph provides:

- Structured conversation flow management
- Built-in tool calling capabilities
- State persistence across turns
- Conditional routing based on user intents
- Easy extensibility for additional tools
