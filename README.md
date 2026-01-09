# EUFSI Life Cycle Assessment Tool

A comprehensive, multi-industry Life Cycle Assessment (LCA) tool powered by Brightway2 engine, supporting Textile, Footwear, Construction, and Battery industries.

## Features

- **Real LCA Databases**: Powered by USLCI, Agribalyse, and FORWAST databases
- **16+ Impact Categories**: Full ReCiPe and EF 3.1 methodology support
- **PDF Reports**: Generate detailed assessment reports
- **Verified Calculations**: Scientifically validated LCA methodology
- **Multi-Industry Support**: Textile, Footwear, Construction, and Battery industries

## Quick Start with Docker (Recommended)

The easiest way to run the LCA tool is using Docker. This requires **only Docker Desktop** - no need to install Python, Node.js, or MongoDB separately!

### Prerequisites
- **Docker Desktop** - Download from [docker.com](https://www.docker.com/products/docker-desktop/)

### Running with Docker

```bash
# 1. Clone the repository
git clone https://github.com/naveenkumar29nl/LCA-Tool-eufsi
cd LCA-Tool-eufsi

# 2. Start all services with one command
docker-compose up

# That's it! The application will be available at:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000/api
# - API Docs: http://localhost:8000/docs
```

To stop the application:
```bash
# Press Ctrl+C in the terminal, then run:
docker-compose down
```

To restart after stopping:
```bash
docker-compose up
```

To rebuild after code changes:
```bash
docker-compose up --build
```

---

## Alternative: Manual Installation

If you prefer to run without Docker, follow these instructions:

### Prerequisites

Before running the application manually, ensure you have the following installed:

- **Python 3.9+** (for backend)
- **Node.js 16+** and npm/yarn (for frontend)
- **MongoDB** (local installation or MongoDB Atlas)

### Installing MongoDB (Local)

#### Windows
1. Download MongoDB Community Server from [MongoDB Download Center](https://www.mongodb.com/try/download/community)
2. Run the installer and follow the installation wizard
3. MongoDB will run as a Windows service by default

#### macOS
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/naveenkumar29nl/LCA-Tool-eufsi
cd LCA-Tool-eufsi
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# The .env file is already configured for local development
# If needed, you can modify backend/.env to change MongoDB URL or other settings
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory (from root)
cd frontend

# Install dependencies
npm install
# or if you prefer yarn:
yarn install

# The .env file is already configured to connect to localhost:8000
# No additional configuration needed for local development
```

## Running the Application

You need to run both the backend and frontend servers.

### 1. Start the Backend Server

```bash
# From the backend directory
cd backend

# Activate virtual environment if not already activated
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Start the server
python start.py
```

The backend server will start on `http://localhost:8000`
- API endpoints: `http://localhost:8000/api`
- API documentation: `http://localhost:8000/docs`

### 2. Start the Frontend Server

Open a **new terminal window** and run:

```bash
# From the frontend directory
cd frontend

# Start the development server
npm start
# or with yarn:
yarn start
```

The frontend will automatically open in your browser at `http://localhost:3000`

## First Time Usage

1. **Create an account**: Click on "Sign Up" and create a new account
2. **Login**: Use your credentials to log in
3. **Select Industry**: Choose from Textile, Footwear, Construction, or Battery
4. **Start Assessment**: Fill in the required parameters for your product
5. **View Results**: Once calculation is complete, view detailed environmental impact analysis
6. **Generate Report**: Download PDF reports of your assessment

## Project Structure

```
LCA-Tool-eufsi/
├── backend/
│   ├── server.py           # Main FastAPI application
│   ├── start.py            # Server startup script
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Backend configuration
├── frontend/
│   ├── src/
│   │   ├── pages/         # React page components
│   │   ├── components/    # Reusable UI components
│   │   └── App.js         # Main React app
│   ├── public/            # Static files
│   ├── package.json       # Node dependencies
│   └── .env              # Frontend configuration
└── README.md             # This file
```

## Environment Variables

### Backend (.env)
```env
MONGO_URL=mongodb://localhost:27017    # MongoDB connection string
DB_NAME=lca_tool                       # Database name
JWT_SECRET_KEY=your-secret-key         # JWT secret for authentication
CORS_ORIGINS=http://localhost:3000     # Allowed CORS origins
PORT=8000                              # Backend server port
HOST=0.0.0.0                          # Backend server host
```

### Frontend (.env)
```env
REACT_APP_BACKEND_URL=http://localhost:8000  # Backend API URL
```

## Technologies Used

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **Brightway2**: LCA calculation engine
- **MongoDB**: Database for storing projects and user data
- **Motor**: Async MongoDB driver
- **ReportLab**: PDF generation
- **JWT**: Authentication

### Frontend
- **React 19**: UI library
- **React Router**: Navigation
- **Axios**: HTTP client
- **Tailwind CSS**: Styling
- **Radix UI**: Accessible UI components
- **Recharts**: Data visualization

## Troubleshooting

### Backend Issues

**MongoDB Connection Error**
- Ensure MongoDB is running: `mongod` or check Windows services
- Verify the MONGO_URL in backend/.env matches your MongoDB installation

**Brightway2 Initialization Error**
- The first run may take time as Brightway2 sets up databases
- Check logs for specific error messages

### Frontend Issues

**Cannot connect to backend**
- Ensure backend server is running on port 8000
- Check REACT_APP_BACKEND_URL in frontend/.env

**Port 3000 already in use**
- Kill the process using port 3000 or use a different port:
  ```bash
  PORT=3001 npm start
  ```

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## License

This project is part of the EUFSI initiative for environmental impact assessment.

## Support

For issues and questions, please open an issue on the GitHub repository.
