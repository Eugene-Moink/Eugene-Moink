import requests
import re

UID = "1887785"
README_PATH = "README.md"

START = "<!-- LUOGU-STATS-START -->"
END = "<!-- LUOGU-STATS-END -->"


def format_rank(rank_text: str) -> str:
    rank_text = rank_text.strip()
    return rank_text if rank_text else "N/A"


def get_luogu_info():
    url = f"https://www.luogu.com.cn/user/{UID}"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.luogu.com.cn/",
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    html = response.text

    name_match = re.search(r'<title>\s*([^<]+?)\s*-\s*个人中心', html)
    submitted_match = re.search(r'提交\s*</div>\s*<div[^>]*>\s*(\d+)\s*</div>', html)
    solved_match = re.search(r'通过\s*</div>\s*<div[^>]*>\s*(\d+)\s*</div>', html)
    ranking_match = re.search(r'排名\s*</div>\s*<div[^>]*>\s*([^<\s]+)\s*</div>', html)

    name = name_match.group(1).strip() if name_match else "Morgann"
    submitted = submitted_match.group(1) if submitted_match else "N/A"
    solved = solved_match.group(1) if solved_match else "N/A"
    ranking = format_rank(ranking_match.group(1)) if ranking_match else "N/A"

    return {
        "name": name,
        "uid": UID,
        "submitted": submitted,
        "solved": solved,
        "ranking": ranking,
    }


def update_readme(stats):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    new_stats = f"""<!-- LUOGU-STATS-START -->
| User | UID | Submitted | Solved | Ranking |
|---|---:|---:|---:|---:|
| [{stats["name"]}](https://www.luogu.com.cn/user/{stats["uid"]}) | {stats["uid"]} | {stats["submitted"]} | {stats["solved"]} | {stats["ranking"]} |
<!-- LUOGU-STATS-END -->"""

    pattern = re.compile(
        rf"{re.escape(START)}.*?{re.escape(END)}",
        re.DOTALL
    )

    new_content = pattern.sub(new_stats, content)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


def main():
    stats = get_luogu_info()
    update_readme(stats)


if __name__ == "__main__":
    main()