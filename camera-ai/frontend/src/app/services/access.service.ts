import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface AccessResponse {
  status: 'success' | 'error';
  message: string;
}

@Injectable({ providedIn: 'root' })
export class AccessService {
  private baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  verifyCode(code: string): Observable<AccessResponse> {
    return this.http.post<AccessResponse>(`${this.baseUrl}/api/access/verify`, {
      code,
    });
  }

  updateCode(
    currentCode: string,
    newCode: string
  ): Observable<AccessResponse> {
    return this.http.post<AccessResponse>(
      `${this.baseUrl}/api/access/update`,
      {
        current_code: currentCode,
        new_code: newCode,
      }
    );
  }
}
