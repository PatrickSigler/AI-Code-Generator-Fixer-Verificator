# PyCodeFixer

A Flask web application that automatically debugs Python code using OpenAI GPT. Submit your code and desired output through a clean interface or API, and let AI fix it for you.

## Features

- 🔍 Automatic code debugging using OpenAI's GPT models
- 🔄 Iterative improvement until code produces expected output
- 💻 Clean web interface for code submission
- 🔌 API endpoint for integration with other tools
- ⏱️ Rate limiting to prevent API abuse
- 🛡️ Secure handling of API keys via environment variables

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/PatrickSigler/AI-Code-Generator-Fixer-Verificator
   cd PyCodeFixer
   ```

2. Install dependencies:
   ```bash
   pip install flask openai python-dotenv
   ```

3. Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Open your browser and go to `http://localhost:5000`

3. Enter your Python code and desired output (if any)

4. Click "Debug Code" and wait for the AI to fix your code

## API Usage

You can also use the API endpoint directly:

```bash
curl -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello, wrld!\")", "desiredOutput": "Hello, world!"}'
```

## Configuration

The following environment variables can be set in the `.env` file:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `PORT`: Port to run the server on (default: 5000)
- `FLASK_DEBUG`: Set to "true" for debug mode (default: "false")

## How It Works

1. User submits code and optional desired output
2. Code is executed in a sandboxed environment
3. If there are errors or the output doesn't match expectations:
   - AI analyzes the code and suggests fixes
   - Fixed code is executed and checked again
   - Process repeats up to 3 times or until code works correctly
4. Final code and output are returned to the user
