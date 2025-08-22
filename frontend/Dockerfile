# Frontend Dockerfile (optional if using compose service)
FROM node:20-alpine
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci || npm install
COPY frontend .
EXPOSE 3000
CMD ["npm", "start"]


