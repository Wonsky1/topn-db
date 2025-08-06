# OLX Database FastAPI Service

A FastAPI service for managing OLX monitoring tasks and item records, converted from the original Python module.

## Features

- **Monitoring Tasks Management**: Create, read, update, and delete monitoring tasks for different chat IDs
- **Item Records Management**: Store and retrieve scraped OLX item data
- **Pending Tasks**: Get tasks ready for processing based on frequency settings
- **Items to Send**: Retrieve items that should be sent for specific monitoring tasks
- **Cleanup Operations**: Delete old items to manage database size
- **Warsaw Timezone Support**: Proper timezone handling for Polish market

## Project Structure

```
topn-db/
├── app.py                 # FastAPI application entry point
├── core/
│   ├── config.py         # Configuration management
│   └── database.py       # Database models and connection
├── api/
│   ├── routers/          # API route definitions
│   │   ├── tasks.py      # Monitoring tasks endpoints
│   │   └── items.py      # Item records endpoints
│   └── services/         # Business logic layer
│       ├── task_service.py
│       └── item_service.py
├── schemas/              # Pydantic models for request/response
│   ├── tasks.py
│   └── items.py
├── requirements.txt      # Python dependencies
└── .env.example         # Environment variables template
```

## Installation

1. Clone the repository and navigate to the project directory:
```bash
cd /Users/vlad/PycharmProjects/topn-db
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env file with your database URL and other settings
```

5. Initialize the database:
```bash
# The database tables will be created automatically when the app starts
```

## Configuration

The service uses environment variables with the `OLX_` prefix:

- `OLX_DATABASE_URL`: PostgreSQL database connection URL
- `OLX_DEFAULT_SENDING_FREQUENCY_MINUTES`: Default frequency for task processing (default: 60)
- `OLX_DEFAULT_LAST_MINUTES_GETTING`: Default time window for new items (default: 30)
- `OLX_DEBUG`: Enable debug mode (default: false)
- `OLX_HOST`: Server host (default: 0.0.0.0)
- `OLX_PORT`: Server port (default: 8000)

## Running the Service

### Development Mode
```bash
python app.py
```

### Production Mode with Uvicorn
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- Main API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc

## API Endpoints

### Monitoring Tasks
- `GET /api/v1/tasks/` - Get all monitoring tasks
- `GET /api/v1/tasks/chat/{chat_id}` - Get tasks by chat ID
- `GET /api/v1/tasks/{task_id}` - Get task by ID
- `POST /api/v1/tasks/` - Create new monitoring task
- `PUT /api/v1/tasks/{task_id}` - Update monitoring task
- `DELETE /api/v1/tasks/{task_id}` - Delete task by ID
- `DELETE /api/v1/tasks/chat/{chat_id}` - Delete tasks by chat ID
- `GET /api/v1/tasks/pending` - Get pending tasks
- `POST /api/v1/tasks/{task_id}/update-last-got-item` - Update last got item timestamp
- `GET /api/v1/tasks/{task_id}/items-to-send` - Get items to send for task

### Item Records
- `GET /api/v1/items/` - Get all items (paginated)
- `GET /api/v1/items/by-source` - Get items by source URL
- `GET /api/v1/items/recent` - Get recent items
- `GET /api/v1/items/{item_id}` - Get item by ID
- `GET /api/v1/items/by-url/{item_url}` - Get item by URL
- `POST /api/v1/items/` - Create new item record
- `DELETE /api/v1/items/{item_id}` - Delete item by ID
- `DELETE /api/v1/items/cleanup/older-than/{days}` - Delete old items

## Database Models

### MonitoringTask
- `id`: Primary key
- `chat_id`: Chat identifier
- `name`: Task name (max 64 chars)
- `url`: URL to monitor
- `last_updated`: Last update timestamp
- `last_got_item`: Last item retrieval timestamp

### ItemRecord
- `id`: Primary key
- `item_url`: Unique item URL
- `source_url`: Source monitoring URL
- `title`: Item title
- `price`: Item price
- `location`: Item location
- `created_at`: Creation date from source
- `created_at_pretty`: Formatted creation date
- `image_url`: Item image URL
- `description`: Item description
- `first_seen`: When item was first scraped

## Migration from Original Module

This FastAPI service maintains compatibility with the original `olx_db` Python module:

- Same database schema and models
- Same business logic and timezone handling
- Same configuration using `OLX_` prefixed environment variables
- All original functions are now available as REST API endpoints

## Development

### Adding New Endpoints
1. Add new schemas in `schemas/`
2. Add business logic in `api/services/`
3. Add routes in `api/routers/`
4. Register router in `app.py`

### Testing
Use the interactive API documentation at `/docs` to test endpoints, or use curl/Postman with the API endpoints.

## License

[Add your license information here]
