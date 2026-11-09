import json

from reviews import analyze_review


if __name__ == "__main__":
    review = """
    The AI tool produces great results, but the interface
    is confusing and it takes forever to generate anything.
    It costs $20 per month.
    """
    print(json.dumps(analyze_review(review), indent=2))
