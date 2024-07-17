from langchain_core.output_parsers import BaseOutputParser
from typing import Union, Optional

import json
from langchain_core.outputs import Generation
from backend.model.messages import Message
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.outputs import ChatGeneration
from langchain_core.output_parsers.base import T
class MessageOutputParser(BaseOutputParser):
    def parse(self, text: Union[str, dict]) -> Message:
        if isinstance(text, dict):
            return Message(**text)
        try:
            data = json.loads(text)
            return Message.parse_obj(data)
        except json.JSONDecodeError:
            return Message(type="message", sender="assist", message=text, session_id="unknown")

    def invoke(
        self, input: Union[str, BaseMessage], config: Optional[RunnableConfig] = None
    ) -> T:
        if isinstance(input, BaseMessage):
            return self._call_with_config(
                lambda inner_input: self.parse_result(
                    [ChatGeneration(message=inner_input)]
                ),
                input,
                config,
                run_type="parser",
            )
        else:
            return self._call_with_config(
                lambda inner_input: self.parse_result([Generation(text=json.dumps(inner_input, ensure_ascii=False, indent=4))]),
                input,
                config,
                run_type="parser",
            )

    @property
    def _type(self) -> str:
        return "message_output_parser"