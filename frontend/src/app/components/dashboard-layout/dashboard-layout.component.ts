// components/dashboard-layout/dashboard-layout.component.ts
import {
  Component,
  OnInit,
  inject,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { WasteDataService } from '../../services/waste-data.service';
import { ImpactMetricsComponent } from '../impact-metrics/impact-metrics.component';
import { WasteLineageTimelineComponent } from '../waste-lineage-timeline/waste-lineage-timeline.component';
import { MintCreditsComponent } from '../mint-credits/mint-credits.component';

@Component({
  selector: 'app-dashboard-layout',
  standalone: true,
  imports: [
    CommonModule,
    ImpactMetricsComponent,
    WasteLineageTimelineComponent,
    MintCreditsComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './dashboard-layout.component.html',
})
export class DashboardLayoutComponent implements OnInit {
  readonly svc = inject(WasteDataService);

  ngOnInit(): void {
    this.svc.loadProperties().subscribe({
      next: (props) => {
        if (props.length > 0) {
          this.svc.loadLineage(props[0].property_id).subscribe();
        }
      },
    });
  }

  onPropertyChange(event: Event): void {
    const id = (event.target as HTMLSelectElement).value;
    this.svc.loadLineage(id).subscribe();
  }
}
