import { Injectable } from '@nestjs/common';
import { ClassificationService } from '../classification/classification.service';
import { LlmService } from '../llm/llm.service';

@Injectable()
export class PatientService {
  constructor(
    private readonly classificationService: ClassificationService,
    private readonly llmService: LlmService,
  ) {}

  async analyzePatient(patientData: any) {
    // 1. Chama o serviço de classificação
    const classificationResult = await this.classificationService.classify(patientData);

    let recommendation = null;

    // 2. Se for um outlier, chama o serviço do LLM para gerar uma recomendação
    if (classificationResult.is_outlier) {
      recommendation = await this.llmService.generateRecommendation(patientData);
    }

    // 3. Aqui você adicionaria a lógica para salvar no banco de dados

    // 4. Retorna o resultado completo da análise
    return {
      patientData,
      is_outlier: classificationResult.is_outlier,
      recommendation: recommendation || 'Nenhuma ação recomendada, paciente dentro dos parâmetros.',
    };
  }
}
