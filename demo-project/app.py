from flask import Flask, request, Response, stream_with_context
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv
import time
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.openai.com/v1"
)

# Create or load assistant
def get_or_create_assistant():
    assistant_id = os.getenv("ASSISTANT_ID")
    
    # If we have an assistant ID, verify it exists
    if assistant_id:
        try:
            client.beta.assistants.retrieve(assistant_id)
            return assistant_id
        except Exception:
            print(f"Could not find assistant with ID: {assistant_id}")
            assistant_id = None
    
    # Create new assistant if needed
    if not assistant_id:
        assistant = client.beta.assistants.create(
            name="Chat Assistant",
            description="A helpful chat assistant that can write code and process files",
            instructions="""You are a helpful and knowledgeable assistant that excels at:
            1. Providing clear and concise responses
            2. Writing and explaining code
            3. Analyzing and processing files
            4. Maintaining context throughout conversations
            Always format code blocks properly and explain your reasoning.""",
            model="gpt-4-turbo-preview",
            tools=[{
                "type": "code_interpreter"
            }],
            temperature=0.7,
            response_format={"type": "text"}
        )
        print(f"Created new assistant with ID: {assistant.id}")
        return assistant.id
    
    return assistant_id

# Initialize assistant
ASSISTANT_ID = get_or_create_assistant()

@app.route("/", methods=["GET"])
def hello():
    return "Hello, World!"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "")
    thread_id = data.get("thread_id")
    
    try:
        # Create a new thread if none exists
        if not thread_id:
            thread = client.beta.threads.create()
            thread_id = thread.id
        
        # Add message to thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        
        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )
        
        def generate():
            while True:
                # Check run status
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                if run_status.status == "completed":
                    # Retrieve messages
                    messages = client.beta.threads.messages.list(thread_id=thread_id)
                    latest_message = messages.data[0]
                    if latest_message.role == "assistant":
                        response_data = {
                            "content": latest_message.content[0].text.value,
                            "thread_id": thread_id
                        }
                        yield f"data: {json.dumps(response_data)}\n\n"
                    break
                elif run_status.status == "failed":
                    error_data = {
                        "error": "Assistant run failed",
                        "thread_id": thread_id
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
                
                time.sleep(0.5)
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream'
        )
        
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return {"error": "No file provided"}, 400
    
    file = request.files["file"]
    
    try:
        # Upload file to OpenAI
        openai_file = client.files.create(
            file=file.stream,
            purpose="assistants"
        )
        
        # Attach file to assistant
        client.beta.assistants.update(
            assistant_id=ASSISTANT_ID,
            file_ids=[openai_file.id]
        )
        
        return {"file_id": openai_file.id}
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(debug=True)