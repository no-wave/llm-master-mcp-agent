import arxiv
import json
import os
from typing import List
from mcp.server.fastmcp import FastMCP

# papers 디렉토리 경로
PAPER_DIR = "../../papers"

# FastMCP 서버 초기화
mcp = FastMCP("research")

@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    주제를 기반으로 arXiv에서 논문을 검색하고 해당 정보를 저장합니다.

    Args:
        topic: 검색할 주제
        max_results: 검색할 최대 결과 수 (기본값: 5)

    Returns:
        검색된 논문의 ID 리스트
    """
    client = arxiv.Client()
    search = arxiv.Search(
        query=topic,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )
    papers = client.results(search)

    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)
    file_path = os.path.join(path, "papers_info.json")

    try:
        with open(file_path, "r") as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    paper_ids = []
    for paper in papers:
        pid = paper.get_short_id()
        paper_ids.append(pid)
        papers_info[pid] = {
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'summary': paper.summary,
            'pdf_url': paper.pdf_url,
            'published': str(paper.published.date())
        }

    with open(file_path, "w") as json_file:
        json.dump(papers_info, json_file, indent=2)

    print(f"결과가 다음 위치에 저장되었습니다: {file_path}")
    return paper_ids

@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    모든 주제 디렉토리에서 특정 논문 ID에 대한 정보를 검색합니다.

    Args:
        paper_id: 검색할 논문의 ID

    Returns:
        논문 정보를 담은 JSON 문자열(찾지 못할 경우 오류 메시지)
    """
    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(item_path):
            file_path = os.path.join(item_path, "papers_info.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as json_file:
                        papers_info = json.load(json_file)
                        if paper_id in papers_info:
                            return json.dumps(papers_info[paper_id], indent=2)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"{file_path} 파일 읽기 오류: {e}")
                    continue
    return f"{paper_id} 논문에 대한 저장된 정보를 찾을 수 없습니다."

@mcp.resource("papers://folders")
def get_available_folders() -> str:
    """
    papers 디렉토리의 사용 가능한 주제 폴더 목록을 Markdown 형식으로 반환합니다.
    """
    folders = []
    if os.path.exists(PAPER_DIR):
        for topic_dir in os.listdir(PAPER_DIR):
            topic_path = os.path.join(PAPER_DIR, topic_dir)
            if os.path.isdir(topic_path) and os.path.exists(os.path.join(topic_path, "papers_info.json")):
                folders.append(topic_dir)

    content = "# Available Topics\n\n"
    if folders:
        for folder in folders:
            content += f"- {folder}\n"
        content += f"\nUse @<topic> to access papers in that topic.\n"
    else:
        content += "No topics found.\n"
    return content

@mcp.resource("papers://{topic}")
def get_topic_papers(topic: str) -> str:
    """
    특정 주제(topic)에 대한 논문 정보를 Markdown 형식으로 반환합니다.

    Args:
        topic: 조회할 연구 주제
    """
    topic_dir = topic.lower().replace(" ", "_")
    papers_file = os.path.join(PAPER_DIR, topic_dir, "papers_info.json")

    if not os.path.exists(papers_file):
        return f"# No papers found for topic: {topic}\n\nTry searching for papers on this topic first."

    try:
        with open(papers_file, 'r') as f:
            papers_data = json.load(f)
    except json.JSONDecodeError:
        return f"# Error reading papers data for {topic}\n\nThe papers data file is corrupted."

    content = f"# Papers on {topic.replace('_', ' ').title()}\n\n"
    content += f"Total papers: {len(papers_data)}\n\n"
    for pid, info in papers_data.items():
        content += f"## {info['title']}\n"
        content += f"- **Paper ID**: {pid}\n"
        content += f"- **Authors**: {', '.join(info['authors'])}\n"
        content += f"- **Published**: {info['published']}\n"
        content += f"- **PDF URL**: [{info['pdf_url']}]({info['pdf_url']})\n\n"
        content += f"### Summary\n{info['summary'][:500]}...\n\n"
        content += "---\n\n"
    return content

@mcp.prompt()
def generate_search_prompt(topic: str, num_papers: int = 5) -> str:
    """특정 주제에 대한 학술 논문 검색 및 요약을 위해 Claude에게 전달할 한국어 프롬프트를 생성합니다."""
    return f"""다음 절차에 따라 '{topic}' 주제에 대한 {num_papers}개의 학술 논문을 검색하고 정보를 정리하세요:

1. search_papers(topic='{topic}', max_results={num_papers})를 호출하여 논문 ID 목록을 가져옵니다.
2. 각 논문에 대해 아래 정보를 추출합니다:
   - 제목
   - 저자
   - 출판일
   - 주요 발견 요약
   - 기여 내용 또는 혁신점
   - 사용된 연구 방법론
   - '{topic}' 주제와의 관련성

3. 최종 결과물에는 다음 내용을 포함하세요:
   - '{topic}' 분야의 연구 현황 개요
   - 논문 간 공통 주제 및 트렌드
   - 향후 연구를 위한 주요 연구 공백
   - 이 분야에서 영향력 있는 주요 논문 목록

4. 구조화된 헤딩과 불릿 포인트를 사용하여 가독성 좋게 제시하세요."""

if __name__ == "__main__":
    # 서버 실행 (stdio 방식)
    mcp.run(transport='stdio')
