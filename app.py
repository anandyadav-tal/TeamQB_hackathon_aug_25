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
from flask import Flask, render_template, request, jsonify
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Dict

# --- Configuration & Initialization ---
load_dotenv()

app = Flask(__name__)

# --- 1. Define the Structured Output for the AI ---
# This Pydantic model tells the AI exactly how to format its response.
# This ensures we get reliable, structured JSON every time.
class RequirementAnalysis(BaseModel):
    """Data model for a JIRA requirement analysis."""
    clarifying_questions: List[str] = Field(description="Questions for the product owner to fill in missing details or resolve ambiguities.")
    acceptance_criteria_review: List[Dict[str, str]] = Field(description="A review of existing acceptance criteria, suggesting improvements or new criteria. Each item should have a 'criteria' and a 'suggestion'.")
    potential_blockers: List[str] = Field(description="A list of potential technical or logical blockers, dependencies, or risks.")
    required_testing: Dict[str, List[str]] = Field(description="A dictionary outlining functional tests and edge cases for QA. Keys should be 'functional_tests' and 'edge_cases'.")
    complexity_analysis: Dict[str, str] = Field(description="A qualitative complexity score (Low, Medium, High) for both development and QA efforts. Keys should be 'development' and 'qa'.")

# --- 2. The Core AI Logic ---

def analyze_jira_ticket(ticket_description: str):
    """
    Analyzes a JIRA ticket description using the Gemini model.

    Args:
        ticket_description: The full text content of the JIRA ticket.

    Returns:
        A dictionary containing the structured analysis.
    """
    # Initialize the Gemini model
    # Using gemini-1.5-flash for its speed, large context, and reasoning capabilities.
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)

    # Set up the output parser
    parser = JsonOutputParser(pydantic_object=RequirementAnalysis)

    # The prompt is the most critical piece. It's engineered to make the AI
    # adopt different personas and structure its thinking process.
    prompt_template = """
    You are an expert AI assistant designed to analyze software requirements for an agile team.
    Your task is to thoroughly analyze the following JIRA ticket description from three perspectives:
    1.  **A Senior Developer:** Focus on technical feasibility, potential blockers, and implementation details.
    2.  **A QA Engineer:** Focus on testability, edge cases, and ensuring the requirements are clear enough to write test plans.
    3.  **A Product Manager:** Focus on clarity, completeness, and business value.

    **Analysis Process:**
    1.  **Internal Monologue (Chain of Thought):** First, think step-by-step about the request. Identify the core feature, the user, and the goal. Break down the requirements into smaller pieces. Consider what information is present and what is missing.
    2.  **Generate the Analysis:** Based on your internal monologue, generate a complete analysis. Fill in all the required fields. Be concise but thorough.

    **JIRA TICKET DESCRIPTION:**
    ---
    {ticket_description}
    ---

    **OUTPUT FORMAT:**
    Provide your final analysis in a valid JSON object that strictly follows this format:
    {format_instructions}
    """

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["ticket_description"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    # Create the chain of operations: prompt -> model -> parser
    chain = prompt | llm | parser

    print("Invoking AI model to analyze the ticket...")
    try:
        analysis_result = chain.invoke({"ticket_description": ticket_description})
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
    """Renders the main HTML page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """API endpoint that receives the ticket and returns the analysis."""
    data = request.get_json()
    ticket_description = data.get('ticket')

    if not ticket_description or len(ticket_description.strip()) < 20:
        return jsonify({"error": "Please provide a JIRA ticket description of at least 20 characters."}), 400

    result = analyze_jira_ticket(ticket_description)

    return jsonify(result)


if __name__ == '__main__':
    # Note: `debug=True` is great for development but should be `False` in production.
    # `use_reloader=False` can be helpful if you are running setup tasks.
    ###changes done by sanket##
    app.run(app.run(host="0.0.0.0", port=5000, debug=True))
