from enum import Enum


class TaskStatus(str, Enum):
    IN_PROGRESS = "В процессе"
    COMPLETED = "Завершена"