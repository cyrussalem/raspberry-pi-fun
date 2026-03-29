import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError } from 'rxjs';
import { SettingsComponent } from './settings.component';
import { AccessService } from '../services/access.service';
import { StaffService } from '../services/staff.service';
import { HttpErrorResponse } from '@angular/common/http';

describe('SettingsComponent', () => {
  let component: SettingsComponent;
  let routerSpy: jest.SpyObj<Router>;
  let accessSpy: jest.SpyObj<AccessService>;
  let staffSpy: jest.SpyObj<StaffService>;
  let snackBarSpy: jest.SpyObj<MatSnackBar>;

  beforeEach(async () => {
    routerSpy = { navigate: jest.fn() } as any;
    accessSpy = { verifyCode: jest.fn(), updateCode: jest.fn() } as any;
    staffSpy = { listStaff: jest.fn().mockReturnValue(of({ status: 'success', data: [] })) } as any;
    snackBarSpy = { open: jest.fn() } as any;

    await TestBed.configureTestingModule({
      imports: [SettingsComponent],
    })
      .overrideComponent(SettingsComponent, {
        set: {
          providers: [
            { provide: Router, useValue: routerSpy },
            { provide: AccessService, useValue: accessSpy },
            { provide: StaffService, useValue: staffSpy },
            { provide: MatSnackBar, useValue: snackBarSpy },
          ],
        },
      })
      .compileComponents();

    const fixture = TestBed.createComponent(SettingsComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load staff on init', () => {
    component.ngOnInit();
    expect(staffSpy.listStaff).toHaveBeenCalled();
  });

  it('should navigate back to dashboard', () => {
    component.goBack();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/']);
  });

  it('should navigate to add staff page', () => {
    component.addStaff();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/settings/staff/new']);
  });

  it('should navigate to edit staff page', () => {
    component.editStaff('alice_johnson');
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/settings/staff', 'alice_johnson']);
  });

  describe('access code', () => {
    it('should be invalid when codes are empty', () => {
      expect(component.isCodeValid).toBe(false);
    });

    it('should be valid with proper codes', () => {
      component.currentCode = '0000';
      component.newCode = '1234';
      expect(component.isCodeValid).toBe(true);
    });

    it('should be invalid with non-numeric new code', () => {
      component.currentCode = '0000';
      component.newCode = 'abcd';
      expect(component.isCodeValid).toBe(false);
    });

    it('should call updateCode on submit', () => {
      accessSpy.updateCode.mockReturnValue(of({ status: 'success' as const, message: 'Updated.' }));
      component.currentCode = '0000';
      component.newCode = '1234';
      component.updateCode();
      expect(accessSpy.updateCode).toHaveBeenCalledWith('0000', '1234');
    });

    it('should clear fields on success', () => {
      accessSpy.updateCode.mockReturnValue(of({ status: 'success' as const, message: 'Updated.' }));
      component.currentCode = '0000';
      component.newCode = '1234';
      component.updateCode();
      expect(component.currentCode).toBe('');
      expect(component.newCode).toBe('');
    });

    it('should show error on failure', () => {
      const err = new HttpErrorResponse({
        error: { message: 'Wrong code.' },
        status: 403,
      });
      accessSpy.updateCode.mockReturnValue(throwError(() => err));
      component.currentCode = '9999';
      component.newCode = '1234';
      component.updateCode();
      expect(component.codeError).toBe('Wrong code.');
    });
  });

  describe('staff list', () => {
    it('should populate staff list from API', () => {
      staffSpy.listStaff.mockReturnValue(
        of({
          status: 'success' as const,
          message: '',
          data: [{ id: 'alice', name: 'Alice', photos: ['p1.jpg'], registered_at: '' }],
        })
      );
      component.loadStaff();
      expect(component.staffList.length).toBe(1);
      expect(component.staffList[0].name).toBe('Alice');
    });
  });
});
