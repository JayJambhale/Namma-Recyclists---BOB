// components/mint-credits/mint-credits.component.ts
import {
  Component,
  inject,
  signal,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WasteDataService } from '../../services/waste-data.service';
import { MintRequest, MintResponse, WasteType, NodeType } from '../../models/swm.models'; // MintResponse used by signal type

@Component({
  selector: 'app-mint-credits',
  standalone: true,
  imports: [CommonModule, FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './mint-credits.component.html',
})
export class MintCreditsComponent {
  // public so template can read selectedProperty()
  readonly svc = inject(WasteDataService);

  readonly wasteTypes: WasteType[] = ['Wet', 'Dry', 'Sanitary', 'Special Care'];
  readonly nodeTypes: NodeType[] = ['Auto-Tipper', 'DWCC', 'Recycler', 'Composting'];

  readonly formData = signal<Omit<MintRequest, 'property_id' | 'batch_id'>>({
    waste_type: 'Dry',
    weight_kg: 10,
    node_type: 'DWCC',
    location: 'DWCC Ward 174, HSR Layout',
    operator_id: 'DRV-BLR-0042',
    notes: '',
  });

  readonly submitState = signal<'idle' | 'loading' | 'success' | 'error'>('idle');
  readonly lastResult = signal<MintResponse | null>(null);
  readonly errorMsg = signal<string | null>(null);

  updateField<K extends keyof ReturnType<typeof this.formData>>(
    key: K,
    value: ReturnType<typeof this.formData>[K]
  ) {
    this.formData.update((f) => ({ ...f, [key]: value }));
  }

  submit() {
    const prop = this.svc.selectedProperty();
    if (!prop) return;

    this.submitState.set('loading');
    this.lastResult.set(null);
    this.errorMsg.set(null);

    const payload: MintRequest = {
      property_id: prop.property_id,
      batch_id: `BTC-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      ...this.formData(),
    };

    this.svc.mintCredits(payload).subscribe({
      next: (res) => {
        this.lastResult.set(res);
        this.submitState.set('success');
        // Refresh lineage
        this.svc.loadLineage(prop.property_id).subscribe();
      },
      error: (err: Error) => {
        this.errorMsg.set(err.message);
        this.submitState.set('error');
      },
    });
  }
}
