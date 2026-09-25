"""Print the OpenAPI schema (used by the frontend's `npm run gen:api`). Needs no database."""

import json
import sys

from .config import Settings
from .main import create_app

if __name__ == '__main__':
    # Keep redirected output identical on Windows and Linux, including accented text.
    sys.stdout.reconfigure(encoding='utf-8', newline='\n')
    app = create_app(Settings())
    print(json.dumps(app.openapi(), indent=2, ensure_ascii=False))
