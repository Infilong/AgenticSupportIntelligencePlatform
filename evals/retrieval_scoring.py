"""Source discovery and passage sufficiency are distinct, frozen evaluation metrics."""

SCORER_VERSION = "active-required-sections-v2"


def normalized(text):
    return " ".join(text.split()).casefold()


def score_case(case, response, facts, versions):
    all_rows = response["results"]
    rows = all_rows[:5]
    sections = {row["section"] for row in rows}
    required_sections = {section for group in case["groups"] for section in group}
    passages = [
        normalized(row["text"])
        for row in rows
        if row["section"] in required_sections
        and versions.get(row["version_id"], {}).get("state") == "active"
    ]
    leakage = [
        row["version_id"]
        for row in all_rows
        if versions.get(row["version_id"], {}).get("state") != "active"
    ]
    groups_found = sum(bool(set(group) & sections) for group in case["groups"])
    fact_results = [
        any(
            normalized(span) in passage for span in alternatives for passage in passages
        )
        for alternatives in facts.get(case["id"], [])
    ]
    return {
        "retrieval_passed": (
            groups_found == len(case["groups"])
            and all(fact_results)
            and not leakage
            and len(all_rows) <= 5
        )
        if case["groups"]
        else None,
        "groups_found": groups_found,
        "fact_results": fact_results,
        "leakage": leakage,
        "result_bound_violated": len(all_rows) > 5,
    }


def safety_passed(cases, probes):
    return all(
        not row["leakage"] and not row["result_bound_violated"]
        for row in [*cases, *probes]
    )


def aggregate(cases):
    scores = {}
    for language in ("en", "ja", "zh", "all"):
        eligible = [
            case
            for case in cases
            if case["groups"] and (language == "all" or case["language"] == language)
        ]
        found = sum(case["groups_found"] for case in eligible)
        total_groups = sum(len(case["groups"]) for case in eligible)
        passed = sum(case["retrieval_passed"] for case in eligible)
        scores[language] = {
            "passed": passed,
            "total": len(eligible),
            "case_success_at_5": passed / len(eligible),
            "groups_found": found,
            "total_groups": total_groups,
            "section_recall_at_5": found / total_groups,
        }
    return scores
