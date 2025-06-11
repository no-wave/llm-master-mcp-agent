
import arxiv
import json
import os
from typing import List
from mcp.server.fastmcp import FastMCP

PAPER_DIR = "papers"

# FastMCP 서버 초기화
mcp = FastMCP("research", port=8001)

@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    주제에 따라 arXiv에서 논문을 검색하고 그 정보를 저장한다.
    
    인자:
        topic: 검색할 주제
        max_results: 검색할 최대 결과 수 (기본값: 5)
        
    반환:
        검색에서 찾은 논문 ID 목록
    """
    
    # arxiv를 사용하여 논문 찾기
    client = arxiv.Client()

    # 검색된 주제와 일치하는 가장 관련성 높은 논문 검색
    search = arxiv.Search(
        query = topic,
        max_results = max_results,
        sort_by = arxiv.SortCriterion.Relevance
    )

    papers = client.results(search)
    
    # 이 주제에 대한 디렉토리 생성
    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)
    
    file_path = os.path.join(path, "papers_info.json")

    # 기존 논문 정보 로드 시도
    try:
        with open(file_path, "r") as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    # 각 논문을 처리하고 papers_info에 추가
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
    
    # 업데이트된 papers_info를 json 파일에 저장
    with open(file_path, "w") as json_file:
        json.dump(papers_info, json_file, indent=2)
    
    print(f"결과가 다음 위치에 저장됨: {file_path}")
    
    return paper_ids

@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    모든 주제 디렉토리에서 특정 논문에 대한 정보를 검색한다.
    
    인자:
        paper_id: 검색할 논문의 ID
        
    반환:
        논문이 발견되면 JSON 문자열로 된 논문 정보, 발견되지 않으면 오류 메시지
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
                    print(f"{file_path} 읽기 오류: {str(e)}")
                    continue
    
    return f"논문 {paper_id}와 관련된 저장된 정보가 없다."



@mcp.resource("papers://folders")
def get_available_folders() -> str:
    """
    papers 디렉토리에서 사용 가능한 모든 주제 폴더를 나열한다.
    
    이 리소스는 사용 가능한 모든 주제 폴더의 간단한 목록을 제공한다.
    """
    folders = []
    
    # 모든 주제 디렉토리 가져오기
    if os.path.exists(PAPER_DIR):
        for topic_dir in os.listdir(PAPER_DIR):
            topic_path = os.path.join(PAPER_DIR, topic_dir)
            if os.path.isdir(topic_path):
                papers_file = os.path.join(topic_path, "papers_info.json")
                if os.path.exists(papers_file):
                    folders.append(topic_dir)
    
    # 간단한 마크다운 목록 생성
    content = "# 사용 가능한 주제\n\n"
    if folders:
        for folder in folders:
            content += f"- {folder}\n"
        content += f"\n해당 주제의 논문에 접근하려면 @{folder}를 사용하세요.\n"
    else:
        content += "주제를 찾을 수 없다.\n"
    
    return content

@mcp.resource("papers://{topic}")
def get_topic_papers(topic: str) -> str:
    """
    특정 주제에 대한 논문의 상세 정보를 가져온다.
    
    인자:
        topic: 논문을 검색할 연구 주제
    """
    topic_dir = topic.lower().replace(" ", "_")
    papers_file = os.path.join(PAPER_DIR, topic_dir, "papers_info.json")
    
    if not os.path.exists(papers_file):
        return f"# 주제에 대한 논문을 찾을 수 없음: {topic}\n\n먼저 이 주제에 대한 논문을 검색해 보세요."
    
    try:
        with open(papers_file, 'r') as f:
            papers_data = json.load(f)
        
        # 논문 세부 정보가 포함된 마크다운 내용 생성
        content = f"# {topic.replace('_', ' ').title()} 주제의 논문\n\n"
        content += f"총 논문 수: {len(papers_data)}\n\n"
        
        for paper_id, paper_info in papers_data.items():
            content += f"## {paper_info['title']}\n"
            content += f"- **논문 ID**: {paper_id}\n"
            content += f"- **저자**: {', '.join(paper_info['authors'])}\n"
            content += f"- **발행일**: {paper_info['published']}\n"
            content += f"- **PDF URL**: [{paper_info['pdf_url']}]({paper_info['pdf_url']})\n\n"
            content += f"### 요약\n{paper_info['summary'][:500]}...\n\n"
            content += "---\n\n"
        
        return content
    except json.JSONDecodeError:
        return f"# {topic}에 대한 논문 데이터 읽기 오류\n\n논문 데이터 파일이 손상되었다."

@mcp.prompt()
def generate_search_prompt(topic: str, num_papers: int = 5) -> str:
    """특정 주제에 대한 학술 논문을 찾고 논의하기 위한 Claude용 프롬프트를 생성한다."""
    return f"""search_papers 도구를 사용하여 '{topic}'에 관한 {num_papers}개의 학술 논문을 검색하세요.

    다음 지침을 따르세요:
    1. 먼저, search_papers(topic='{topic}', max_results={num_papers})를 사용하여 논문을 검색하세요
    2. 찾은 각 논문에 대해 다음 정보를 추출하고 정리하세요:
       - 논문 제목
       - 저자
       - 출판일
       - 주요 발견에 대한 간략한 요약
       - 주요 기여 또는 혁신
       - 사용된 방법론
       - '{topic}' 주제와의 관련성
    
    3. 다음을 포함하는 종합적인 요약을 제공하세요:
       - '{topic}'의 현재 연구 상태 개요
       - 논문 전반에 걸친 공통 주제 및 동향
       - 주요 연구 격차 또는 향후 조사 영역
       - 이 분야에서 가장 영향력 있는 논문
    
    4. 읽기 쉽도록 제목과 글머리 기호가 있는 명확하고 구조화된 형식으로 결과를 정리하세요.
    
    각 논문에 대한 자세한 정보와 {topic}의 연구 현황에 대한 고수준 종합을 모두 제시해 주세요."""

if __name__ == "__main__":
    # 서버 초기화 및 실행
    mcp.run(transport='sse')
