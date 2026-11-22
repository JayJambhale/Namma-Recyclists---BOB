FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --legacy-peer-deps

COPY . .
# No production build — serve dev server for local demo
EXPOSE 4200
CMD ["npm", "run", "start"]
