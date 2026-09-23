from sqlalchemy.orm import Session
from src.security.models.allowed_file_type import AllowedFileType

DEFAULT_FILE_TYPES = [
    (".txt", "text/plain"),
    (".pdf", "application/pdf"),
    (".png", "image/png"),
    (".jpg", "image/jpeg"),
    (".jpeg", "image/jpeg"),
    (".gif", "image/gif"),
    (".bmp", "image/bmp"),
    (".webp", "image/webp"),
    (".doc", "application/msword"),
    (
        ".docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ),
    (".xls", "application/vnd.ms-excel"),
    (".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    (".ppt", "application/vnd.ms-powerpoint"),
    (
        ".pptx",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ),
    (".csv", "text/csv"),
    (".zip", "application/zip"),
    (".rar", "application/x-rar-compressed"),
    (".7z", "application/x-7z-compressed"),
    (".mp4", "video/mp4"),
    (".mp3", "audio/mpeg"),
    (".wav", "audio/wav"),
    (".json", "application/json"),
    (".xml", "application/xml"),
]


def seed_allowed_file_types(db: Session):

    for extension, mime_type in DEFAULT_FILE_TYPES:

        exists = (
            db.query(AllowedFileType)
            .filter(AllowedFileType.extension == extension)
            .first()
        )

        if not exists:

            db.add(
                AllowedFileType(
                    extension=extension,
                    mime_type=mime_type,
                    description=f"{extension} files",
                )
            )

    db.commit()
