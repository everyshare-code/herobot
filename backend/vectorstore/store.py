from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from typing import List, Dict


class VectorStore:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  # 초기화 여부 확인
            self.embeddings = OpenAIEmbeddings()
            self.vector_stores: Dict[str, FAISS] = {}
            self.initialized = True  # 초기화 상태 표시

    def create_vectorstore_from_embed_text(self, texts: List[str], session_id: str):
        self.vector_stores[session_id] = FAISS.from_texts(texts, embedding=self.embeddings)

    def initialize_vector_store(self, session_id: str, messages: str):
        combined_messages = []
        current_message = ""
        for line in messages.split('\n'):
            if line.startswith("AI: ") or line.startswith("HUMAN: "):
                if current_message:
                    combined_messages.append(current_message)
                    current_message = line.split(": ", 1)[1].strip()
                else:
                    current_message = line.split(": ", 1)[1].strip()
            else:
                current_message += " " + line.strip()
        if current_message:
            combined_messages.append(current_message)

        print(f"All messages for session {session_id}: {combined_messages}")
        if combined_messages:
            self.create_vectorstore_from_embed_text(combined_messages, session_id)
        else:
            self.create_vectorstore_from_embed_text([], session_id)

    def add_texts(self, session_id: str, texts: List[str]):
        if session_id not in self.vector_stores:
            self.initialize_vector_store(session_id, '\n'.join(texts))
        else:
            self.vector_stores[session_id].add_texts(texts)

    def semantic_search(self, session_id: str, query: str, k: int = 5, score_threshold: float = 0.7) -> List[str]:
        if session_id not in self.vector_stores:
            print(f"No vector store found for session {session_id}")
            return []
        retriever = self.vector_stores[session_id].as_retriever(
            search_type='similarity_score_threshold',
            search_kwargs={"score_threshold": score_threshold}
        )
        relevanced_doc = retriever.invoke(query)
        print(relevanced_doc)
        filtered_results = [document.page_content for document in relevanced_doc if len(document.page_content) > 50]
        print(f"Filtered results for query '{query}' in session {session_id}: {filtered_results}")

        return filtered_results[:k]


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    store = VectorStore()
    messages = """
        AI: 여행 관련 질문을 할 수 있습니다. 무엇을 도와드릴까요?
        HUMAN: 항공권 검색
        AI: 항공권 검색을 위해 출발일, 출발지, 도착지를 입력해주세요.
        HUMAN: 9월11일 서울에서 대만
        AI: 최저가 항공편\n금액: 136,700원\n경유: 직항\n출발: 인천 국제공항(ICN)에서 2024-08-24 09:05:00\n도착: 타이완 타오유완 국제공항  (TPE)에 2024-08-24 10:50:00\n마케팅 항공사: Jeju Air\n[예약 링크](https://www.skyscanner.co.kr/transport/flights/icn/tpe/20240824/?adults=1&adultsv2=1&cabinclass=economy&children=0&childrenv2=&inboundaltsenabled=false&infants=0&originentityid=27539733&outboundaltsenabled=false&preferdirects=false&ref=home&rtn=0)\n\n최단거리 항공편\n금액: 244,635원\n경유: 직항\n출발: 인천 국제공항(ICN)에서 2024-08-24 10:00:00\n도착: 타이완 타오유완 국제공항  (TPE)에 2024-08-24 11:30:00\n마케팅 항공사: Asiana Airlines\n[예약 링크](https://www.skyscanner.co.kr/transport/flights/icn/tpe/20240824/?adults=1&adultsv2=1&cabinclass=economy&children=0&childrenv2=&inboundaltsenabled=false&infants=0&originentityid=27539733&outboundaltsenabled=false&preferdirects=false&ref=home&rtn=0)\n\n
    """
    store.initialize_vector_store('12345', messages)
    results = store.semantic_search('12345', '이전 대만 항공권 내역에 대해서 찾아줘')
    print(results)
