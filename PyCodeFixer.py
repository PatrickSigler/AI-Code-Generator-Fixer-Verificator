from flask import Flask, request, jsonify, render_template_string
import subprocess
import os
import logging
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Set OpenAI API key from environment variable or hardcode for testing
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")

# Initialize OpenAI client properly
try:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {str(e)}")
    client = None

# Default HTML template for the home page
HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Code Debugging Platform</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #333; }
        textarea { width: 100%; height: 200px; margin-bottom: 10px; padding: 8px; }
        input[type="text"] { width: 100%; padding: 8px; margin-bottom: 10px; }
        button { background-color: #4CAF50; border: none; color: white; padding: 10px 15px; cursor: pointer; }
        button:hover { background-color: #45a049; }
        pre { background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .error { color: red; }
        .success { color: green; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Code Debugging Platform</h1>
        <p>Submit your Python code and desired output below:</p>
        
        <form id="codeForm">
            <label for="code">Code:</label>
            <textarea id="code" name="code" placeholder="Enter your Python code here..."></textarea>
            
            <label for="desiredOutput">Desired Output (optional):</label>
            <input type="text" id="desiredOutput" name="desiredOutput" placeholder="Enter the expected output...">
            
            <button type="button" onclick="submitCode()">Debug Code</button>
        </form>
        
        <div id="result" style="margin-top: 20px;"></div>
        
        <script>
            function submitCode() {
                const code = document.getElementById('code').value;
                const desiredOutput = document.getElementById('desiredOutput').value;
                
                if (!code) {
                    document.getElementById('result').innerHTML = '<p class="error">Please enter code.</p>';
                    return;
                }
                
                document.getElementById('result').innerHTML = '<p>Processing...</p>';
                
                fetch('/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        code: code,
                        desiredOutput: desiredOutput
                    }),
                })
                .then(response => response.json())
                .then(data => {
                    let resultHTML = '';
                    
                    if (data.error) {
                        resultHTML += `<p class="error">Error: ${data.error}</p>`;
                    } else {
                        resultHTML += `<p class="success">${data.message}</p>`;
                    }
                    
                    if (data.result) {
                        resultHTML += '<h3>Fixed Code:</h3>';
                        resultHTML += `<pre>${data.result}</pre>`;
                    }
                    
                    resultHTML += '<h3>Output:</h3>';
                    resultHTML += `<pre>${data["Code output"] || "No output"}</pre>`;
                    
                    if (data["Desired Output"]) {
                        resultHTML += '<h3>Desired Output:</h3>';
                        resultHTML += `<pre>${data["Desired Output"]}</pre>`;
                    }
                    
                    document.getElementById('result').innerHTML = resultHTML;
                })
                .catch(error => {
                    document.getElementById('result').innerHTML = `<p class="error">Error: ${error.message}</p>`;
                });
            }
        </script>
    </div>
</body>
</html>
"""

# Rate limiting variables
request_timestamps = {}
RATE_LIMIT = 10  # requests per minute
RATE_WINDOW = 60  # seconds

class OpenAIHandler:
    """Class to handle OpenAI API interactions"""
    
    @staticmethod
    def check_output_match(code_output, desired_output):
        """
        Check if code output matches the desired output using AI or direct comparison
        """
        if not desired_output:
            # If no desired output is provided, assume the code works
            return True
            
        try:
            # First try direct string comparison
            if code_output.strip() == desired_output.strip():
                return True
                
            # If OpenAI client is available, use it for more complex comparison
            if client:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a code verification assistant. Compare the actual output to the desired output and respond with 'yes' if they match or 'no' if they don't. Numbers must match exactly."},
                        {"role": "user", "content": f"Does this code output: '{code_output}' match the desired output: '{desired_output}'? Answer with only 'yes' or 'no'."}
                    ],
                    max_tokens=10,
                    temperature=0.3
                )
                
                result = response.choices[0].message.content.strip().lower()
                logger.info(f"Output comparison result: {result}")
                return result == "yes"
            else:
                # Fallback if OpenAI client is not available
                return False
            
        except Exception as e:
            logger.error(f"Error in check_output_match: {str(e)}")
            return False
    
    @staticmethod
    def debug_code(code, desired_output=None):
        """
        Debug code using OpenAI API or simple syntax fixes if API is unavailable
        """
        if not client:
            # Basic code fixes if OpenAI is not available
            logger.warning("OpenAI client unavailable. Attempting basic fixes.")
            return OpenAIHandler.basic_code_fixes(code)
            
        try:
            prompt_content = f"Fix or complete this Python code:"
            
            if desired_output:
                prompt_content += f" The code should produce this output: '{desired_output}'."
                
            prompt_content += f"\n\nCode:\n{code}\n\nReturn only the fixed code with no explanations."
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a Python expert that fixes or completes code. Return only the fixed code with no additional text or explanations."},
                    {"role": "user", "content": prompt_content}
                ],
                max_tokens=1000,
                temperature=0.5
            )
            
            result = response.choices[0].message.content.strip()
            # Remove markdown code block syntax if present
            if result.startswith("```python"):
                result = result[len("```python"):].strip()
            if result.startswith("```"):
                result = result[3:].strip()
            if result.endswith("```"):
                result = result[:-3].strip()
                
            return result
            
        except Exception as e:
            logger.error(f"Error in debug_code: {str(e)}")
            return OpenAIHandler.basic_code_fixes(code)
    
    @staticmethod
    def basic_code_fixes(code):
        """Basic code fixes when OpenAI API is unavailable"""
        # Common syntax error fixes
        fixed_code = code
        
        # Try to fix indentation errors
        lines = fixed_code.split('\n')
        for i in range(len(lines)):
            lines[i] = lines[i].rstrip()
        fixed_code = '\n'.join(lines)
        
        # Fix missing colons after if/for/while statements
        import re
        for control in ['if', 'for', 'while', 'def', 'class', 'elif', 'else', 'except', 'finally']:
            pattern = f"(\\s*{control}\\s+[^:\\n]+)\\s*$"
            fixed_code = re.sub(pattern, r'\1:', fixed_code, flags=re.MULTILINE)
        
        # Add simple print statement if code is empty or just "no code"
        if not fixed_code.strip() or fixed_code.strip() == "no code":
            fixed_code = 'print("Hello, World!")'
            
        return fixed_code

class CodeExecutor:
    """Class to handle code execution"""
    
    @staticmethod
    def execute_python_code(code):
        """
        Execute Python code in a controlled environment
        """
        # Handle empty code case
        if not code.strip() or code.strip() == "no code":
            return "Error: No valid code provided to execute"
            
        try:
            # Create a temporary file for the code
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as temp:
                temp.write(code)
                temp_filename = temp.name
                
            try:
                # Set timeout for code execution to prevent infinite loops
                result = subprocess.run(
                    ['python', temp_filename],
                    capture_output=True,
                    text=True,
                    timeout=5,  # 5 second timeout
                    env=dict(os.environ, PYTHONIOENCODING='utf-8')
                )
                
                if result.returncode != 0:
                    return f"Error: {result.stderr.strip()}"
                
                return result.stdout.strip()
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_filename)
                except:
                    pass
            
        except subprocess.TimeoutExpired:
            return "Error: Code execution timed out (5 seconds limit)."
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}")
            return f"Error: {str(e)}"

@app.route('/')
def home():
    """Render home page with code submission form"""
    return render_template_string(HOME_TEMPLATE)

def apply_rate_limit(ip_address):
    """Apply rate limiting for API requests"""
    current_time = time.time()
    
    # Remove old timestamps
    for ip in list(request_timestamps.keys()):
        request_timestamps[ip] = [t for t in request_timestamps[ip] if current_time - t < RATE_WINDOW]
        if not request_timestamps[ip]:
            del request_timestamps[ip]
    
    # Check rate for current IP
    if ip_address not in request_timestamps:
        request_timestamps[ip_address] = []
    
    if len(request_timestamps[ip_address]) >= RATE_LIMIT:
        return False
    
    # Add current request timestamp
    request_timestamps[ip_address].append(current_time)
    return True

@app.route('/submit', methods=['POST'])
def submit_code():
    """API endpoint to submit code for debugging and execution"""
    # Apply rate limiting
    if not apply_rate_limit(request.remote_addr):
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
            
        code = data.get('code')
        desired_output = data.get('desiredOutput', '').strip()
        
        if not code or not isinstance(code, str):
            return jsonify({"error": "No valid code provided"}), 400
        
        # Initialize variables for debugging loop
        completed = False
        iterations = 0
        max_iterations = 3  # Reduced from 5 to 3 for efficiency
        current_code = code.strip()
        code_output = ""
        
        # Main debugging loop
        while not completed and iterations < max_iterations:
            iterations += 1
            logger.info(f"Debug iteration {iterations}")
            
            # Execute current code
            code_output = CodeExecutor.execute_python_code(current_code)
            logger.info(f"Code output: {code_output}")
            
            # Check if output matches desired output
            if desired_output:
                completed = OpenAIHandler.check_output_match(code_output, desired_output)
                if completed:
                    break
            else:
                # If no error in output and no desired output specified, consider it complete
                completed = not code_output.startswith("Error:")
                if completed:
                    break
            
            # Debug the code if not completed
            current_code = OpenAIHandler.debug_code(current_code, desired_output)
        
        # Final execution if needed
        if iterations > 0 and (not completed or not code_output):
            code_output = CodeExecutor.execute_python_code(current_code)
        
        # Prepare response
        if not completed and iterations >= max_iterations:
            return jsonify({
                "error": "Maximum debugging iterations reached",
                "result": current_code,
                "Code output": code_output,
                "Desired Output": desired_output
            }), 400
        else:
            return jsonify({
                "result": current_code,
                "Code output": code_output,
                "Desired Output": desired_output,
                "message": "Code successfully fixed" if code != current_code else "Code works as is",
                "iterations": iterations
            })
            
    except Exception as e:
        logger.error(f"Error in submit_code: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    # Check if API key is set
    if OPENAI_API_KEY == "your-api-key-here":
        logger.warning("OpenAI API key not set! Some features will be limited.")
        print("WARNING: OpenAI API key not set! Some features will be limited.")
    
    # Run the Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=os.environ.get("FLASK_DEBUG", "False").lower() == "true", 
            host="0.0.0.0", 
            port=port)
