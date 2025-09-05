FROM node:21-alpine

WORKDIR /app

# Copy only dependency files first (for caching)
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy the rest of the source code
COPY . .

# Expose the port
EXPOSE 3000

# Use JSON array form for CMD
CMD ["npm", "run", "dev"]