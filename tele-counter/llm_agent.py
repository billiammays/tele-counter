from langchain_ollama import ChatOllama

class LLM_Agent():

    def __init__(self, model: str='gpt-oss', temp: float=0.1, 
                 mem_size: int=20, p_path: str='p.txt') -> None:
        self.llm = ChatOllama(
            model=model,
            temperature=temp,
            
        )
        with open(p_path, 'r') as file:
            self.mode = file.read()
        self.messages = [
            ('system', self.mode)
        ]
        self.memory_size = mem_size

    def clear(self) -> None:
        self.messages = [
            ('system', self.mode)
        ]

    def add(self, user: str, message: str) -> None:
        self.messages.append(
            (
                'user',
                f'{user}: {message}'
            )
        )
        while len(self.messages) > self.memory_size:
            self.messages.pop(1)

    def invoke(self):
        ai_msg = self.llm.invoke(self.messages)
        self.messages.append(
            ('assistant', ai_msg.content)
        )
        return ai_msg