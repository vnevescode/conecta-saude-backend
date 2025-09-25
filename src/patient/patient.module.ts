// backend/src/patient/patient.module.ts
import { Module } from '@nestjs/common';
import { PatientService } from './patient.service';
import { PatientController } from './patient.controller'; // <-- DEIXE APENAS UMA LINHA DESSA
import { ClassificationModule } from '../classification/classification.module';
import { LlmModule } from '../llm/llm.module';

@Module({
  imports: [ClassificationModule, LlmModule],
  controllers: [PatientController],
  providers: [PatientService],
})
export class PatientModule {}