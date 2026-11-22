// components/waste-lineage-timeline/waste-lineage-timeline.component.ts
import {
  Component,
  OnInit,
  inject,
  computed,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { WasteDataService } from '../../services/waste-data.service';
import { NodeEvent, NodeStatus, NodeType } from '../../models/swm.models';

interface TimelineStep {
  label: string;
  nodeType: NodeType | 'Origin';
  event: NodeEvent | null;
  isCompleted: boolean;
  isActive: boolean;
}

@Component({
  selector: 'app-waste-lineage-timeline',
  standalone: true,
  imports: [CommonModule, DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './waste-lineage-timeline.component.html',
})
export class WasteLineageTimelineComponent implements OnInit {
  private readonly svc = inject(WasteDataService);

  readonly lineage = this.svc.lineageData;
  readonly isLoading = this.svc.isLoading;

  // ── Map events onto canonical pipeline steps ───────────────────────────────
  readonly steps = computed<TimelineStep[]>(() => {
    const data = this.lineage();
    if (!data) return [];

    const events = data.batch.events;
    const findEvent = (nodeType: string) =>
      events.find((e) => e.node_type === nodeType) ?? null;

    const autoTipperEvents = events.filter(
      (e) => e.node_type === 'Auto-Tipper'
    );
    const pickupEvent = autoTipperEvents[0] ?? null;
    const inTransitEvent = autoTipperEvents[1] ?? null;

    const pipeline: Array<{ label: string; nodeType: NodeType | 'Origin'; key: string }> = [
      { label: 'Picked Up', nodeType: 'Auto-Tipper', key: 'pickup' },
      { label: 'In Transit', nodeType: 'Auto-Tipper', key: 'transit' },
      { label: 'Arrived at DWCC', nodeType: 'DWCC', key: 'dwcc' },
      { label: 'Recycled / Processed', nodeType: 'Recycler', key: 'recycler' },
    ];

    const eventMap: Record<string, NodeEvent | null> = {
      pickup: pickupEvent,
      transit: inTransitEvent,
      dwcc: findEvent('DWCC'),
      recycler: findEvent('Recycler') ?? findEvent('Composting'),
    };

    const completedCount = Object.values(eventMap).filter(Boolean).length;

    return pipeline.map((step, idx) => ({
      label: step.label,
      nodeType: step.nodeType,
      event: eventMap[step.key],
      isCompleted: !!eventMap[step.key],
      isActive: !eventMap[step.key] && idx === completedCount,
    }));
  });

  readonly wasteTypeColor = computed(() => {
    const type = this.lineage()?.batch.waste_type;
    const map: Record<string, string> = {
      Wet: 'text-emerald-600',
      Dry: 'text-sky-600',
      Sanitary: 'text-violet-600',
      'Special Care': 'text-rose-600',
    };
    return map[type ?? ''] ?? 'text-slate-600';
  });

  statusBadge(status: NodeStatus): string {
    const map: Record<NodeStatus, string> = {
      Verified: 'bg-emerald-100 text-emerald-700',
      Processed: 'bg-sky-100 text-sky-700',
      'In Transit': 'bg-amber-100 text-amber-700',
      Contaminated: 'bg-red-100 text-red-700',
    };
    return map[status] ?? 'bg-slate-100 text-slate-600';
  }

  ngOnInit(): void {
    const prop = this.svc.selectedProperty();
    if (prop && !this.lineage()) {
      this.svc.loadLineage(prop.property_id).subscribe();
    }
  }
}
