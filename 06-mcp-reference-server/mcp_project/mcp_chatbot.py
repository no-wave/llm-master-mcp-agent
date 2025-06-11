
from dotenv import load_dotenv
import os
import json
import asyncio
import nest_asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI
from typing import List, Dict, TypedDict
from contextlib import AsyncExitStack

load_dotenv()

# OpenAI API client 초기화
import config
client = OpenAI(api_key=config.API_KEY)

# 도구 정의를 위한 TypedDict
class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict

class MCP_ChatBot:

    def __init__(self):
        # 여러 MCP 세션 관리
        self.sessions: List[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        self.available_tools: List[ToolDefinition] = []
        
        # 도구 이름 ↔ 해당 도구를 제공하는 세션 매핑
        self.tool_to_session: Dict[str, ClientSession] = {}

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """단일 MCP 서버에 연결"""
        try:
            params = StdioServerParameters(**server_config)
            # stdio transport 생성
            read, write = await self.exit_stack.enter_async_context(stdio_client(params))
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self.sessions.append(session)

            # 도구 목록 조회
            response = await session.list_tools()
            print(f"\nConnected to {server_name} with tools:", [t.name for t in response.tools])
            for tool in response.tools:
                # 세션과 도구 매핑
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")

    async def connect_to_servers(self) -> None:
        """설정 파일(server_config.json)에 정의된 모든 서버에 연결"""
        try:
            with open("server_config.json", "r") as f:
                cfg = json.load(f)
            for name, params in cfg.get("mcpServers", {}).items():
                await self.connect_to_server(name, params)
        except Exception as e:
            print(f"Error loading server configuration: {e}")
            raise

    async def process_query(self, query: str) -> None:
        # 사용자 메시지로 대화 시작
        messages = [{"role": "user", "content": query}]
        # OpenAI 함수 스펙으로 도구 정의
        functions = [
            {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}
            for t in self.available_tools
        ]

        while True:
            # OpenAI 함수 호출 자동화
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                functions=functions,
                function_call="auto",
                max_tokens=2024,
                temperature=0.7
            )
            msg = resp.choices[0].message

            # 도구 호출 요청 처리
            if getattr(msg, "function_call", None):
                name = msg.function_call.name
                args = json.loads(msg.function_call.arguments)
                print(f"Calling tool {name} with args {args}")
                session = self.tool_to_session[name]
                result = await session.call_tool(name, arguments=args)
                # 함수 결과를 대화에 추가
                messages.append({"role": "function", "name": name, "content": result.content})
                # 반복하여 후속 응답 처리
                continue

            # 일반 응답 출력 및 종료
            print(msg.content)
            messages.append({"role": "assistant", "content": msg.content})
            break

    async def chat_loop(self) -> None:
        print("\nMCP Chatbot Started! Type queries or 'quit' to exit.")
        while True:
            query = input("Query: ").strip()
            if query.lower() == 'quit':
                break
            await self.process_query(query)
            print()

    async def cleanup(self) -> None:
        """모든 리소스 정리"""
        await self.exit_stack.aclose()

async def main() -> None:
    nest_asyncio.apply()
    chatbot = MCP_ChatBot()
    try:
        await chatbot.connect_to_servers()
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
