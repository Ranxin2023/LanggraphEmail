# Code Explaination
## notice_extraction.py — the LangGraph workflow
### GraphState (TypedDict): Defines the shared state each node reads/writes:
- `notice_message`: raw email/text of the notice
- `notice_email_extract`: structured fields parsed from the notice (type `NoticeEmailExtract`)
- `escalation_text_criteria`: rule string used by a chain to judge if text implies escalation
- `escalation_dollar_criteria`: numeric threshold for fines
- `requires_escalation`: boolean switch set by the check step
- `escalation_emails`: list of recipients
- `follow_ups`: map of follow-up question → boolean answer
- `current_follow_up`: the next follow-up question to ask/answer
### parse_notice_message_node(state) → state
- Uses `NOTICE_PARSER_CHAIN` to extract structured fields from the raw notice_message and stores them in state["notice_email_extract"]. Think: who’s involved, dates, site, potential fine, etc. Logs “Parsing notice…”.
### check_escalation_status_node(state) → state
- Decides if escalation is needed based on two signals:
    - **Text rule**: calls `ESCALATION_CHECK_CHAIN` with `escalation_text_criteria` + message → returns .`needs_escalation` (bool).
    - **Dollar rule**: compares parsed `max_potential_fine` against `escalation_dollar_criteria`.
If either is true, flips state["requires_escalation"] = True. Logs progress.

### send_escalation_email_node(state) → state
- Calls `send_escalation_email(...)` with the parsed extract and the recipient list. Returns state unchanged (side-effect node). 

### create_legal_ticket_node(state) → state
- Calls `create_legal_ticket(...)`, which can return a follow-up question needed to complete the ticket. Stores that in `state["current_follow_up"]`.