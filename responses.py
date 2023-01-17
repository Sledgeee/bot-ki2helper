class UnauthorizedResponse:
    status_code: int
    message: str

    def __init__(self):
        self.status_code = 401
        self.message = "Unauthorized"
