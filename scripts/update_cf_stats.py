import requests
import re
import time

HANDLE = "X_moink"
README_PATH = "README.md"

START = "<!-- CF-STATS-START -->"
END = "<!-- CF-STATS-END -->"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

RANK_CN = {
    "newbie": "新手",
    "pupil": "入门",
    "specialist": "普及",
    "expert": "提高",
    "candidate master": "省选",
    "master": "大师",
    "international master": "国际大师",
    "grandmaster": "特级大师",
    "international grandmaster": "国际特级大师",
    "legendary grandmaster": "传奇特级大师",
    "unrated": "未定级",
}


def rank_to_cn(rank: str) -> str:
    if not isinstance(rank, str):
        return "未定级"
    return RANK_CN.get(rank.lower(), rank)


def fetch_json(url, retry=3):
    last_error = None

    for _ in range(retry):
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            last_error = e
            time.sleep(1)

    raise last_error


def get_user_info():
    url = f"https://codeforces.com/api/user.info?handles={HANDLE}"
    data = fetch_json(url)

    if data.get("status") != "OK":
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
    data = fetch_json(url)

    if data.get("status") != "OK":
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
    rank_cn = rank_to_cn(stats["rank"])
    max_rank_cn = rank_to_cn(stats["maxRank"])

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    new_stats = f"""<!-- CF-STATS-START -->
<div align="center">

<table>
  <tr>
    <th>用户</th>
    <th>当前分数</th>
    <th>最高分数</th>
    <th>当前段位</th>
    <th>最高段位</th>
    <th>通过题数</th>
  </tr>
  <tr>
    <td><a href="https://codeforces.com/profile/{stats["handle"]}">{stats["handle"]}</a></td>
    <td>{stats["rating"]}</td>
    <td>{stats["maxRating"]}</td>
    <td>{rank_cn}</td>
    <td>{max_rank_cn}</td>
    <td>{solved_count}</td>
  </tr>
</table>

</div>
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