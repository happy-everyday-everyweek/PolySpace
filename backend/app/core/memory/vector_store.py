

class VectorStore:
    def __init__(self, collection_name: str = "polyspace_memory"):
        self._collection_name = collection_name
        self._client = None
        self._collection = None

    async def initialize(self) -> None:
        try:
            import chromadb

            self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(self._collection_name)
        except ImportError:
            pass

    async def add(self, texts: list[str], metadatas: list[dict], ids: list[str]) -> None:
        if self._collection:
            self._collection.add(documents=texts, metadatas=metadatas, ids=ids)

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not self._collection:
            return []
        results = self._collection.query(query_texts=[query], n_results=top_k)
        items = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                items.append(
                    {
                        "id": results["ids"][0][i] if results.get("ids") else "",
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 0,
                    }
                )
        return items

    async def delete(self, ids: list[str]) -> None:
        if self._collection:
            self._collection.delete(ids=ids)
