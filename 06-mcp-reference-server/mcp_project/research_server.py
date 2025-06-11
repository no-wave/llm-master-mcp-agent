import arxiv
import json
import os
from typing import List
from mcp.server.fastmcp import FastMCP


PAPER_DIR = "../../papers"

# FastMCP 서버 초기화
mcp = FastMCP("research")

@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    주제를 기반으로 arXiv에서 논문을 검색하고 해당 정보를 저장한다.

    Args:
        topic: 검색할 주제
        max_results: 검색할 최대 결과 수 (기본값: 5)

    Returns:
        검색된 논문의 ID 리스트
    """
    
    # arxiv를 사용하여 논문 검색
    client = arxiv.Client()

    # 입력한 주제와 가장 관련성 높은 논문 검색
    search = arxiv.Search(
        query = topic,
        max_results = max_results,
        sort_by = arxiv.SortCriterion.Relevance
    )

    papers = client.results(search)
    
    # 주제에 해당하는 디렉토리 생성
    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)
    
    file_path = os.path.join(path, "papers_info.json")

    # 기존 논문 정보 불러오기 시도
    try:
        with open(file_path, "r") as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    # 각 논문을 처리하여 papers_info에 추가
    paper_ids = []
    for paper in papers:
        paper_ids.append(paper.get_short_id())
        paper_info = {
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'summary': paper.summary,
            'pdf_url': paper.pdf_url,
            'published': str(paper.published.date())
        }
        papers_info[paper.get_short_id()] = paper_info
    
    # papers_info를 JSON 파일로 저장
    with open(file_path, "w") as json_file:
        json.dump(papers_info, json_file, indent=2)
    
    print(f"결과가 다음 위치에 저장되었습니다: {file_path}")
    
    return paper_ids

@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    모든 주제 디렉토리에서 특정 논문 ID에 대한 정보를 검색한다.

    Args:
        paper_id: 검색할 논문의 ID

    Returns:
        논문 정보를 담은 JSON 문자열 (찾지 못한 경우 오류 메시지 반환)
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
                    print(f"{file_path} 파일 읽기 오류: {str(e)}")
                    continue
    
    return f"{paper_id} 논문에 대한 저장된 정보를 찾을 수 없습니다."

if __name__ == "__main__":
    # 서버 실행 (stdio 방식으로)
    mcp.run(transport='stdio')
