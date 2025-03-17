# AI-Code-Generator-Fixer-Verificator
A Flask web application that automatically debugs Python code using OpenAI GPT. Submit your code and desired output through a clean interface or API, and let AI fix it for you.

Features:

🔍 Automatic code debugging using OpenAI's GPT models

🔄 Iterative improvement until code produces expected output

💻 Clean web interface for code submission

🔌 API endpoint for integration with other tools

⏱️ Rate limiting to prevent API abuse

🛡️ Secure handling of API keys via environment variables


Installation:

Clone the repository:

bashCopygit clone https://github.com/yourusername/PyCodeFixer.git

cd PyCodeFixer


Install dependencies:

bashCopypip install flask openai python-dotenv


Create a .env file in the project root and add your OpenAI API key:

CopyOPENAI_API_KEY=your-api-key-here


Usage:

Start the application:

bashCopypython app.py

Open your browser and go to http://localhost:5000

Enter your Python code and desired output (if any)

Click "Debug Code" and wait for the AI to fix your code


API Usage:

You can also use the API endpoint directly:

bashCopycurl -X POST http://localhost:5000/submit \

  -H "Content-Type: application/json" \
  
  -d '{"code": "print(\"Hello, wrld!\")", "desiredOutput": "Hello, world!"}'
  
Configuration:

The following environment variables can be set in the .env file:


OPENAI_API_KEY: Your OpenAI API key (required)

PORT: Port to run the server on (default: 5000)

FLASK_DEBUG: Set to "true" for debug mode (default: "false")


How It Works:


User submits code and optional desired output

Code is executed in a sandboxed environment

If there are errors or the output doesn't match expectations:


AI analyzes the code and suggests fixes

Fixed code is executed and checked again

Process repeats up to 3 times or until code works correctly



Final code and output are returned to the user
