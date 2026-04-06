from __future__ import annotations


class MicroSQLException(Exception):
    def __init__(self, message: str, line_number: int = 1) -> None:
        super().__init__(message)
        self.message = message
        self.line_number = line_number

    @property
    def error_type(self) -> str:
        return self.__class__.__name__


class ParserException(MicroSQLException):
    pass


class ValidationException(MicroSQLException):
    pass


class TypeConflictException(ValidationException):
    pass


class FileSystemException(MicroSQLException):
    pass
