# =======================
# Stage 1: Build stage
# =======================
FROM node:22.11.0-slim AS builder

WORKDIR /app

COPY app/package.json app/pnpm-lock.yaml* ./

RUN npm install -g pnpm && pnpm install --frozen-lockfile --dangerously-allow-all-builds

COPY app/ .

RUN pnpm build

# =======================
# Stage 2: Production stage
# =======================
FROM nginx:alpine AS prod

# Copy build output from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx config (optional)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]


# =======================
# Stage 3: Development stage
# =======================
FROM node:22.11.0-slim AS dev

WORKDIR /app

COPY app/package.json app/pnpm-lock.yaml* ./

RUN npm install -g pnpm && pnpm install --frozen-lockfile --dangerously-allow-all-builds

COPY app/ .

EXPOSE 3000

CMD ["pnpm", "dev", "--host"]