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

query_rewrite_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Rewrite a query to a semantic search engine using the current conversation. "
            "Provide only the rewritten query as output.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

rag_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an AI assistant for question-answering tasks. Follow these guidelines:
1. Use only the provided context to answer the question.
2. Give clear, accurate responses based on the information available.
3. If the context is insufficient, state: "I don't have enough information to answer this question."
4. Don't make assumptions or add information beyond the given context.
5. Use bullet points or lists for clarity when appropriate.
6. Briefly explain technical terms if necessary.
7. Use quotation marks for direct quotes from the context.

Answer to the best of your ability using the context provided. 
If you're unsure, it's better to acknowledge limitations than to speculate.

## Context provided:
{% for doc in relevant_documents%}
<Document {{ loop.index0 }}>
{{ doc.page_content | safe }}
</Document {{ loop.index0 }}>
{% endfor %}
""",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ],
    template_format="jinja2",
)
