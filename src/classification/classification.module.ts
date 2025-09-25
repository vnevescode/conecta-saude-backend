import { Module } from '@nestjs/common';
import { ClassificationService } from './classification.service';

@Module({
  providers: [ClassificationService],
  exports: [ClassificationService], // <-- ESSA LINHA É CRUCIAL
})
export class ClassificationModule {}
