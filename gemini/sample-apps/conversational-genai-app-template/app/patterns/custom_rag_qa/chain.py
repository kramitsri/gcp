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

# mypy: disable-error-code="arg-type"
import logging
from typing import Any, Dict, Iterator

import google
import vertexai
from langchain_google_community.vertex_rank import VertexAIRank
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings

from app.patterns.custom_rag_qa.templates import query_rewrite_template, rag_template
from app.patterns.custom_rag_qa.vector_store import get_vector_store
from app.utils.output_types import OnChatModelStreamEvent, OnToolEndEvent, custom_chain

# Configuration
EMBEDDING_MODEL = "text-embedding-004"
LLM_MODEL = "gemini-1.5-flash-001"
TOP_K = 5

# Initialize logging
logging.basicConfig(level=logging.INFO)

credentials, project_id = google.auth.default()
vertexai.init(project=project_id)
embedding = VertexAIEmbeddings(model_name=EMBEDDING_MODEL)
vector_store = get_vector_store(embedding=embedding)
retriever = vector_store.as_retriever(search_kwargs={"k": 20})
compressor = VertexAIRank(
    project_id=project_id,
    location_id="global",
    ranking_config="default_ranking_config",
    title_field="id",
    top_n=TOP_K,
)
llm = ChatVertexAI(model=LLM_MODEL, temperature=0, max_tokens=1024)

query_gen = query_rewrite_template | llm
response_chain = rag_template | llm


@custom_chain
def chain(
    input: Dict[str, Any], **kwargs: Any
) -> Iterator[OnToolEndEvent | OnChatModelStreamEvent]:
    """
    Implements a RAG QA chain. Decorated with `custom_chain` to offer LangChain compatible astream_events
    and invoke interface and OpenTelemetry tracing.
    """
    # Generate optimized query
    query = query_gen.invoke(input).content

    # Retrieve and rank documents
    retrieved_docs = retriever.invoke(query)
    ranked_docs = compressor.compress_documents(documents=retrieved_docs, query=query)

    # Yield tool results metadata
    yield OnToolEndEvent(data={"input": {"query": query}, "output": ranked_docs})

    # Stream LLM response
    for chunk in response_chain.stream(
        input={"messages": input["messages"], "relevant_documents": ranked_docs}
    ):
        yield OnChatModelStreamEvent(data={"chunk": chunk})
