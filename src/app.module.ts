import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { PatientModule } from './patient/patient.module';

@Module({
  imports: [PatientModule], // <-- SÓ PRECISAMOS IMPORTAR O MÓDULO PRINCIPAL
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}