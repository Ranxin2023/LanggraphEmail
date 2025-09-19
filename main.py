from graphs.notice_extraction import build_notice_extraction_graph
from example_emails import EMAILS
def main():
    initial_state_escalation = {
            "notice_message": EMAILS[0],
            "notice_email_extract": None,
            "escalation_text_criteria": """Workers explicitly violating safety
                                    protocols""",
            "escalation_dollar_criteria": 100_000,
            "requires_escalation": False,
            "escalation_emails": ["brog@abc.com", "bigceo@company.com"],
    }
    NOTICE_EXTRACTION_GRAPH=build_notice_extraction_graph()
    results = NOTICE_EXTRACTION_GRAPH.invoke(initial_state_escalation)
    print(f"the result from notice extraction is {results}")

if __name__=='__main__':
    main()