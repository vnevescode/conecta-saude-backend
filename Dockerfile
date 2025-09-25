# Estágio 1: Build da Aplicação
FROM node:20-alpine AS development

WORKDIR /usr/src/app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Estágio 2: Imagem Final de Produção
FROM node:20-alpine AS production

ARG NODE_ENV=production
ENV NODE_ENV=${NODE_ENV}

WORKDIR /usr/src/app

COPY package*.json ./
RUN npm install --only=production

# Copia apenas os arquivos da build do estágio anterior
COPY --from=development /usr/src/app/dist ./dist

CMD ["node", "dist/main"]