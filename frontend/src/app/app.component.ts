// src/app/app.component.ts
import { Component } from '@angular/core';
import { DashboardLayoutComponent } from './components/dashboard-layout/dashboard-layout.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [DashboardLayoutComponent],
  template: `<app-dashboard-layout />`,
})
export class AppComponent {}
