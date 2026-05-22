import requests
import re

HANDLE = "X_moink"
README_PATH = "README.md"

START = "<!-- CF-STATS-START -->"
END = "<!-- CF-STATS-END -->"


def get_user_info():
    url = f"https://codeforces.com/api/user.info?handles={HANDLE}"
    data = requests.get(url, timeout=20).json()

    if data["status"] != "OK":
        raise Exception("Failed to fetch user info")

    user = data["result"][0]

    return {
        "handle": user.get("handle", HANDLE),
        "rating": user.get("rating", "Unrated"),
        "maxRating": user.get("maxRating", "Unrated"),
        "rank": user.get("rank", "unrated"),
        "maxRank": user.get("maxRank", "unrated"),
    }


def get_solved_count():
    url = f"https://codeforces.com/api/user.status?handle={HANDLE}"
    data = requests.get(url, timeout=20).json()

    if data["status"] != "OK":
        raise Exception("Failed to fetch submissions")

    solved = set()

    for sub in data["result"]:
        if sub.get("verdict") == "OK":
            problem = sub.get("problem", {})

            contest_id = problem.get("contestId")
            index = problem.get("index")
            name = problem.get("name")

            if contest_id and index:
                problem_id = f"{contest_id}{index}"
            else:
                problem_id = name

            solved.add(problem_id)

    return len(solved)


def update_readme(stats, solved_count):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    new_stats = f"""<!-- CF-STATS-START -->
| Handle | Rating | Max Rating | Rank | Max Rank | Solved |
|---|---:|---:|---|---|---:|
| [{stats["handle"]}](https://codeforces.com/profile/{stats["handle"]}) | {stats["rating"]} | {stats["maxRating"]} | {stats["rank"]} | {stats["maxRank"]} | {solved_count} |
<!-- CF-STATS-END -->"""

    pattern = re.compile(
        rf"{re.escape(START)}.*?{re.escape(END)}",
        re.DOTALL
    )

    new_content = pattern.sub(new_stats, content)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


def main():
    stats = get_user_info()
    solved_count = get_solved_count()
    update_readme(stats, solved_count)


if __name__ == "__main__":
    main()