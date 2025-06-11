import os
import json
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from typing import List, Dict, TypedDict
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

# 환경 변수 로드
load_dotenv()

# OpenAI API 클라이언트 초기화
import config
client = OpenAI(api_key=config.API_KEY)

# 도구 정의를 위한 TypedDict
class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict

class MCP_ChatBot:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.available_tools: List[ToolDefinition] = []
        self.available_prompts: List[Dict] = []
        self.sessions: Dict[str, ClientSession] = {}

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """단일 MCP 서버에 연결하고 도구/프롬프트/리소스를 로드"""
        try:
            params = StdioServerParameters(**server_config)
            read, write = await self.exit_stack.enter_async_context(stdio_client(params))
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            # 도구 목록 조회
            tools_resp = await session.list_tools()
            for tool in tools_resp.tools:
                self.sessions[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })

            # 프롬프트 목록 조회
            prompts_resp = await session.list_prompts()
            if prompts_resp and prompts_resp.prompts:
                for prompt in prompts_resp.prompts:
                    self.sessions[prompt.name] = session
                    self.available_prompts.append({
                        "name": prompt.name,
                        "description": prompt.description,
                        "arguments": prompt.arguments
                    })

            # 리소스 목록 조회
            resources_resp = await session.list_resources()
            if resources_resp and resources_resp.resources:
                for resource in resources_resp.resources:
                    uri = str(resource.uri)
                    self.sessions[uri] = session
        except Exception as e:
            print(f"Error connecting to {server_name}: {e}")

    async def connect_to_servers(self) -> None:
        """설정 파일로부터 모든 MCP 서버에 연결"""
        try:
            with open("server_config.json", "r") as f:
                cfg = json.load(f)
            for name, params in cfg.get("mcpServers", {}).items():
                await self.connect_to_server(name, params)
        except Exception as e:
            print(f"Error loading config: {e}")
            raise

    async def process_query(self, query: str) -> None:
        """사용자 쿼리를 OpenAI로 전송, 도구 호출 및 응답 처리"""
        messages = [{"role": "user", "content": query}]
        functions = [
            {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}
            for t in self.available_tools
        ]

        while True:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                functions=functions,
                function_call="auto",
                max_tokens=2024,
                temperature=0.7
            )
            msg = resp.choices[0].message

            # 함수 호출 요청 처리
            if getattr(msg, "function_call", None):
                name = msg.function_call.name
                args = json.loads(msg.function_call.arguments)
                print(f"Calling tool {name} with args {args}")
                session = self.sessions.get(name)
                if not session:
                    print(f"Tool '{name}' not found.")
                    break
                result = await session.call_tool(name, arguments=args)
                messages.append({"role": "function", "name": name, "content": result.content})
                continue

            # 일반 응답 출력 후 종료
            print(msg.content)
            messages.append({"role": "assistant", "content": msg.content})
            break

    async def get_resource(self, uri: str) -> None:
        """리소스 URI를 통해 MCP 세션에서 콘텐츠 가져오기"""
        session = self.sessions.get(uri)
        if not session and uri.startswith("papers://"):
            for k, s in self.sessions.items():
                if k.startswith("papers://"):
                    session = s
                    uri = k
                    break
        if not session:
            print(f"Resource '{uri}' not found.")
            return
        try:
            result = await session.read_resource(uri=uri)
            if result and result.contents:
                print(f"\nResource: {uri}\n{result.contents[0].text}")
            else:
                print("No content available.")
        except Exception as e:
            print(f"Error: {e}")

    async def list_prompts(self) -> None:
        """사용 가능한 프롬프트 목록 출력"""
        if not self.available_prompts:
            print("No prompts available.")
            return
        print("\nAvailable prompts:")
        for p in self.available_prompts:
            print(f"- {p['name']}: {p['description']}")
            if p['arguments']:
                print("  Arguments:")
                for arg in p['arguments']:
                    # PromptArgument 객체에는 .name 속성만 사용
                    name = getattr(arg, 'name', '')
                    print(f"    - {name}")

    async def execute_prompt(self, prompt_name: str, args: Dict) -> None:
        """지정된 프롬프트 실행 후 결과로 쿼리 처리"""
        session = self.sessions.get(prompt_name)
        if not session:
            print(f"Prompt '{prompt_name}' not found.")
            return
        try:
            result = await session.get_prompt(prompt_name, arguments=args)
            if result and result.messages:
                content = result.messages[0].content
                if isinstance(content, str):
                    text = content
                elif hasattr(content, 'text'):
                    text = content.text
                else:
                    text = " ".join([
                        item.text if hasattr(item, 'text') else str(item)
                        for item in content
                    ])
                print(f"\nExecuting prompt '{prompt_name}'...")
                await self.process_query(text)
        except Exception as e:
            print(f"Error: {e}")

    async def chat_loop(self) -> None:
        """사용자 상호작용 메인 루프"""
        print("\nMCP Chatbot Started!")
        print("Type queries, 'quit', '@folders', '@<topic>', '/prompts', '/prompt <name> <arg=value>'")
        while True:
            q = input("\nQuery: ").strip()
            if not q:
                continue
            if q.lower() == 'quit':
                break
            if q.startswith("@"):
                topic = q[1:]
                uri = "papers://folders" if topic == "folders" else f"papers://{topic}"
                await self.get_resource(uri)
                continue
            if q.startswith("/"):
                parts = q.split()
                cmd = parts[0].lower()
                if cmd == '/prompts':
                    await self.list_prompts()
                elif cmd == '/prompt':
                    if len(parts) < 2:
                        print("Usage: /prompt <name> <arg=value> ...")
                        continue
                    pname = parts[1]
                    args = {}
                    for arg in parts[2:]:
                        if '=' in arg:
                            key, val = arg.split('=', 1)
                            args[key] = val
                    await self.execute_prompt(pname, args)
                else:
                    print(f"Unknown command: {cmd}")
                continue
            await self.process_query(q)

    async def cleanup(self) -> None:
        """리소스 정리"""
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
