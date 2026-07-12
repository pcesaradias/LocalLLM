FROM node:20-bookworm-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Install serve to serve the built app
RUN npm install -g serve

# Copy source code
COPY . .

# Build the app (Vite outputs to ./dist)
RUN npm run build

# Run as the unprivileged user that ships with the node image
USER node

# Expose port
EXPOSE 3000

# Serve the Vite build output
CMD ["serve", "-s", "dist", "-l", "3000"]
