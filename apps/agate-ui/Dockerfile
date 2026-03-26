FROM node:18-alpine

WORKDIR /app

# Copy package files (node_modules not copied from host — see .dockerignore)
COPY package.json package-lock.json* ./

# Install dependencies
RUN echo "[agate-ui build] Installing UI dependencies (this can take a minute on first run)..." \
    && if [ -f package-lock.json ]; then npm ci; else npm install; fi

# App source (overwrites nothing under node_modules — excluded by .dockerignore)
COPY . .

# Expose port
EXPOSE 5173

# Start dev server (docker-compose overrides this with npm install + sync-nodes + dev)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

