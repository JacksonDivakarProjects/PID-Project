# PID Project - Full Stack Application

This project consists of a FastAPI backend and a React frontend, both containerized with Docker for easy deployment and development.

## Project Structure

```
PID-Project/
├── README.md
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── ... (other backend files)
└── Frontend/
    ├── Dockerfile
    ├── package.json
    ├── package-lock.json
    └── ... (other frontend files)
```

## Prerequisites

- Docker installed on your machine
- Docker Compose installed on your machine

## Quick Start (Recommended)

### Running Both Services with Docker Compose

1. **Clone the repository and navigate to the project directory:**
   ```bash
   cd PID-Project
   ```

2. **Start both services:**
   ```bash
   docker-compose up --build
   ```

3. **Access the applications:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Backend API Documentation: http://localhost:8000/docs

4. **Stop the services:**
   ```bash
   docker-compose down
   ```

## Running Services Separately

### Backend Only

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Build the backend image:**
   ```bash
   docker build -t pid-backend .
   ```

3. **Run the backend container:**
   ```bash
   docker run -d \
     --name fastapi-backend \
     -p 8000:8000 \
     -v $(pwd):/app \
     pid-backend
   ```

4. **Access the backend:**
   - API: http://localhost:8000
   - Interactive API docs: http://localhost:8000/docs

5. **View logs:**
   ```bash
   docker logs fastapi-backend
   ```

6. **Stop and remove the container:**
   ```bash
   docker stop fastapi-backend
   docker rm fastapi-backend
   ```

### Frontend Only

1. **Navigate to the Frontend directory:**
   ```bash
   cd Frontend
   ```

2. **Build the frontend image:**
   ```bash
   docker build -t pid-frontend .
   ```

3. **Run the frontend container:**
   ```bash
   docker run -d \
     --name react-frontend \
     -p 3000:3000 \
     -v $(pwd):/app \
     -v /app/node_modules \
     -e CHOKIDAR_USEPOLLING=true \
     pid-frontend
   ```

4. **Access the frontend:**
   - Application: http://localhost:3000

5. **View logs:**
   ```bash
   docker logs react-frontend
   ```

6. **Stop and remove the container:**
   ```bash
   docker stop react-frontend
   docker rm react-frontend
   ```

## Development Mode

### With Docker Compose (Recommended)

The docker-compose setup includes volume mounts for hot reloading during development:

```bash
# Start in development mode with live reload
docker-compose up --build

# View logs for specific service
docker-compose logs backend
docker-compose logs frontend

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
```

### Without Docker (Local Development)

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd Frontend
npm install
npm run dev
```

## Environment Variables

### Backend
- `PYTHONPATH=/app` - Set Python path for module imports

### Frontend
- `CHOKIDAR_USEPOLLING=true` - Enable polling for file changes in Docker
- `REACT_APP_API_URL=http://localhost:8000` - Backend API URL

## Useful Docker Commands

### General
```bash
# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# View images
docker images

# Clean up unused Docker resources
docker system prune -f

# Clean up volumes too (be careful!)
docker system prune --volumes -f
```

### Docker Compose Specific
```bash
# Start services in detached mode
docker-compose up -d

# Build services without starting
docker-compose build

# View logs
docker-compose logs -f

# Execute command in running container
docker-compose exec backend bash
docker-compose exec frontend sh

# Scale services (if needed)
docker-compose up --scale frontend=2
```

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Check what's using the port
   lsof -i :8000
   lsof -i :3000
   
   # Kill the process or change ports in docker-compose.yml
   ```

2. **Permission issues with volumes:**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

3. **Container keeps restarting:**
   ```bash
   # Check logs for errors
   docker-compose logs [service-name]
   ```

4. **OpenCV/libGL errors in backend:**
   - The backend Dockerfile includes necessary OpenGL libraries
   - If issues persist, try using `opencv-python-headless` in requirements.txt

5. **Frontend not connecting to backend:**
   - Ensure `REACT_APP_API_URL` points to the correct backend URL
   - For Docker Compose, services can communicate using service names

### Fresh Start
If you encounter persistent issues:

```bash
# Stop all services
docker-compose down

# Remove containers
docker-compose rm -f

# Remove images
docker rmi pid-project_backend pid-project_frontend

# Clean system
docker system prune -f

# Rebuild everything
docker-compose up --build
```

## API Documentation

Once the backend is running, you can access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker Compose
5. Submit a pull request

## Support

If you encounter any issues:
1. Check the logs using `docker-compose logs [service-name]`
2. Ensure all prerequisites are installed
3. Try the "Fresh Start" troubleshooting steps
4. Check if ports 3000 and 8000 are available