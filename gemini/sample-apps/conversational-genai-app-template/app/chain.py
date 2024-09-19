# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_vertexai import ChatVertexAI

llm = ChatVertexAI(
    model_name="gemini-1.5-flash-001",
    temperature=0,
    max_output_tokens=1024,
)


template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a conversational bot that produce recipes for users based
        on a question.""",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

chain = template | llm
