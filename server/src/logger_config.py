import logging
import sys

def setup_logging(level: str = 'INFO') -> logging.Logger:
    logging.basicConfig(
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    )
    return logging.getLogger('app')

logger = setup_logging()
