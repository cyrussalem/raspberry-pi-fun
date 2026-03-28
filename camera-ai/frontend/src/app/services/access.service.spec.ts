import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { AccessService } from './access.service';

describe('AccessService', () => {
  let service: AccessService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [AccessService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AccessService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('verifyCode', () => {
    it('should POST to /api/access/verify with the code', () => {
      service.verifyCode('1234').subscribe((response) => {
        expect(response.status).toBe('success');
        expect(response.message).toContain('Access granted');
      });

      const req = httpMock.expectOne(
        (r) => r.url.endsWith('/api/access/verify') && r.method === 'POST'
      );
      expect(req.request.body).toEqual({ code: '1234' });
      req.flush({
        status: 'success',
        message: 'Access granted. Door unlocked for 5 seconds.',
      });
    });

    it('should handle error response for invalid code', () => {
      service.verifyCode('9999').subscribe({
        error: (err) => {
          expect(err.status).toBe(403);
        },
      });

      const req = httpMock.expectOne(
        (r) => r.url.endsWith('/api/access/verify') && r.method === 'POST'
      );
      req.flush(
        { status: 'error', message: 'Access denied. Invalid access code.' },
        { status: 403, statusText: 'Forbidden' }
      );
    });
  });

  describe('updateCode', () => {
    it('should POST to /api/access/update with current and new code', () => {
      service.updateCode('0000', '1234').subscribe((response) => {
        expect(response.status).toBe('success');
        expect(response.message).toContain('updated');
      });

      const req = httpMock.expectOne(
        (r) => r.url.endsWith('/api/access/update') && r.method === 'POST'
      );
      expect(req.request.body).toEqual({
        current_code: '0000',
        new_code: '1234',
      });
      req.flush({
        status: 'success',
        message: 'Access code updated successfully.',
      });
    });

    it('should handle error for wrong current code', () => {
      service.updateCode('wrong', '1234').subscribe({
        error: (err) => {
          expect(err.status).toBe(403);
        },
      });

      const req = httpMock.expectOne(
        (r) => r.url.endsWith('/api/access/update') && r.method === 'POST'
      );
      req.flush(
        { status: 'error', message: 'Current access code is incorrect.' },
        { status: 403, statusText: 'Forbidden' }
      );
    });
  });
});
