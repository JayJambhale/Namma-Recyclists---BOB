// services/waste-data.service.ts — BFF service using Angular HttpClient

import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import {
  LineageResponse,
  MintRequest,
  MintResponse,
  Property,
} from '../models/swm.models';

@Injectable({ providedIn: 'root' })
export class WasteDataService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  // ── Reactive Signals (global state) ────────────────────────────────────────
  readonly selectedProperty = signal<Property | null>(null);
  readonly lineageData = signal<LineageResponse | null>(null);
  readonly properties = signal<Property[]>([]);
  readonly isLoading = signal<boolean>(false);
  readonly errorMessage = signal<string | null>(null);

  // ── Property Listing ────────────────────────────────────────────────────────
  loadProperties(): Observable<Property[]> {
    this.isLoading.set(true);
    return this.http.get<Property[]>(`${this.baseUrl}/properties`).pipe(
      tap((props) => {
        this.properties.set(props);
        if (props.length > 0 && !this.selectedProperty()) {
          this.selectedProperty.set(props[0]);
        }
        this.isLoading.set(false);
      }),
      catchError(this.handleError.bind(this))
    );
  }

  // ── Lineage (Batch Timeline) ────────────────────────────────────────────────
  loadLineage(propertyId: string): Observable<LineageResponse> {
    this.isLoading.set(true);
    return this.http
      .get<LineageResponse>(`${this.baseUrl}/lineage/${propertyId}`)
      .pipe(
        tap((data) => {
          this.lineageData.set(data);
          this.selectedProperty.set(data.property);
          this.isLoading.set(false);
        }),
        catchError(this.handleError.bind(this))
      );
  }

  // ── Mint Green Credits ──────────────────────────────────────────────────────
  mintCredits(payload: MintRequest): Observable<MintResponse> {
    return this.http
      .post<MintResponse>(`${this.baseUrl}/ledger/mint`, payload)
      .pipe(
        tap((res) => {
          // Refresh property balance in signal store after minting
          const current = this.selectedProperty();
          if (current && current.property_id === payload.property_id) {
            this.selectedProperty.set({
              ...current,
              green_credits_balance: res.new_balance,
            });
          }
        }),
        catchError(this.handleError.bind(this))
      );
  }

  // ── Error Handling ──────────────────────────────────────────────────────────
  private handleError(err: HttpErrorResponse): Observable<never> {
    this.isLoading.set(false);
    const msg =
      err.error?.detail ?? err.message ?? 'An unknown error occurred.';
    this.errorMessage.set(msg);
    return throwError(() => new Error(msg));
  }
}
