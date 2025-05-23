# MultiAgentTutor
A Tutoring bot that utilises a multi-agentic architecture to resolve your queries!

# AI Tutor System

A multi-agent AI tutoring assistant built using Python, FastAPI, and the Gemini API. This system is designed based on principles based off Google's Agent Development Kit (ADK), featuring a main Tutor Agent that delegates queries to specialized sub-agents (e.g., Math Agent, Physics Agent), which can utilize tools to provide accurate answers.

## Table of Contents

- [Project Description](#project-description)
- [Architecture](#architecture)
- [Features](#features)


## Project Description

*(This section will be elaborated further as the project progresses.)*

The goal of this project is to create an AI-powered tutoring assistant. The main "Tutor Agent" intelligently routes student questions to specialized sub-agents (e.g., Math Agent, Physics Agent). These specialist agents leverage the Gemini API for understanding and response generation, and can also use specific "tools" (like a calculator or a constant lookup) to enhance their accuracy.

## Architecture

*(This section will be updated with a diagram or more detailed explanation of the multi-agent architecture.)*

The system follows a multi-agent architecture:

1.  **User Interface/API Layer:** Accepts user queries.
2.  **Tutor Agent (Orchestrator):** Receives the query, determines its nature (e.g., subject), and delegates it to the appropriate sub-agent.
3.  **Specialist Sub-Agents:**
    *   **Math Agent:** Handles mathematical questions.
    *   **Physics Agent:** Handles physics-related questions.
    *   Each sub-agent uses the Gemini API for core LLM capabilities.
4.  **Tools:**
    *   Specialized functions that sub-agents can invoke (e.g., a calculator for the Math Agent, a physics constant lookup for the Physics Agent).

## Features

*(This list will grow as features are implemented.)*

*   Natural language query understanding.
*   Delegation of queries to specialized agents.
*   Integration with Google's Gemini API for AI responses.
*   Tool usage by specialist agents (e.g., calculator, constant lookup).
*   API endpoint for interaction.
*   (Potentially) A simple web interface.
