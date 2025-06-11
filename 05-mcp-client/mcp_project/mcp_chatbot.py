
from dotenv import load_dotenv
import os
import json
import asyncio
import nest_asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI
import config

nest_asyncio.apply()
load_dotenv()

client = OpenAI(api_key=config.API_KEY)

class MCP_ChatBot:

    def __init__(self):
        self.session: ClientSession = None
        self.available_tools: list[dict] = []
        self.available_functions: list[dict] = []

    async def process_query(self, query: str):
        # 사용자 메시지로 대화 시작
        messages = [{"role": "user", "content": query}]

        # MCP 서버에서 받아온 도구 목록을 OpenAI 함수 스펙으로 변환
        self.available_functions = [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            }
            for tool in self.available_tools
        ]

        while True:
            # OpenAI 최신 클라이언트 메서드 사용
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                functions=self.available_functions,
                function_call="auto",
                max_tokens=2024,
                temperature=0.7
            )
            msg = response.choices[0].message

            # 모델이 함수(도구) 호출을 요청하면
            if getattr(msg, "function_call", None):
                func_name = msg.function_call.name
                func_args = json.loads(msg.function_call.arguments)
                print(f"Calling tool {func_name} with args {func_args}")
                # MCP 프로토콜로 도구 실행
                tool_result = await self.session.call_tool(func_name, arguments=func_args)
                # 함수 실행 결과를 대화에 추가
                messages.append({
                    "role": "function",
                    "name": func_name,
                    "content": tool_result.content
                })
                # 결과 반영 후 다시 반복
                continue

            # 일반 텍스트 응답이면 출력 후 종료
            print(msg.content)
            messages.append({"role": "assistant", "content": msg.content})
            break

    async def chat_loop(self):
        print("\nMCP Chatbot Started!\nType your queries or 'quit' to exit.")
        while True:
            query = input("\nQuery: ").strip()
            if query.lower() == 'quit':
                break
            await self.process_query(query)
            print("\n")

    async def connect_to_server_and_run(self):
        # FastMCP 서버를 stdio로 실행
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "research_server.py"],
            env=None,
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                # 세션 초기화 및 도구 리스트 가져오기
                await session.initialize()
                response = await session.list_tools()
                tools = response.tools
                print("\nConnected to server with tools:", [tool.name for tool in tools])
                self.available_tools = [
                    {"name": tool.name, "description": tool.description, "input_schema": tool.inputSchema}
                    for tool in tools
                ]
                await self.chat_loop()

async def main():
    chatbot = MCP_ChatBot()
    await chatbot.connect_to_server_and_run()

if __name__ == "__main__":
    asyncio.run(main())
