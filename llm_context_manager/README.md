# LLM Context Manager

A Python tool for managing and summarizing long conversations using OpenAI's GPT models or Google's Gemini API. This tool breaks down large conversations into manageable chunks, summarizes each chunk, and then creates a meta-summary of the entire conversation.

## Features

- Splits long conversations into token-sized chunks
- Summarizes each chunk using OpenAI's GPT models or Google's Gemini API
- Creates a meta-summary of all chunks
- Maintains state between sessions
- Handles large files efficiently
- Token-aware chunking
- Docker support for easy deployment
- Web interface for easy file upload and download

## Setup

### Local Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and configure your settings:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` and set your configuration:
   ```
   # Choose your AI provider
   AI_PROVIDER=openai  # or gemini

   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL_NAME=gpt-4
   MAX_TOKENS_PER_REQUEST=4000

   # Gemini Configuration
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL_NAME=gemini-pro
   ```

### Docker Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and configure as above
3. Build and run using Docker Compose:
   ```bash
   docker-compose up --build
   ```

## Usage

### Web Interface

1. Start the application:
   ```bash
   # Local
   python app.py

   # Docker
   docker-compose up
   ```
2. Open your browser and navigate to `http://localhost:5000`
3. Upload your conversation file (.txt)
4. View the summary and download results

### Command Line Interface

Process a conversation file:
```bash
# Local
python main.py path/to/your/conversation.txt

# Docker
docker-compose run llm-context-manager python main.py conversations/your_file.txt
```

The script will:
1. Read the conversation file
2. Split it into manageable chunks
3. Summarize each chunk using your chosen AI provider (OpenAI or Gemini)
4. Create a meta-summary
5. Save the results in two files:
   - `conversation_state.json`: Contains all summaries and processing state
   - `conversation_state_summary.txt`: Contains the final meta-summary

## Output Files

- `conversation_state.json`: JSON file containing all chunk summaries and processing state
- `conversation_state_summary.txt`: Text file containing the final meta-summary

## Error Handling

The script includes error handling for:
- File reading/writing errors
- API errors (both OpenAI and Gemini)
- Token limit exceeded errors
- File upload/download errors

Errors are logged to the console and displayed in the web interface with appropriate error messages.

## AI Provider Selection

The tool supports two AI providers:
1. OpenAI (GPT models)
2. Google Gemini

You can switch between providers by setting the `AI_PROVIDER` environment variable in your `.env` file:
- For OpenAI: `AI_PROVIDER=openai`
- For Gemini: `AI_PROVIDER=gemini`

Make sure to provide the appropriate API keys for your chosen provider in the `.env` file.