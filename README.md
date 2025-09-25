Backend - Conecta+Saúde
Sobre o Projeto
Este repositório contém o serviço principal do backend do projeto Conecta+Saúde. Ele atua como o cérebro da aplicação, orquestrando o fluxo de análise de pacientes.

Desenvolvido em Node.js com o framework NestJS, este serviço é responsável por:

Receber requisições da interface do usuário (frontend).

Comunicar-se com o microsserviço de Machine Learning (model-LLM) para classificar pacientes como outliers.

Chamar a API do Google Gemini para gerar recomendações de saúde com base nos dados dos pacientes.

Expor o endpoint POST /patient/analyze para o consumo do frontend.

🛠️ Tecnologias Utilizadas
Node.js: Ambiente de execução JavaScript.

NestJS: Framework progressivo para aplicações Node.js eficientes e escaláveis.

TypeScript: Superset do JavaScript que adiciona tipagem estática.

Docker: Para containerização da aplicação.

🚀 Como Executar
Este serviço é projetado para ser executado em conjunto com o model-LLM através do Docker Compose na raiz do projeto. Para instruções detalhadas de como rodar o ambiente completo, consulte o arquivo BUILD.md.

🤝 Contribuição
Contribuições são muito bem-vindas! Por favor, leia nosso GUIA DE CONTRIBUIÇÃO para saber como participar.