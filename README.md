# OKGBI Auto Project

This repository contains a web application for automated calculation and optimization of production schedules for concrete plates.

## Project Overview

The project consists of several components:

1. **Web Application (Django)**: A web interface for managing calculations and viewing results
2. **Frontend Application (React)**: A modern user interface built with React
3. **API Service (FastAPI)**: Provides endpoints for calculation and optimization of production schedules
4. **Database (PostgreSQL)**: Stores application data
5. **Nginx**: Serves as a reverse proxy and serves static files

## Prerequisites

Before deploying the project, ensure you have the following installed:

- Docker and Docker Compose (version 3.9 or higher)
- Git (for cloning the repository)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd okgbiAuto
```

### 2. Configure Environment Variables

Create a `.env` file in the project root or copy from the example:

```bash
cp .env.example .env
```

Edit the `.env` file to set the following variables:

```
DB_USER=okgbi
DB_NAME=okgbi
DB_PASSWORD=your_secure_password
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=your_secure_admin_password
```

### 3. Deploy with Docker Compose

Build and start all services:

```bash
docker-compose up -d
```

This will:
- Build and start the web application
- Build and start the API service
- Start the PostgreSQL database
- Configure Nginx as a reverse proxy
- Create a Django superuser automatically
- Apply database migrations
- Collect static files

## Accessing the Application

After deployment, you can access:

- **Web Application**: http://localhost:8000
- **Frontend Application**: http://localhost:3000 (in development mode) or http://localhost (in production mode)
- **API Service**: http://localhost:8080
- **Django Admin Panel**: http://localhost:8000/admin (login with the superuser credentials defined in `.env`)

## API Endpoints

The API service provides the following endpoints:

1. **POST /api/v1/calculate/**: Calculate a calendar plan with constraints
2. **POST /api/v1/calculate/no-limits**: Optimize a calendar plan without constraints

For detailed API documentation and request/response formats, see the [API README](api/README.md).

## Maintenance

### Viewing Logs

```bash
# View logs for all services
docker-compose logs

# View logs for a specific service
docker-compose logs web
docker-compose logs api
docker-compose logs db
```

### Stopping the Services

```bash
docker-compose down
```

### Restarting Services

```bash
docker-compose restart
```

### Rebuilding Services After Code Changes

```bash
docker-compose up -d --build
```

## Troubleshooting

If you encounter issues:

1. Check the logs for error messages: `docker-compose logs`
2. Ensure all environment variables are correctly set in the `.env` file
3. Verify that all required ports (8000, 8080) are available on your system
4. Make sure Docker and Docker Compose are up to date

## Development

For development purposes, the project is configured with volume mounts that reflect code changes without rebuilding containers:

- Web application code is mounted at `/code` in the web container
- API code is mounted at `/app` in the api container
- Frontend code is mounted at `/app` in the frontend container

This allows for real-time code changes during development.

### Running in Development Mode

To run the application in development mode:

```bash
docker-compose -f docker-compose.dev.yml up -d
```

This will start all services in development mode, with hot reloading enabled for the frontend application.

## Production

For production deployment, the project includes optimized configurations:

### Running in Production Mode

To run the application in production mode:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

This will:
- Build an optimized production version of the frontend application
- Serve the frontend application using Nginx
- Configure the API service for production use
- Set up proper reverse proxying for all services

### Production vs Development

The main differences between production and development modes:

1. **Frontend**: In production, the React app is built into static files and served by Nginx. In development, it runs with hot reloading enabled.
2. **Performance**: Production mode is optimized for performance and security.
3. **Ports**: Production mode exposes only port 80 for the frontend, while development mode exposes additional ports for direct access to services.
4. **Debugging**: Development mode includes additional debugging information and tools.
