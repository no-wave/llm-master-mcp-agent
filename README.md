# MCP 에이전트 쿡북 with Python
LLM 에이전트 구축을 위한 MCP (Model Context Protocol) 개발 실전 가이드

<img src="https://beat-by-wire.gitbook.io/beat-by-wire/~gitbook/image?url=https%3A%2F%2F3055094660-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Fspaces%252FYzxz4QeW9UTrhrpWwKiQ%252Fuploads%252FvBSvA6ckLevWD5V681KQ%252FLLM%2520Master-MCP%2520%25E1%2584%258B%25E1%2585%25A6%25E1%2584%258B%25E1%2585%25B5%25E1%2584%258C%25E1%2585%25A5%25E1%2586%25AB%25E1%2584%2590%25E1%2585%25B3%2520%25E1%2584%258F%25E1%2585%25AE%25E1%2586%25A8%25E1%2584%2587%25E1%2585%25AE%25E1%2586%25A8.png%3Falt%3Dmedia%26token%3D1ed4ddfe-022e-43a6-9099-5ca4853a7fec&width=300&dpr=4&quality=100&sign=a86fb0ae&sv=2" width="500" height="707"/>

## 책 소개
인공지능 기술이 급속도로 발전하면서, 우리는 AI가 단순한 질문 응답을 넘어 복잡한 업무를 수행하는 시대에 접어들었다. 이러한 변화의 중심에는 대형 언어 모델(LLM)과 이들을 활용한 에이전트 시스템이 있다. 그러나 AI가 진정한 업무 파트너로 자리 잡기 위해서는, 다양한 도구와 데이터 소스와의 원활한 통합이 필수적이다.

기존에는 각 도구나 서비스마다 별도의 API를 통해 AI와 연결해야 했으며, 이는 개발자에게 큰 부담으로 작용했다. 이러한 문제를 해결하기 위해 등장한 것이 바로 MCP(Model Context Protocol)이다. MCP는 애플리케이션이 LLM에 컨텍스트를 제공하는 방법을 표준화한 개방형 프로토콜로, 다양한 데이터 소스와 도구를 AI 모델에 연결하는 표준화된 방법을 제공한다 .

MCP의 구조는 Host, Client, Server로 이루어져 있다. Host는 LLM 애플리케이션 자체로, MCP 통신의 중심이며 여러 개의 Client를 포함하고 이들을 관리한다. Client는 MCP 서버와의 전용 일대일 연결을 유지 관리하며, Server는 MCP를 통해 특정 기능을 노출하고 로컬 또는 원격 데이터 소스에 연결하는 경량 서버이다.
『MCP 에이전트 쿡북』은 인공지능 에이전트와 외부 도구 및 데이터를 통합하여 실용적인 AI 애플리케이션을 구축하고자 하는 개발자, 엔지니어, 제품 관리자, 연구자, 그리고 기술 기획자를 위한 실용서이다.

특히 다음과 같은 독자에게 유용하다:
- AI 에이전트 개발자: LLM 기반 에이전트를 다양한 도구와 연결하여 실제 업무에 적용하고자 하는 개발자
- MCP 서버 구축자: 사내 시스템, 데이터베이스, SaaS 도구 등을 MCP 서버로 연결하여 AI와의 연동을 구현하려는 엔지니어
- AI 제품 기획자 및 PM: MCP 기반 아키텍처를 이해하고, 확장 가능한 AI 서비스의 기획과 설계를 담당하는 제품 관리자
- AI 연구자 및 프로토타이핑 담당자: 다양한 도구와 데이터를 연동하여 새로운 AI 기능을 실험하고자 하는 연구자
- 기존 AI 통합에 어려움을 겪는 개발자: 복잡한 API 통합을 간소화하고, 표준화된 방식으로 AI와 외부 시스템을 연결하고자 하는 개발자

이 책은 MCP의 기본 개념부터 실제 구현까지, 개발자가 MCP를 효과적으로 활용할 수 있도록 안내한다. 이를 통해 AI 에이전트가 다양한 도구와 데이터를 활용하여 더욱 지능적이고 유연하게 작동할 수 있는 기반을 마련하고자 한다. AI와의 협업을 더욱 원활하게 만들기 위한 여정에, 이 책이 든든한 동반자가 되기를 바란다.

## 목 차
저자 소개.


Table of Contents

0장. MCP를 시작하기 전에

1장. LLM 에이전트와 MCP

2장. Claude 데스크탑 MCP 구현

3장. Tool을 활용한 챗봇 구축

4장. MCP Server 만들기

5장. MCP Client 만들기

6장. MCP Chatbot의 Reference Server 접속

7장. Prompt 및 Resource Features 추가

8장. Remote Server에 배포하기

References. 참고 문헌

## E-Book 구매
- Yes24: https://www.yes24.com/product/goods/148121586
- 교보문고: https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000011607683
- 알라딘: https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=365835950

## Github 코드
https://github.com/no-wave/llm-master-mcp-agent
