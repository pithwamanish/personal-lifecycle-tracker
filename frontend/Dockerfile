# Multi-stage Dockerfile for Frontend

# Stage 1: Development with Vite hot reloading
FROM node:22-slim AS dev
WORKDIR /app

ENV NODE_ENV=development

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]

# Stage 2: Production builder
FROM dev AS builder
ENV NODE_ENV=production
RUN npm run build

# Stage 3: Production static server with Caddy reverse proxy
FROM caddy:2-alpine AS prod
WORKDIR /srv
COPY --from=builder /app/dist /srv
COPY Caddyfile /etc/caddy/Caddyfile
EXPOSE 80
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
