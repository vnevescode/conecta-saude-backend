import { Module } from '@nestjs/common';
import { LlmService } from './llm.service';

@Module({
  providers: [LlmService],
  exports: [LlmService], // <-- ADICIONE ESTA LINHA AQUI TAMBÉM
})
export class LlmModule {}
