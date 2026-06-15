import requests
import re
import time
import os
import sys
import traceback
from datetime import datetime

# 配置信息
HANDLE = "X_moink"
README_PATH = "README.md"

START_MARKER = "<!-- CF-STATS-START -->"
END_MARKER = "<!-- CF-STATS-END -->"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# 中文段位映射
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

def log(message, level="INFO"):
    """统一的日志输出函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")
    sys.stdout.flush()  # 确保日志立即输出

def rank_to_cn(rank: str) -> str:
    """将英文段位转换为中文段位"""
    if not isinstance(rank, str):
        log(f"无效的段位类型: {type(rank)}", "WARNING")
        return "未定级"
    
    rank_lower = rank.lower()
    result = RANK_CN.get(rank_lower, rank)
    log(f"段位转换: '{rank}' -> '{result}'", "DEBUG")
    return result

def fetch_json(url, retry=3, timeout=30):
    """带重试机制的JSON获取函数"""
    last_error = None
    
    for attempt in range(retry):
        try:
            log(f"尝试获取URL (第{attempt + 1}/{retry}次): {url}", "DEBUG")
            response = requests.get(url, headers=HEADERS, timeout=timeout)
            
            # 检查HTTP状态码
            response.raise_for_status()
            
            # 检查响应内容是否为JSON
            try:
                data = response.json()
                log(f"成功获取数据，状态: {data.get('status', 'unknown')}", "DEBUG")
                return data
            except ValueError as e:
                log(f"响应内容不是有效的JSON: {e}", "ERROR")
                log(f"响应内容: {response.text[:200]}", "DEBUG")
                raise
            
        except requests.exceptions.RequestException as e:
            last_error = e
            log(f"网络请求失败: {e}", "WARNING")
            if attempt < retry - 1:
                wait_time = 2 ** attempt  # 指数退避
                log(f"等待 {wait_time} 秒后重试...", "INFO")
                time.sleep(wait_time)
        except Exception as e:
            last_error = e
            log(f"获取数据时发生未知错误: {e}", "ERROR")
            traceback.print_exc()
            if attempt < retry - 1:
                time.sleep(1)
    
    log(f"所有重试都失败了，最后错误: {last_error}", "ERROR")
    raise last_error

def get_user_info():
    """获取用户信息"""
    log("开始获取用户信息...", "INFO")
    url = f"https://codeforces.com/api/user.info?handles={HANDLE}"
    
    try:
        data = fetch_json(url, retry=3)
        
        if data.get("status") != "OK":
            error_msg = data.get("comment", "未知错误")
            log(f"获取用户信息失败: {error_msg}", "ERROR")
            # 返回默认值而不是抛出异常，确保脚本继续运行
            return {
                "handle": HANDLE,
                "rating": "Unrated",
                "maxRating": "Unrated",
                "rank": "unrated",
                "maxRank": "unrated"
            }
        
        if not data.get("result") or len(data["result"]) == 0:
            log("API返回结果为空", "WARNING")
            return {
                "handle": HANDLE,
                "rating": "Unrated",
                "maxRating": "Unrated",
                "rank": "unrated",
                "maxRank": "unrated"
            }
        
        user = data["result"][0]
        log(f"成功获取用户信息: {user.get('handle')}，当前分数: {user.get('rating')}", "INFO")
        
        return {
            "handle": user.get("handle", HANDLE),
            "rating": user.get("rating", "Unrated"),
            "maxRating": user.get("maxRating", "Unrated"),
            "rank": user.get("rank", "unrated"),
            "maxRank": user.get("maxRank", "unrated"),
        }
        
    except Exception as e:
        log(f"获取用户信息时发生严重错误: {e}", "ERROR")
        traceback.print_exc()
        # 返回安全的默认值
        return {
            "handle": HANDLE,
            "rating": "Unrated",
            "maxRating": "Unrated",
            "rank": "unrated",
            "maxRank": "unrated"
        }

def get_solved_count():
    """获取已解决问题数量"""
    log("开始统计已解决问题数量...", "INFO")
    url = f"https://codeforces.com/api/user.status?handle={HANDLE}"
    
    try:
        data = fetch_json(url, retry=3)
        
        if data.get("status") != "OK":
            error_msg = data.get("comment", "未知错误")
            log(f"获取提交记录失败: {error_msg}", "WARNING")
            return 0
        
        if not data.get("result"):
            log("提交记录为空", "WARNING")
            return 0
        
        solved = set()
        log(f"共获取到 {len(data['result'])} 条提交记录", "DEBUG")
        
        for sub in data["result"]:
            if sub.get("verdict") == "OK":
                problem = sub.get("problem", {})
                contest_id = problem.get("contestId")
                index = problem.get("index")
                name = problem.get("name")
                
                if contest_id and index:
                    problem_id = f"{contest_id}{index}"
                    solved.add(problem_id)
                elif name:
                    # 使用问题名称作为备选标识
                    solved.add(name.strip())
        
        solved_count = len(solved)
        log(f"统计完成，已解决问题数量: {solved_count}", "INFO")
        return solved_count
        
    except Exception as e:
        log(f"统计已解决问题时发生错误: {e}", "ERROR")
        traceback.print_exc()
        return 0

def validate_readme_file():
    """验证README文件是否存在且可读"""
    if not os.path.exists(README_PATH):
        log(f"README文件不存在: {README_PATH}", "ERROR")
        return False
    
    if not os.access(README_PATH, os.R_OK):
        log(f"没有读取权限: {README_PATH}", "ERROR")
        return False
    
    if not os.access(README_PATH, os.W_OK):
        log(f"没有写入权限: {README_PATH}", "WARNING")
        # 尝试修改权限
        try:
            os.chmod(README_PATH, 0o644)
            log(f"已修改文件权限: {README_PATH}", "INFO")
        except Exception as e:
            log(f"修改文件权限失败: {e}", "ERROR")
            return False
    
    file_size = os.path.getsize(README_PATH)
    log(f"README文件大小: {file_size} bytes", "DEBUG")
    return True

def update_readme(stats, solved_count):
    """更新README文件"""
    log("开始更新README文件...", "INFO")
    
    # 验证文件
    if not validate_readme_file():
        log("README文件验证失败，无法继续更新", "ERROR")
        return False
    
    try:
        # 读取文件内容
        with open(README_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        
        log(f"README文件读取成功，内容长度: {len(content)}", "DEBUG")
        
        # 检查标记是否存在
        if START_MARKER not in content or END_MARKER not in content:
            log("README中缺少必要的标记，无法更新", "ERROR")
            log(f"需要的开始标记: '{START_MARKER}'", "DEBUG")
            log(f"需要的结束标记: '{END_MARKER}'", "DEBUG")
            # 显示文件内容预览
            preview = content[:500] + "..." if len(content) > 500 else content
            log(f"README内容预览:\n{preview}", "DEBUG")
            return False
        
        # 转换段位为中文
        rank_cn = rank_to_cn(stats["rank"])
        max_rank_cn = rank_to_cn(stats["maxRank"])
        
        # 生成新的统计信息
        new_stats = f"""{START_MARKER}
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

<p><em>最后更新: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</em></p>

</div>
{END_MARKER}"""
        
        # 使用正则表达式替换内容
        pattern = re.compile(
            rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
            re.DOTALL
        )
        
        # 检查模式是否匹配
        if not pattern.search(content):
            log("正则表达式匹配失败，无法找到要替换的内容", "ERROR")
            return False
        
        new_content = pattern.sub(new_stats, content)
        
        # 检查内容是否真的发生了变化
        if new_content == content:
            log("内容没有变化，无需更新文件", "INFO")
            return True
        
        # 写入新内容
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        log("README文件更新成功！", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"更新README时发生错误: {e}", "ERROR")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    log("=" * 50, "INFO")
    log("Codeforces统计信息更新脚本开始执行", "INFO")
    log("=" * 50, "INFO")
    
    try:
        # 获取用户信息
        stats = get_user_info()
        
        # 获取已解决问题数量
        solved_count = get_solved_count()
        
        # 更新README
        success = update_readme(stats, solved_count)
        
        if success:
            log("✅ 脚本执行成功完成！", "SUCCESS")
            sys.exit(0)
        else:
            log("❌ 脚本执行完成，但README更新失败", "WARNING")
            sys.exit(1)
            
    except Exception as e:
        log(f"❌ 脚本执行过程中发生严重错误: {e}", "ERROR")
        traceback.print_exc()
        sys.exit(1)
    finally:
        log("=" * 50, "INFO")
        log("脚本执行结束", "INFO")
        log("=" * 50, "INFO")

if __name__ == "__main__":
    main()
