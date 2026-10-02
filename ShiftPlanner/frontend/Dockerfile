# Образ фронтенда: собираем статику Vite и раздаём её nginx'ом.
# Заодно nginx проксирует /api на бэкенд (см. nginx.conf).

FROM node:20-alpine AS build
WORKDIR /app

# Сначала только манифесты — слой с node_modules кешируется.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# URL бэкенда вшивается в статику на этапе сборки (особенность SPA).
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
