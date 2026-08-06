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
    __external__ = True

    class Index:
        name = get_settings().logging.index

    message = Text()
    request_id = Keyword()
    stream = Keyword()
    log = Object(Log)
    error = Object(Error)
    service = Object(Named)
    container = Object(Named)

