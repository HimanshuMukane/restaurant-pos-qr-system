class Error(Exception):
    pass

class DatabaseError(Error):
    pass

class IntegrityError(DatabaseError):
    pass

class UniqueViolation(IntegrityError):
    pass

class NotNullViolation(IntegrityError):
    pass
