# uncomment the corresponding imports below to avoid NameError:
# from .i_generator_reader import IgeneratorReader
# from .i_retriever import IRetriever
# from .i_cross_encoder_reranker import ICrossEncoderReranker
# from .i_graph_exporter import IGraphExporter


class SearchResult:
    def __init__(
        self,
        artifact_id: str,
        artifact_type: str,
        score: float,
        content: str,
        tenant_id: str = "tenant_default",
    ):
        self.artifact_id = artifact_id
        self.artifact_type = artifact_type
        self.score = score
        self.content = content
        self.tenant_id = tenant_id
