from elasticsearch.dsl import (
    AsyncDocument,
    InnerDoc,
    Integer,
    Keyword,
    Object,
    Text,
)

from src.core.config import get_settings


class OriginFile(InnerDoc):
    name = Keyword()
    line = Integer()


class Origin(InnerDoc):
    function = Keyword()
    file = Object(OriginFile)


class Log(InnerDoc):
    level = Keyword()
    logger = Keyword()
    origin = Object(Origin)


class Error(InnerDoc):
    type = Keyword()
    message = Text()
    stack_trace = Text()


class Named(InnerDoc):
    name = Keyword()


class LogDocument(AsyncDocument):
    """
    Desc: The line Filebeat ships, declared so a query can be built against
        named fields instead of raw dictionaries.
    """

    # Filebeat owns this mapping through its own index template, and the
    # stream is a data stream rather than a plain index. If the app created
    # it first, Filebeat could no longer roll it over, so boot_es_indices
    # skips any document carrying this flag.
    __external__ = True

    class Index:
        name = get_settings().logging.index

    # @timestamp cannot be a Python name, so it is not declared here; the
    # mapping already types it and a query sorts on the string.
    message = Text()
    request_id = Keyword()
    stream = Keyword()
    log = Object(Log)
    error = Object(Error)
    service = Object(Named)
    container = Object(Named)
