import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { StaffService } from './staff.service';

describe('StaffService', () => {
  let service: StaffService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [StaffService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(StaffService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should list staff', () => {
    service.listStaff().subscribe((res) => {
      expect(res.status).toBe('success');
    });
    const req = httpMock.expectOne((r) => r.url.endsWith('/api/staff'));
    expect(req.request.method).toBe('GET');
    req.flush({ status: 'success', data: [] });
  });

  it('should get staff by id', () => {
    service.getStaff('alice').subscribe((res) => {
      expect(res.data.name).toBe('Alice');
    });
    const req = httpMock.expectOne((r) => r.url.endsWith('/api/staff/alice'));
    expect(req.request.method).toBe('GET');
    req.flush({ status: 'success', data: { id: 'alice', name: 'Alice', photos: [] } });
  });

  it('should register staff', () => {
    service.registerStaff('Alice').subscribe((res) => {
      expect(res.status).toBe('success');
    });
    const req = httpMock.expectOne((r) => r.url.endsWith('/api/staff/register'));
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ name: 'Alice' });
    req.flush({ status: 'success', data: { id: 'alice', name: 'Alice' } });
  });

  it('should delete staff', () => {
    service.deleteStaff('alice').subscribe((res) => {
      expect(res.status).toBe('success');
    });
    const req = httpMock.expectOne((r) => r.url.endsWith('/api/staff/alice'));
    expect(req.request.method).toBe('DELETE');
    req.flush({ status: 'success', message: 'Removed.' });
  });

  it('should upload photo', () => {
    const file = new File(['data'], 'photo.jpg', { type: 'image/jpeg' });
    service.uploadPhoto('alice', file).subscribe((res) => {
      expect(res.status).toBe('success');
    });
    const req = httpMock.expectOne((r) => r.url.endsWith('/api/staff/alice/photos') && r.method === 'POST');
    expect(req.request.body instanceof FormData).toBe(true);
    req.flush({ status: 'success', data: { photo_path: 'staff/alice/photo_001.jpg' } });
  });

  it('should delete photo', () => {
    service.deletePhoto('alice', 'staff/alice/photo_001.jpg').subscribe((res) => {
      expect(res.status).toBe('success');
    });
    const req = httpMock.expectOne(
      (r) => r.url.endsWith('/api/staff/alice/photos') && r.method === 'DELETE'
    );
    expect(req.request.params.get('photo_path')).toBe('staff/alice/photo_001.jpg');
    req.flush({ status: 'success', message: 'Photo removed.' });
  });

  it('should generate correct photo URL', () => {
    const url = service.getPhotoUrl('staff/alice_johnson/photo_001.jpg');
    expect(url).toContain('/api/staff-photos/alice_johnson/photo_001.jpg');
  });
});
