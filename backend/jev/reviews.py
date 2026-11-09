import os
import re

import requests


rubrics = {
    "effectiveness": (
        "How well does the tool accomplish its advertised tasks, based only on `review`?",
        [
            "Does not accomplish the task at all.",
            "Almost always fails to accomplish the task.",
            "Accomplishes very little of the task.",
            "Accomplishes part of the task, with major shortcomings.",
            "Produces mixed results; substantial correction is needed.",
            "Mostly accomplishes the task, with noticeable shortcomings.",
            "Accomplishes the task well, with some correction needed.",
            "Produces strong results, with minor shortcomings.",
            "Produces excellent results, requiring almost no correction.",
            "Fully accomplishes the task with outstanding results.",
        ],
    ),
    "ease_of_use": (
        "How easy is the tool for a nontechnical business owner to operate, based only on `review`?",
        [
            "Impossible to operate without extensive technical expertise.",
            "Extremely difficult; expert help is needed for most tasks.",
            "Very difficult; substantial technical knowledge is needed.",
            "Difficult; frequent help or workarounds are needed.",
            "Confusing but usable after considerable learning.",
            "Usable with some learning and occasional help.",
            "Fairly easy; a nontechnical user can work independently after setup.",
            "Easy to learn and use, with minor friction.",
            "Very easy; almost no guidance is needed.",
            "Effortless and intuitive for a nontechnical first-time user.",
        ],
    ),
}


def analyze_review(review: str) -> dict:
    questions = {}
    for metric, (instructions, criteria) in rubrics.items():
        questions[metric] = {
            "type": "score",
            "instructions": instructions,
            "criteria": criteria,
        }
        questions[f"{metric}_mentioned"] = {
            "type": "noul",
            "instructions": (
                f"Does `review` contain evidence to answer this question: {instructions} "
                "General praise or criticism alone is insufficient."
            ),
        }

    # Jev selects existing text; it cannot generate a price string.
    sentences = {
        f"sentence_{i}": sentence
        for i, sentence in enumerate(re.split(r"(?<=[.!?])\s+", review.strip()))
    }
    questions["price"] = {
        "type": "choice",
        "instructions": (
            "Select the sentence in `review` that mentions the tool's price, cost, "
            "subscription, or being free. Prefer a sentence with a specific amount. "
            "Choose none if pricing is not mentioned."
        ),
        "criteria": {"none": "Pricing is not mentioned.", **sentences},
    }

    response = requests.post(
        "https://openrouter.ai/api/alpha/decisions",
        headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
        json={
            "model": "typesafe/jev-1.13",
            "state": {"review": review},
            "questions": questions,
        },
        timeout=30
    )

    response.raise_for_status()
    answers = response.json()["answers"]
    result = {
        metric: (
            round(answers[metric]["score"] + 1, 2)  # Jev's ten tiers are indexed 0–9.
            if answers[f"{metric}_mentioned"]["noul"] >= 0.5 else None
        )
        for metric in rubrics
    }
    price_choice = answers["price"]["choice"]
    result["price"] = None if price_choice == "none" else sentences[price_choice]
    return result
