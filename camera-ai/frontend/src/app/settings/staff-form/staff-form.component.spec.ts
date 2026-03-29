import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError } from 'rxjs';
import { StaffFormComponent } from './staff-form.component';
import { StaffService } from '../../services/staff.service';
import { HttpErrorResponse } from '@angular/common/http';

describe('StaffFormComponent', () => {
  let component: StaffFormComponent;
  let routerSpy: jest.SpyObj<Router>;
  let staffSpy: jest.SpyObj<StaffService>;
  let snackBarSpy: jest.SpyObj<MatSnackBar>;

  function createComponent(routeId: string | null) {
    const activatedRoute = {
      snapshot: { paramMap: { get: () => routeId } },
    };

    TestBed.configureTestingModule({
      imports: [StaffFormComponent],
    })
      .overrideComponent(StaffFormComponent, {
        set: {
          providers: [
            { provide: ActivatedRoute, useValue: activatedRoute },
            { provide: Router, useValue: routerSpy },
            { provide: StaffService, useValue: staffSpy },
            { provide: MatSnackBar, useValue: snackBarSpy },
          ],
        },
      })
      .compileComponents();

    const fixture = TestBed.createComponent(StaffFormComponent);
    component = fixture.componentInstance;
    component.ngOnInit();
  }

  beforeEach(() => {
    routerSpy = { navigate: jest.fn() } as any;
    staffSpy = {
      registerStaff: jest.fn(),
      getStaff: jest.fn(),
      uploadPhoto: jest.fn(),
      deletePhoto: jest.fn(),
      deleteStaff: jest.fn(),
      getPhotoUrl: jest.fn((p: string) => `/photos/${p}`),
    } as any;
    snackBarSpy = { open: jest.fn() } as any;
  });

  describe('add mode', () => {
    beforeEach(() => createComponent(null));

    it('should create in add mode', () => {
      expect(component).toBeTruthy();
      expect(component.isEditMode).toBe(false);
    });

    it('should have correct page title', () => {
      expect(component.pageTitle).toBe('Add New Staff');
    });

    it('should be invalid without name and file', () => {
      expect(component.isAddValid).toBe(false);
    });

    it('should be invalid with name but no file', () => {
      component.staffName = 'Alice';
      expect(component.isAddValid).toBe(false);
    });

    it('should be valid with name and file', () => {
      component.staffName = 'Alice';
      component.selectedFile = new File(['data'], 'photo.jpg');
      expect(component.isAddValid).toBe(true);
    });

    it('should navigate back to settings', () => {
      component.goBack();
      expect(routerSpy.navigate).toHaveBeenCalledWith(['/settings']);
    });

    it('should register then upload photo on submit', () => {
      staffSpy.registerStaff.mockReturnValue(
        of({ status: 'success' as const, message: '', data: { id: 'alice' } })
      );
      staffSpy.uploadPhoto.mockReturnValue(
        of({ status: 'success' as const, message: '', data: {} })
      );

      component.staffName = 'Alice';
      component.selectedFile = new File(['data'], 'photo.jpg');
      component.submitNew();

      expect(staffSpy.registerStaff).toHaveBeenCalledWith('Alice');
      expect(staffSpy.uploadPhoto).toHaveBeenCalledWith('alice', component.selectedFile);
      expect(routerSpy.navigate).toHaveBeenCalledWith(['/settings']);
    });

    it('should show error if registration fails', () => {
      const err = new HttpErrorResponse({
        error: { message: 'Failed.' },
        status: 500,
      });
      staffSpy.registerStaff.mockReturnValue(throwError(() => err));

      component.staffName = 'Alice';
      component.selectedFile = new File(['data'], 'photo.jpg');
      component.submitNew();

      expect(component.error).toBe('Failed.');
      expect(component.isSubmitting).toBe(false);
    });

    it('should not submit when invalid', () => {
      component.submitNew();
      expect(staffSpy.registerStaff).not.toHaveBeenCalled();
    });
  });

  describe('edit mode', () => {
    beforeEach(() => {
      staffSpy.getStaff.mockReturnValue(
        of({
          status: 'success' as const,
          message: '',
          data: {
            id: 'alice',
            name: 'Alice Johnson',
            photos: ['staff/alice/photo_001.jpg', 'staff/alice/photo_002.jpg'],
            registered_at: '',
          },
        })
      );
      createComponent('alice');
    });

    it('should create in edit mode', () => {
      expect(component.isEditMode).toBe(true);
      expect(component.staffId).toBe('alice');
    });

    it('should have correct page title', () => {
      expect(component.pageTitle).toBe('Edit Staff');
    });

    it('should load staff data on init', () => {
      expect(staffSpy.getStaff).toHaveBeenCalledWith('alice');
      expect(component.staffName).toBe('Alice Johnson');
      expect(component.photos.length).toBe(2);
    });

    it('should generate photo URLs', () => {
      const url = component.getPhotoUrl('staff/alice/photo_001.jpg');
      expect(url).toBe('/photos/staff/alice/photo_001.jpg');
    });

    it('should extract filename from path', () => {
      expect(component.getPhotoFilename('staff/alice/photo_001.jpg')).toBe('photo_001.jpg');
    });

    it('should delete photo and reload', () => {
      staffSpy.deletePhoto.mockReturnValue(
        of({ status: 'success' as const, message: 'Removed.' })
      );
      component.deletePhoto('staff/alice/photo_001.jpg');
      expect(staffSpy.deletePhoto).toHaveBeenCalledWith('alice', 'staff/alice/photo_001.jpg');
      expect(snackBarSpy.open).toHaveBeenCalled();
    });

    it('should delete staff with confirmation', () => {
      jest.spyOn(window, 'confirm').mockReturnValue(true);
      staffSpy.deleteStaff.mockReturnValue(
        of({ status: 'success' as const, message: 'Deleted.' })
      );
      component.deleteStaff();
      expect(staffSpy.deleteStaff).toHaveBeenCalledWith('alice');
      expect(routerSpy.navigate).toHaveBeenCalledWith(['/settings']);
    });

    it('should not delete staff if not confirmed', () => {
      jest.spyOn(window, 'confirm').mockReturnValue(false);
      component.deleteStaff();
      expect(staffSpy.deleteStaff).not.toHaveBeenCalled();
    });
  });
});
