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

### answer_follow_up_question_node(state) → state
- If `current_follow_up` exists, it asks a **binary QA chain** (BINARY_QUESTION_CHAIN) by appending the follow-up prompt to the original notice message, gets a boolean answer, and records it in state["follow_ups"].

### route_follow_up_edge(state) → "answer_follow_up_question" | END
- If there’s a pending follow-up (`current_follow_up`), loop to answer it; otherwise **end**.

### How it runs end-to-end
- Parse the notice into structured data
- Decide escalation via text rule and fine threshold
- 
## binary_questions.py
### 1. Imports
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
```
- `ChatOpenAI`: lets you call an OpenAI model (like GPT-4o mini).
- `ChatPromptTemplate`: defines reusable prompt templates for LangChain.
- `BaseModel, Field`: Pydantic models to validate and structure the output.

### 2. BinaryAnswer class
```python
class BinaryAnswer(BaseModel):
    is_true: bool = Field(
        description="Whether the answer to the question is yes or no. True if yes otherwise False."
    )

```
- A **Pydantic schema** that defines the structured output format.
- It has one field:
    - is_true: bool → will be True for “yes” answers, False for “no”.
- The description helps LangChain understand how to map the LLM’s answer into structured output.
### 3. Prompt template
```python
binary_question_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            Answer this question as True for "yes" and False for "no".
            No other answers are allowed:

            {question}
            """,
        )
    ]
)
```
- This creates a **system-level instruction prompt**.
### 4. LLM setup
```python
binary_question_model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```
- Instantiates an OpenAI chat model (cheap, small GPT-4o).
- `temperature=0` makes answers deterministic — the model won’t “get creative.”
### 5. Chain Definition
```python
BINARY_QUESTION_CHAIN = (
    binary_question_prompt
    | binary_question_model.with_structured_output(BinaryAnswer)
)
```

- Start with `binary_question_prompt`.
- Pipe (|) its output into the LLM (`binary_question_model`).
- Use `.with_structured_output(BinaryAnswer)` to ensure the LLM’s response is parsed into your BinaryAnswer schema (so you always get a `BinaryAnswer(is_true=True/False)` object).

## escalation_check.py
### 1. Imports
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

```

### 2. 

## notice_extraction.py
### 1. 
### 2. NoticeEmailExtract schema
- **Fields**:
    - `date_of_notice_str`: raw string for notice date (excluded from representation, internal only).
    - `entity_name`: sender’s name.
    - `entity_phone`: sender’s phone.
    - 
### 3. Helper to convert strings to dates
```python
@staticmethod
def _convert_string_to_date(date_str: str | None) -> date | None:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception as e:
        print(e)
        return None

```
- Safely converts a string in `YYYY-mm-dd` format into a Python date object.
- Returns `None` if conversion fails.

### 4. Computed fields
```python
@computed_field
@property
def date_of_notice(self) -> date | None:
    return self._convert_string_to_date(self.date_of_notice_str)

@computed_field
@property
def compliance_deadline(self) -> date | None:
    return self._convert_string_to_date(self.compliance_deadline_str)

```
- These are **derived properties** based on the raw string fields.
- Example: If `date_of_notice_str="2025-09-21"`, then `date_of_notice` will return a real `datetime.date(2025, 9, 21)`.
- Same for compliance deadline.
- This ensures you always get **Python-native date objects** in addition to the raw string.

#### What is `@property` in Python?
- `@property` is a built-in Python decorator.
- It lets you define a method that you can access like an attribute.
- Example:
```python
class Example:
    def __init__(self, x: int):
        self.x = x

    @property
    def double(self):
        return self.x * 2

e = Example(5)
print(e.double)  # 10 (calls the method but looks like a field)

```

#### What is `@computed_field` in Pydantic?
- In Pydantic v2, @computed_field tells Pydantic:
    - “This property should be treated as part of the model’s fields.”
    - Even though it’s computed dynamically, it becomes part of the model’s schema and serialization (dict(), json()).

- example:
```python
from pydantic import BaseModel, computed_field

class Rectangle(BaseModel):
    width: int
    height: int

    @computed_field
    @property
    def area(self) -> int:
        return self.width * self.height

r = Rectangle(width=5, height=10)
print(r.area)          # 50 (property access)
print(r.model_dump())  # {'width': 5, 'height': 10, 'area': 50}
```

### 5. Model setup
```python
escalation_check_model = ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0, 
    api_key=os.getenv('OPENAI_API_KEY')
)
```
- Uses **GPT-4o-mini** (fast, cheap).
- temperature=0 → deterministic, consistent answers.
- API key is pulled from environment variables (`.env`).

### 6. Chain definition
```python
ESCALATION_CHECK_CHAIN = (
    escalation_prompt
    | escalation_check_model.with_structured_output(EscalationCheck)
)

```
- Builds the **LangChain pipeline**:
    - Start with the `escalation_prompt` (instructions).
    - Pass it to the `escalation_check_model`.
    - Use .with_structured_output(EscalationCheck) so the output is always parsed into the schema (needs_escalation: bool).