Guia de Build - Backend Conecta+Saúde
Este documento descreve como construir e executar o serviço de backend localmente para fins de desenvolvimento e teste.

🐳 Método 1: Execução com Docker (Recomendado)
A forma mais simples de rodar o projeto é usar o arquivo docker-compose.yml que está na pasta raiz do projeto (Conecta-Saude-Projeto).

Navegue até a pasta raiz do projeto.

Certifique-se de que seu arquivo .env está configurado com as chaves de API necessárias.

Execute o Docker Compose:

docker-compose up --build

O serviço de backend estará acessível em http://localhost:3000.

👨‍💻 Método 2: Execução Manual (Desenvolvimento Local)
Use este método para rodar o serviço de forma isolada.

Pré-requisitos:

Node.js (v20.x ou superior)

NPM (gerenciador de pacotes)

Passos:

Navegue até a pasta do backend:

cd backend

Instale as dependências:

npm install

Configure o .env: Crie um arquivo .env na raiz da pasta backend e adicione as variáveis de ambiente, como LLM_API_KEY. Lembre-se que, para este método funcionar, o serviço de ML precisa estar rodando separadamente para que a CLASSIFICATION_SERVICE_URL seja válida.

Execute em modo de desenvolvimento:

npm run start:dev

O servidor iniciará e ficará observando alterações nos arquivos.