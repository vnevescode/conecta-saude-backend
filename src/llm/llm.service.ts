import { Injectable } from '@nestjs/common';
import { GoogleGenerativeAI } from '@google/generative-ai';

@Injectable()
export class LlmService {
  private genAI: GoogleGenerativeAI;

  constructor() {
    if (!process.env.LLM_API_KEY) {
      throw new Error('LLM_API_KEY is not defined in .env file');
    }
    this.genAI = new GoogleGenerativeAI(process.env.LLM_API_KEY);
  }

  async generateRecommendation(patientData: any): Promise<string> {
    const model = this.genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });
    const prompt = `
      Você é um assistente de saúde pública para a secretaria de saúde do Recife.
      Sua função é gerar um plano de ação claro e objetivo com base nos dados de um paciente 
      classificado como um caso atípico (outlier) para diabetes ou hipertensão.

      **Dados do Paciente Atípico:**
      - Idade: ${patientData.idade}
      - Nível de Glicose: ${patientData.nivel_glicose} mg/dL
      - Pressão Arterial: ${patientData.pressao_sistolica} / ${patientData.pressao_diastolica} mmHg
      - Histórico Familiar Relevante: ${patientData.historico_familiar ? 'Sim' : 'Não'}

      **Instrução:**
      Gere uma recomendação de ação para a secretaria de saúde em formato de tópicos (bullet points).
      Seja direto, profissional e foque em ações práticas como contato, agendamento e verificação.
    `;
    const result = await model.generateContent(prompt);
    return result.response.text();
  }
}
