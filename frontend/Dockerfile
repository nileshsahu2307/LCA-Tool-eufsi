# Frontend Dockerfile for EUFSI LCA Tool - Production Optimized
# Multi-stage build for smaller image size

# Stage 1: Build the React app
FROM node:20-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --only=production --ignore-scripts || npm install --force

# Copy source code
COPY . .

# Accept build argument for API URL with default value
ARG REACT_APP_BACKEND_URL=https://lca-eufsi-api.onrender.com
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# Build the production app
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy built files from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 3000 (not 80, to match Render expectations)
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
