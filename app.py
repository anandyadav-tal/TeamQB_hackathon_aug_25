# app.py
#
# This file contains the complete backend for your JIRA Analysis Agent MVP.
# It uses Flask to create a web server and the Google Gemini API for AI-powered analysis.
#
# --- SETUP INSTRUCTIONS ---
# 1. Create a project folder and a Python virtual environment.
#
# 2. Save this code as `app.py` inside your project folder.
#
# 3. Create a `templates` folder and save the HTML code (from the comment block below)
#    as `index.html` inside it.
#
# 4. Install the required Python packages:
#    pip install Flask python-dotenv langchain langchain-google-genai
#
# 5. Create a file named `.env` in your project folder.
#
# 6. Add your Google API key to the .env file like this:
#    GOOGLE_API_KEY="your_google_api_key_here"
#
# 7. Run the application from your terminal:
#    flask run
#
# 8. Open your web browser and go to http://127.0.0.1:5000

import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, url_for
import flask
from werkzeug.utils import secure_filename
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Dict

# --- Configuration & Initialization ---
load_dotenv()

UPLOAD_FOLDER = 'uploads'  # Define your upload directory
ALLOWED_EXTENSIONS = {'txt'} # Define allowed extensions
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', UPLOAD_FOLDER)  # Use environment variable or default
app.secret_key = str(b'_5#y2L"F4Q8z\n\xec]/')

class DiagramAnalysis(BaseModel):
    """Data model for the diagram analysis portion of the report."""
    is_required: bool = Field(description="A boolean flag. Set to true if a diagram is helpful, otherwise false.")
    mermaid_script: str = Field(description="If is_required is true, provide a valid Mermaid.js script for a flowchart or sequence diagram. If false, provide a brief explanation why a diagram is not needed.")

class DeveloperView(BaseModel):
    """Analysis from a developer's perspective."""
    potential_blockers: List[str] = Field(description="A list of potential technical or logical blockers, dependencies, or risks.")
    complexity: str = Field(description="A qualitative complexity score (Low, Medium, High) for the development effort.")
    diagram_analysis: DiagramAnalysis = Field(description="An analysis of whether a diagram is needed and the corresponding Mermaid.js script if it is.")

class QAView(BaseModel):
    """Analysis from a QA engineer's perspective."""
    required_testing: Dict[str, List[str]] = Field(description="A dictionary outlining functional tests and edge cases for QA. Keys should be 'functional_tests' and 'edge_cases'.")
    complexity: str = Field(description="A qualitative complexity score (Low, Medium, High) for the QA effort.")

class ProductManagerView(BaseModel):
    """Analysis from a Product Manager's perspective."""
    clarifying_questions: List[str] = Field(description="Questions for the product owner to fill in missing details or resolve ambiguities.")
    acceptance_criteria_review: List[Dict[str, str]] = Field(description="A review of existing acceptance criteria, suggesting improvements or new criteria. Each item should have a 'criteria' and a 'suggestion'.")

class RequirementAnalysis(BaseModel):
    """The main data model for a comprehensive, role-based JIRA requirement analysis."""
    developer_view: DeveloperView
    qa_view: QAView
    product_manager_view: ProductManagerView

# --- 2. The Core AI Logic ---

def analyze_jira_ticket(ticket_description: str, documentation: str = "") -> Dict:
    """
    Analyzes a JIRA ticket description using the Gemini model.

    Args:
        ticket_description: The full text content of the JIRA ticket.

    Returns:
        A dictionary containing the structured analysis.
    """
    # Initialize the Gemini model
    # Using gemini-1.5-flash for its speed, large context, and reasoning capabilities.
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2, api_key="AIzaSyASRVLY3n7c_9peyySMrKyVd5s78AOUoPk")

    # Set up the output parser
    parser = JsonOutputParser(pydantic_object=RequirementAnalysis)

    # The prompt is the most critical piece. It's engineered to make the AI
    # adopt different personas and structure its thinking process.
    prompt_template = """
    You are an expert AI assistant for an agile software team. Your primary task is to analyze a JIRA ticket and provide a comprehensive, structured analysis broken down by team roles.

    **Analysis Process:**
    In a single pass, analyze the JIRA ticket and the provided documentation, if any, from the perspectives of a Developer, a QA Engineer, and a Product Manager.

    - **For the Developer View:** Focus on technical feasibility, implementation risks, dependencies, and decide if a visual diagram is necessary to explain the workflow.
    - **For the QA View:** Focus on testability, identifying functional and edge case scenarios, and assessing testing complexity.
    - **For the Product Manager View:** Focus on requirement clarity, completeness, business value, and suggest improvements to acceptance criteria.

    **Diagram Decision:** As part of the developer analysis, make a specific decision: Does this ticket describe a multi-step process, user flow, or system interaction that would be clarified by a visual diagram?
        - If YES, set `is_required` to `true` and generate a concise Mermaid.js script.
        - If NO (e.g., it's a simple bug fix or text change), set `is_required` to `false` and briefly explain why a diagram isn't necessary.
    
    **JIRA TICKET DESCRIPTION:**
    ---
    {ticket_description}
    ---

    **DOCUMENTATION (if any):**
    ---
    {documentation}
    ---

    **OUTPUT FORMAT:**
    Combine all findings into a single, valid JSON object that strictly follows the nested format requested below. Do not deviate from this structure.
    {format_instructions}
    """
    print(documentation)
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["ticket_description", "documentation"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    # Create the chain of operations: prompt -> model -> parser
    chain = prompt | llm | parser

    print("Invoking AI model to analyze the ticket...")
    try:
        analysis_result = chain.invoke({"ticket_description": ticket_description, "documentation": documentation})
        return analysis_result
    except Exception as e:
        print(f"An error occurred during AI analysis: {e}")
        # In case of an error with the AI, return a structured error message
        return {
            "error": "Failed to get a valid analysis from the AI model. The model might be temporarily unavailable or the request was malformed. Please try again."
        }


# --- 3. Flask Routes (API and Frontend) ---

@app.route('/')
def index():
    """Renders the main page with the upload form."""
    # Clear the uploaded_file key from the session on every page load
    if 'uploaded_file' in flask.session:
        flask.session.pop('uploaded_file')  # Clear the uploaded file name from the session

    upload_form = render_template('upload.html')
    return render_template('index.html', upload_form=upload_form)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handles file uploads."""
    print("Handling file upload...")
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return render_template('upload.html', error="No file part in the request.")
        file = request.files['file']
        # If the user does not select a file, the browser submits an empty file without a filename.
        if file.filename == '':
            return render_template('upload.html', error="No file selected.")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flask.session['uploaded_file'] = filename  # Save the uploaded file name in the session
            return jsonify({"success": True, "message": "File uploaded successfully."})  # Return JSON response for AJAX
    return render_template('upload.html')


def get_uploaded_documentation():
    """Helper function to retrieve the uploaded documentation file."""
    try:
        print(flask.session)
        if 'uploaded_file' in flask.session:
            uploaded_file = flask.session['uploaded_file']
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    flask.session.pop('uploaded_file')  # Clear the uploaded file name from the session after reading
                    return content
    except Exception as e:
        print(f"Error retrieving uploaded documentation: {e}")
    return ""  # Return empty string if no file is uploaded or file doesn't exist

@app.route('/analyze', methods=['POST'])
def analyze():
    """API endpoint that receives the ticket and returns the analysis."""
    data = request.get_json()
    ticket_description = data.get('ticket')

    if not ticket_description or len(ticket_description.strip()) < 20:
        return jsonify({"error": "Please provide a JIRA ticket description of at least 20 characters."}), 400
    # Optional: If you have documentation, you can pass it as well
    documentation = get_uploaded_documentation()
    result = analyze_jira_ticket(ticket_description, documentation)

    return jsonify(result)


# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if __name__ == '__main__':
    # Note: `debug=True` is great for development but should be `False` in production.
    # `use_reloader=False` can be helpful if you are running setup tasks.
    ###changes done by sanket##
    app.run(app.run(host="0.0.0.0", port=5000, debug=True))
