import { Controller, Post, Body } from '@nestjs/common';
import { PatientService } from './patient.service';

@Controller('patient')
export class PatientController {
  constructor(private readonly patientService: PatientService) {}

  @Post('analyze')
  analyze(@Body() patientData: any) {
    return this.patientService.analyzePatient(patientData);
  }
}
