from business_assistant.ui.processor import build_structured_output
import json


def main():
    sample = '{"trends": "Revenue up 5% Q/Q", "averages": {"AOV": 45.2}}'
    out = build_structured_output(sample, ["Policy A: revenue recognition"], "User said prior recommendations were unclear")
    print("OK" if isinstance(out, dict) and "summary_of_findings" in out else "FAIL")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
