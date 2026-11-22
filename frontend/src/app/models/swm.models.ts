// models/swm.models.ts — TypeScript interfaces mirroring the backend Pydantic schemas

export type WasteType = 'Wet' | 'Dry' | 'Sanitary' | 'Special Care';
export type NodeType = 'Auto-Tipper' | 'DWCC' | 'Recycler' | 'Composting';
export type NodeStatus = 'Verified' | 'Contaminated' | 'Processed' | 'In Transit';
export type PropertyType = 'Household' | 'Commercial';

export interface NodeEvent {
  event_id: string;
  timestamp: string;        // ISO 8601
  node_type: NodeType;
  location: string;
  weight_kg: number;
  status: NodeStatus;
  operator_id?: string;
  notes?: string;
}

export interface Batch {
  batch_id: string;
  property_id: string;
  waste_type: WasteType;
  initial_weight_kg: number;
  collected_on: string;
  events: NodeEvent[];
  is_audit_passed: boolean;
  credits_minted: number;
}

export interface Property {
  property_id: string;
  ward_number: number;
  ward_name: string;
  address: string;
  type: PropertyType;
  green_credits_balance: number;
  segregation_streak_days: number;
  total_waste_diverted_kg: number;
  registered_on: string;
}

export interface LineageResponse {
  property: Property;
  batch: Batch;
}

export interface MintRequest {
  property_id: string;
  batch_id: string;
  waste_type: WasteType;
  weight_kg: number;
  node_type: NodeType;
  location: string;
  operator_id?: string;
  notes?: string;
}

export interface MintResponse {
  batch_id: string;
  audit_passed: boolean;
  credits_minted: number;
  new_balance: number;
  audit_reasoning: string;
}
