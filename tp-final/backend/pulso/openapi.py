"""Print the OpenAPI schema (used by the frontend's `npm run gen:api`). Needs no database."""

import json

from .config import Settings
from .main import create_app

if __name__ == '__main__':
    app = create_app(Settings())
    print(json.dumps(app.openapi(), indent=2, ensure_ascii=False))
