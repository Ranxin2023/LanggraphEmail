# LangGraph Email Escalation
## Introduction
This project demonstrates how to build an **automated workflow with LangGraph** for processing notice emails and deciding whether they require escalation. The system uses LLM-powered chains to parse incoming notices, check escalation criteria (based on text rules and fine thresholds), and then either:
- **Send escalation emails** to a predefined list of recipients, or
- **Create a legal ticket** with structured follow-up questions automatically answered by the model.

## Key Features
- **Notice Parsing**: Extracts structured fields (dates, site, violations, fines) from raw notice messages.
- **Escalation Logic**: Applies both text rules and numeric thresholds to decide if a notice requires escalation.
- **Follow-Up Automation:** Loops through yes/no clarification questions using a binary-answer LLM chain.
- **Graph-Oriented Workflow**: Built with LangGraph for clarity, modularity, and state management.

