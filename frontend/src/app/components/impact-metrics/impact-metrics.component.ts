// components/impact-metrics/impact-metrics.component.ts
import {
  Component,
  OnInit,
  inject,
  computed,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { WasteDataService } from '../../services/waste-data.service';

interface MetricCard {
  label: string;
  value: string;
  unit: string;
  icon: string;
  colorClass: string;
  bgClass: string;
}

@Component({
  selector: 'app-impact-metrics',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './impact-metrics.component.html',
})
export class ImpactMetricsComponent implements OnInit {
  private readonly svc = inject(WasteDataService);

  // ── Derived Signals ─────────────────────────────────────────────────────────
  readonly property = this.svc.selectedProperty;

  readonly metrics = computed<MetricCard[]>(() => {
    const p = this.property();
    return [
      {
        label: 'Diverted from Landfill YTD',
        value: p ? p.total_waste_diverted_kg.toFixed(1) : '—',
        unit: 'kg',
        icon: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                 stroke-width="1.5" stroke="currentColor" class="w-7 h-7">
                 <path stroke-linecap="round" stroke-linejoin="round"
                   d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591
                      M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636
                      M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z" />
               </svg>`,
        colorClass: 'text-emerald-600',
        bgClass: 'bg-emerald-50 border-emerald-200',
      },
      {
        label: 'Green Credits Balance',
        value: p ? p.green_credits_balance.toFixed(1) : '—',
        unit: 'GC',
        icon: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                 stroke-width="1.5" stroke="currentColor" class="w-7 h-7">
                 <path stroke-linecap="round" stroke-linejoin="round"
                   d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0
                      3.14-2.337 3.14-7.527 0-9.864-1.172-.879-3.07-.879-4.242 0
                      L9 5.818M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
               </svg>`,
        colorClass: 'text-amber-600',
        bgClass: 'bg-amber-50 border-amber-200',
      },
      {
        label: 'Segregation Streak',
        value: p ? String(p.segregation_streak_days) : '—',
        unit: 'days',
        icon: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                 stroke-width="1.5" stroke="currentColor" class="w-7 h-7">
                 <path stroke-linecap="round" stroke-linejoin="round"
                   d="M15.362 5.214A8.252 8.252 0 0 1 12 21 8.25 8.25 0 0 1
                      6.038 7.047 8.287 8.287 0 0 0 9 9.618a8.983 8.983 0 0 1
                      3.361-6.867 8.21 8.21 0 0 0 3 2.463Z" />
                 <path stroke-linecap="round" stroke-linejoin="round"
                   d="M12 18a3.75 3.75 0 0 0 .495-7.468 5.99 5.99 0 0 0-1.925
                      3.547 5.975 5.975 0 0 1-2.133-1A3.75 3.75 0 0 0 12 18Z" />
               </svg>`,
        colorClass: 'text-sky-600',
        bgClass: 'bg-sky-50 border-sky-200',
      },
    ];
  });

  ngOnInit(): void {
    if (!this.svc.properties().length) {
      this.svc.loadProperties().subscribe();
    }
  }
}
