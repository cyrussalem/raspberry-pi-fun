import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface StaffRecord {
  id: string;
  name: string;
  photos: string[];
  registered_at: string;
}

export interface StaffResponse {
  status: 'success' | 'error';
  message: string;
  data?: any;
}

@Injectable({ providedIn: 'root' })
export class StaffService {
  private baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  listStaff(): Observable<StaffResponse> {
    return this.http.get<StaffResponse>(`${this.baseUrl}/api/staff`);
  }

  getStaff(staffId: string): Observable<StaffResponse> {
    return this.http.get<StaffResponse>(
      `${this.baseUrl}/api/staff/${staffId}`
    );
  }

  registerStaff(name: string): Observable<StaffResponse> {
    return this.http.post<StaffResponse>(
      `${this.baseUrl}/api/staff/register`,
      { name }
    );
  }

  deleteStaff(staffId: string): Observable<StaffResponse> {
    return this.http.delete<StaffResponse>(
      `${this.baseUrl}/api/staff/${staffId}`
    );
  }

  uploadPhoto(staffId: string, file: File): Observable<StaffResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<StaffResponse>(
      `${this.baseUrl}/api/staff/${staffId}/photos`,
      formData
    );
  }

  deletePhoto(
    staffId: string,
    photoPath: string
  ): Observable<StaffResponse> {
    return this.http.delete<StaffResponse>(
      `${this.baseUrl}/api/staff/${staffId}/photos`,
      { params: { photo_path: photoPath } }
    );
  }

  getPhotoUrl(photoPath: string): string {
    // photoPath is like "staff/alice_johnson/photo_001.jpg"
    // Strip the "staff/" prefix since the static mount is already at /api/staff-photos
    const relativePath = photoPath.replace(/^staff\//, '');
    return `${this.baseUrl}/api/staff-photos/${relativePath}`;
  }
}
