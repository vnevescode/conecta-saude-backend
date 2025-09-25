import { Injectable } from '@nestjs/common';
import axios from 'axios';

@Injectable()
export class ClassificationService {
  private readonly classificationApiUrl = process.env.CLASSIFICATION_SERVICE_URL;

  async classify(patientData: any): Promise<{ is_outlier: boolean }> {
    if (!this.classificationApiUrl) {
      throw new Error('CLASSIFICATION_SERVICE_URL is not defined in .env file');
    }
    try {
      const response = await axios.post(`${this.classificationApiUrl}/classify`, patientData);
      return response.data;
    } catch (error) {
      console.error('Erro ao chamar o serviço de classificação:', error.message);
      throw new Error('Serviço de classificação indisponível ou com erro.');
    }
  }
}
