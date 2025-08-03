# JIRA Requirement Analysis Agent: Project Flow & Future Enhancements

This document outlines the architecture and data flow of the JIRA Requirement Analysis Agent, an AI-powered tool designed to improve the software development lifecycle (SDLC) by providing multi-perspective analysis of software requirements.

## 📌 JIRA Requirement Analysis Agent – Architecture Diagram

```plaintext
                             ┌───────────────────────────────────────┐
                             │           🌐 User (Browser)           │
                             │ ────────────────┬──────────────────── │
                             │                 │                     │
                             │    1. Paste JIRA ticket & click       │
                             │       "Analyze Requirement"           │
                             └──────┬─────────────────┬─────────────┘
                                    │                 │
                                    ▼                 ▼

                      ┌───────────────────────────────┐
                      │       🌈 Frontend (HTML/JS)   │
                      │      Tailwind CSS + JS + UX   │
                      └───────────────────────────────┘
                                    │
                     2. POST /analyze {ticket} (JSON)
                                    │
                                    ▼

            ┌─────────────────────────────────────────────┐
            │            🚀 Backend (Flask Server)         │
            │     - API endpoint `/analyze`                │
            │     - Validates & routes ticket to LLM       │
            │     - Handles error response gracefully      │
            └─────────────────────────────────────────────┘
                                    │
                    3. analyze_jira_ticket(ticket_text)
                                    │
                                    ▼

            ┌─────────────────────────────────────────────┐
            │            🧠 AI Core (LangChain + Gemini)   │
            │ ┌─────────────────────────────────────────┐ │
            │ │ 🔹 LangChain with Gemini Pro            │ │
            │ │ 🔹 Prompt Engineering (with roles)      │ │
            │ │ 🔹 Pydantic Schema Validation           │ │
            │ │ 🔹 JsonOutputParser                     │ │
            │ └─────────────────────────────────────────┘ │
            │ - Generates structured JSON for:             │
            │   - Developer View                           │
            │   - QA View                                  │
            │   - Product Manager View                     │
            └─────────────────────────────────────────────┘
                                    │
            4. Structured JSON → Flask → JSON Response
                                    │
                                    ▼

                  ┌────────────────────────────────────┐
                  │         🌈 Frontend Renderer        │
                  │ - Renders JSON into tabs            │
                  │ - Mermaid.js injected if needed     │
                  │ - Conditional SVG diagram rendering │
                  └────────────────────────────────────┘
                                    │
                  5. Dynamic display of all perspectives
                                    ▼
                             ┌──────────────────┐
                             │  Final Output UI │
                             └──────────────────┘
                             

```

## 1. Project Goal

The primary goal of this project is to automate the initial analysis of a JIRA ticket. By leveraging a powerful Large Language Model (LLM), the agent provides a structured breakdown of the requirement from the perspectives of a Developer, a QA Engineer, and a Product Manager. This saves time, identifies potential issues early, and ensures all team members have a shared understanding of the task at hand.

## 2. High-Level Architecture

The application is built with a simple but powerful architecture consisting of three main components:

- **Frontend (UI):** A single-page web interface built with HTML and styled with Tailwind CSS. It's responsible for capturing user input and displaying the final analysis.

- **Backend (API Server):** A lightweight web server built with Python and the Flask framework. It serves the frontend and provides an API endpoint to handle analysis requests.

- **AI Core (Analysis Engine):** The brain of the application, powered by Google's Gemini Pro model via the langchain-google-genai library. It performs the actual requirement analysis.

## 3. Step-by-Step Data Flow

### Step 1: User Submits a JIRA Ticket

- The user navigates to the web interface and pastes the full text of a JIRA ticket description into the provided textarea.
- The user clicks the "Analyze Requirement" button.

### Step 2: Frontend Sends Request to Backend

- The browser's JavaScript captures the text from the textarea.
- It initiates an asynchronous fetch request to the `/analyze` API endpoint on the Flask server.
- The request is a POST request with a JSON payload containing the ticket description (e.g., `{ "ticket": "As a user, I want..." }`).
- While waiting for the response, the UI is updated to show a loading state (the button is disabled and a spinner appears).

### Step 3: Backend Processes the Request

- The Flask server receives the POST request at the `/analyze` route.
- It validates the incoming JSON to ensure the ticket description is present and not empty.
- It calls the core `analyze_jira_ticket` function, passing the ticket description to it.

### Step 4: AI Core Performs the Analysis

This is the most critical part of the flow:

- **Model Initialization:** The `analyze_jira_ticket` function initializes the `ChatGoogleGenerativeAI` model (Gemini).
- **Structured Output Definition:** It defines a required JSON output structure using Pydantic models. This structure is nested, with top-level keys for `developer_view`, `qa_view`, and `product_manager_view`.
- **Prompt Engineering:** A detailed prompt template is constructed. This prompt instructs the AI to act as an expert assistant and to fill out the pre-defined JSON structure by analyzing the ticket from the three different role perspectives.
- **Single API Call:** The prompt, the ticket description, and the JSON format instructions are combined and sent to the Gemini API in a single, efficient call.
- **JSON Parsing:** The AI's response, which is a JSON string, is automatically parsed by LangChain's `JsonOutputParser` into a Python dictionary that matches the Pydantic model.

### Step 5: Backend Returns the Analysis

- The Flask server receives the structured Python dictionary from the AI Core.
- It serializes this dictionary back into a JSON response and sends it back to the frontend with a `200 OK` status code.
- If any errors occurred during the AI call, a structured error JSON is returned instead.

### Step 6: Frontend Renders the Results

- The JavaScript in the browser receives the JSON response from the server.
- It dynamically generates HTML to display the analysis within the results div.

    - **Role-Specific Tabs:** It creates a tabbed interface for the Developer, QA, and Product Manager views.
    - **Conditional Diagram Rendering:** It specifically checks the `developer_view.diagram_analysis.is_required` flag.
        - If true, it injects the Mermaid.js script into the page and calls the Mermaid library to render the script into an SVG diagram.
        - If false, it simply displays the AI's text explanation for why a diagram was not needed.
    - The results are displayed, and the UI is returned to its initial, interactive state.

# 🚀 Future Enhancements by Team QB

## 1. 🔄 Direct JIRA Integration & integration with real code.
Automatically fetch and update JIRA tickets in real-time, eliminating the need for manual copy-paste and improving efficiency.

## 2. 💬 Slack/Teams Plugin
Seamlessly share AI-generated analysis within Slack or Microsoft Teams channels to keep all stakeholders aligned.
